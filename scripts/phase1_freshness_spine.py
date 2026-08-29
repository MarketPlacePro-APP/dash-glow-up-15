#!/usr/bin/env python3
"""TLWB KPI freshness spine.

Writes only static build artifacts for the dashboard runtime and archive/control
rows for source checks. Phase 2A also writes normalized event/metric audit rows
from the high-risk generated adapters so cards cannot look current without a
source-backed manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


APP_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_MAIN = APP_ROOT.parent
LINK_WORKSPACE = Path("/Users/seanwilliams/.openclaw/workspace")
ARCHIVE_DB = Path(os.environ.get("TLWB_SOURCE_ARCHIVE_DB", str(LINK_WORKSPACE / "outputs" / "tlwb_source_archive.db")))
SCHEDULE_JSON = APP_ROOT / "data" / "schedule.json"
SOURCE_HEALTH_JSON = APP_ROOT / "data" / "source_health.json"
PHASE2A_AUDIT_JSON = APP_ROOT / "data" / "phase2a_audit.json"
GENERATE_DATA = APP_ROOT / "scripts" / "generate-live-data-review.py"
TZ = ZoneInfo("America/Denver")

ADAPTER_FILES = {
    "executiveAdapters": APP_ROOT / "src" / "data" / "executiveAdapters.ts",
    "tlwbPageAdapters": APP_ROOT / "src" / "data" / "tlwbPageAdapters.ts",
    "expoStrip": APP_ROOT / "src" / "data" / "expoStrip.ts",
    "masterTrackerMarketing": APP_ROOT / "src" / "data" / "masterTrackerMarketing.ts",
    "generatedData": APP_ROOT / "src" / "data" / "generatedData.ts",
}
GOOGLE_EXPORTS = WORKSPACE_MAIN / "data" / "google_exports"
REPLIT_EXPORTS = {
    "inside_sales": WORKSPACE_MAIN / "data" / "inside_replit_latest.json",
    "collections": WORKSPACE_MAIN / "data" / "collections_replit_latest.json",
}

SOURCE_LOCATIONS = {
    "expo": "Slack #expo — https://app.slack.com/client (TLWB workspace)",
    "teamwayne": "Slack #teamwayne — FE preview team channel",
    "teamdent": "Slack #teamdent — FE preview team channel",
    "teamwyman": "Slack #teamwyman — FE preview team channel",
    "teamvogel": "Slack #teamvogel — FE preview team channel",
    "teammillar": "Slack #teammillar — FE preview team channel",
    "teamtony": "Slack #teamtony — ME workshop team channel",
    "teamshaw": "Slack #teamshaw — ME workshop team channel; includes Megan",
    "teamnick": "Slack #teamnick — ME workshop team channel",
    "teamdrecksel": "Slack #teamdrecksel (Team Drexel) — ME workshop team channel",
    "eventstats": "Slack #eventstats — marketing spend/registration posts",
    "numbers_per_session": "Google Sheet: Numbers Per Session (1dfke_KCSGHNfnG_FUjAwo1TPAXFtgLEh9tE_XqQB0TU)",
    "upcoming_schedule": "Google Sheet: TLWB/MO Schedule (1F05mJPz4m8Kzxc8ROTQc4puRBky263ghSUMTg4kxKqY)",
    "workshop_team_schedule": "Google Sheet: Workshop Team Scheduling (1psHz1be5AdbpjLu4vWEIvecf6CLeuRWodBoHu20Dotw)",
    "master_tracker": "Google Sheet: TLWB Live Event Numbers (1miRUadPo0WsB9tAZ2XgJ3xgyV3CY0Z4xGUNd8eRY4EU)",
    "ws_sales_tracker": "Google Sheet: WS Sales Tracker (1CmJYo4jIiweNArfZvvKdb0q_WlLtLsNH1UqHaad5gxQ)",
    "inside_replit": "Replit API: utltlwb-stats.replit.app/api/tlwb/inside-sales-dpl",
    "collections_replit": "Replit API: utltlwb-stats.replit.app/api/tlwb/collections-performance",
}


def adapter_mtime(name: str) -> str | None:
    path = ADAPTER_FILES.get(name)
    if not path or not path.exists():
        return None
    return iso(datetime.fromtimestamp(path.stat().st_mtime, TZ))


def file_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return iso(datetime.fromtimestamp(path.stat().st_mtime, TZ))


def executive_adapter_text() -> str:
    path = ADAPTER_FILES["executiveAdapters"]
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rendered_expo_values(adapter_text: str) -> str | None:
    values = re.findall(r"\{\s*label:\s*'([^']+)'\s*,\s*value:\s*([0-9]+|null)", adapter_text)
    if not values:
        return None
    return ", ".join(f"{label} {value}" for label, value in values[:6])


def rendered_preview_values(adapter_text: str) -> str | None:
    block_match = re.search(r"export const activePreviewMarkets: ActivePreviewMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return None
    rows = []
    for row in re.finditer(
        r"market:\s*'([^']+)'.*?team:\s*'([^']+)'.*?registered:\s*([0-9]+).*?attendedCutoff:\s*([0-9]+).*?sales:\s*([0-9]+).*?sourceState:\s*'([^']+)'.*?sourcePostedAt:\s*'([^']+)'",
        block_match.group(1),
        re.S,
    ):
        market, team, reg, attendance, sales, state, posted_at = row.groups()
        if state == "active_session":
            rows.append(f"{market} ({team}): {reg} reg, {attendance} attendance, {sales} sales, source {posted_at}")
    return " | ".join(rows[:4]) if rows else None


def active_preview_source_channels(adapter_text: str) -> list[str]:
    """Return only Slack channels represented by currently LIVE Preview cards."""
    block_match = re.search(r"export const activePreviewMarkets: ActivePreviewMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return []
    channels: list[str] = []
    for row in re.finditer(
        r"team:\s*'([^']+)'.*?sourceState:\s*'([^']+)'",
        block_match.group(1),
        re.S,
    ):
        team, state = row.groups()
        if state != "active_session":
            continue
        match = re.search(r"/\s*#([a-z0-9-]+)", team, re.I)
        if match and match.group(1).lower() not in channels:
            channels.append(match.group(1).lower())
    return channels


def recent_final_preview_source_channels(adapter_text: str) -> list[str]:
    """Return channels represented by retained final Preview route cards."""
    block_match = re.search(r"export const activePreviewMarkets: ActivePreviewMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return []
    channels: list[str] = []
    for row in re.finditer(
        r"team:\s*'([^']+)'.*?sourceState:\s*'([^']+)'",
        block_match.group(1),
        re.S,
    ):
        team, state = row.groups()
        if state != "final_route_totals":
            continue
        match = re.search(r"/\s*#([a-z0-9-]+)", team, re.I)
        if match and match.group(1).lower() not in channels:
            channels.append(match.group(1).lower())
    return channels


def rendered_middle_end_values(adapter_text: str) -> str | None:
    block_match = re.search(r"export const middleEndSummary: MiddleEndSummary\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return None
    rows = []
    for row in re.finditer(
        r"market:\s*'([^']+)'.*?team:\s*'([^']+)'.*?sold:\s*([0-9]+).*?attended:\s*([0-9]+).*?showRate:\s*([^,]+),.*?workshopSales:\s*([0-9]+)",
        block_match.group(1),
        re.S,
    ):
        market, team, sold, attended, _show_rate, workshop_sales = row.groups()
        rows.append(f"{market} ({team}): preview sold {sold}, shown BU {attended}, ME sold {workshop_sales}")
    return " | ".join(rows[:6]) if rows else None


def rendered_upcoming_me_values(adapter_text: str) -> str | None:
    block_match = re.search(r"export const upcomingMePipeline: UpcomingMePipelineMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return None
    rows = []
    for row in re.finditer(
        r"market:\s*'([^']+)'.*?previewTeam:\s*'([^']+)'.*?middleEndTeam:\s*'([^']+)'.*?previewSold:\s*([0-9]+|null).*?projectedBuyingUnits:\s*([0-9]+|null).*?middleEndSold:\s*([0-9]+|null).*?sourcePostedAt:\s*'([^']+)'",
        block_match.group(1),
        re.S,
    ):
        market, preview_team, me_team, preview_sold, projected_bu, me_sold, posted_at = row.groups()
        rows.append(f"{market} ({preview_team} -> {me_team}): preview sold {preview_sold}, projected BU {projected_bu}, ME sold {me_sold}, source {posted_at}")
    return " | ".join(rows[:4]) if rows else None


def slug(value: str | None) -> str:
    raw = (value or "unknown").lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_") or "unknown"


def parse_number(value: str | None) -> float | None:
    if value is None or value == "null":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_active_preview_events(adapter_text: str) -> list[dict[str, Any]]:
    block_match = re.search(r"export const activePreviewMarkets: ActivePreviewMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return []
    events: list[dict[str, Any]] = []
    pattern = re.compile(
        r"\{\s*market:\s*'([^']+)'.*?team:\s*'([^']+)'.*?"
        r"sessionsCompleted:\s*([0-9]+|null).*?totalSessions:\s*([0-9]+|null).*?"
        r"registered:\s*([0-9]+).*?attendedCutoff:\s*([0-9]+).*?sales:\s*([0-9]+).*?"
        r"status:\s*'([^']+)'.*?sourceState:\s*'([^']+)'.*?"
        r"startDate:\s*'([^']+)'.*?latestSessionDate:\s*'([^']+)'.*?sourcePostedAt:\s*'([^']+)'",
        re.S,
    )
    for row in pattern.finditer(block_match.group(1)):
        market, team, sessions_completed, total_sessions, registered, attended, sales, status, source_state, start_date, latest_session_date, posted_at = row.groups()
        event_id = f"preview_{slug(market)}_{start_date}"
        events.append({
            "event_id": event_id,
            "market_name": market,
            "event_type": "preview",
            "segment": "TLWB",
            "team_name": team,
            "start_date": start_date,
            "end_date": latest_session_date,
            "source_id": f"slack_channel_{slug(team.split('#')[-1])}" if "#" in team else None,
            "source_record_ref": f"phase2a:activePreviewMarkets:{event_id}",
            "source_posted_at": posted_at,
            "status": status,
            "source_state": source_state,
            "metrics": {
                "registered": parse_number(registered),
                "attended_cutoff": parse_number(attended),
                "sales": parse_number(sales),
                "sessions_completed": parse_number(sessions_completed),
                "total_sessions": parse_number(total_sessions),
            },
        })
    return events


def parse_middle_end_events(adapter_text: str) -> list[dict[str, Any]]:
    block_match = re.search(r"export const middleEndSummary: MiddleEndSummary\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return []
    events: list[dict[str, Any]] = []
    pattern = re.compile(
        r"\{\s*label:\s*'([^']+)'.*?period:\s*'([^']+)'.*?market:\s*'([^']+)'.*?"
        r"team:\s*'([^']+)'.*?sold:\s*([0-9]+).*?attended:\s*([0-9]+).*?"
        r"startDate:\s*'([^']+)'.*?workshopSales:\s*([0-9]+)",
        re.S,
    )
    for row in pattern.finditer(block_match.group(1)):
        label, period, market, team, sold, attended, start_date, workshop_sales = row.groups()
        event_id = f"middle_end_{slug(market)}_{start_date}"
        events.append({
            "event_id": event_id,
            "market_name": market,
            "event_type": "middle_end",
            "segment": "TLWB",
            "team_name": team,
            "start_date": start_date,
            "end_date": start_date,
            "source_id": None,
            "source_record_ref": f"phase2a:middleEndSummary:{event_id}",
            "status": "final",
            "source_state": period,
            "label": label,
            "metrics": {
                "preview_sold": parse_number(sold),
                "buying_units_attended": parse_number(attended),
                "workshop_sales": parse_number(workshop_sales),
            },
        })
    return events


def parse_upcoming_me_events(adapter_text: str) -> list[dict[str, Any]]:
    block_match = re.search(r"export const upcomingMePipeline: UpcomingMePipelineMarket\[] = \[(.*?)\n\];", adapter_text, re.S)
    if not block_match:
        return []
    events: list[dict[str, Any]] = []
    pattern = re.compile(
        r"\{\s*market:\s*'([^']+)'.*?previewTeam:\s*'([^']+)'.*?middleEndTeam:\s*'([^']+)'.*?"
        r"startDate:\s*'([^']+)'.*?endDate:\s*'([^']+)'.*?previewSold:\s*([0-9]+|null).*?"
        r"projectedBuyingUnits:\s*([0-9]+|null).*?middleEndSold:\s*([0-9]+|null).*?sourcePostedAt:\s*'([^']+)'",
        re.S,
    )
    for row in pattern.finditer(block_match.group(1)):
        market, preview_team, me_team, start_date, end_date, preview_sold, projected_bu, me_sold, posted_at = row.groups()
        event_id = f"upcoming_middle_end_{slug(market)}_{start_date}"
        events.append({
            "event_id": event_id,
            "market_name": market,
            "event_type": "middle_end",
            "segment": "TLWB",
            "team_name": me_team,
            "preview_team": preview_team,
            "start_date": start_date,
            "end_date": end_date,
            "source_id": None,
            "source_record_ref": f"phase2a:upcomingMePipeline:{event_id}",
            "source_posted_at": posted_at,
            "status": "upcoming",
            "source_state": "pipeline",
            "metrics": {
                "preview_sold": parse_number(preview_sold),
                "projected_buying_units": parse_number(projected_bu),
                "middle_end_sold": parse_number(me_sold),
            },
        })
    return events


def git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(WORKSPACE_MAIN),
            capture_output=True, text=True, timeout=5, check=False,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def source_location_for(channels: list[str]) -> str:
    parts = [SOURCE_LOCATIONS.get(c, f"Slack #{c}") for c in channels]
    return " · ".join(parts)

REQUIRED_CHANNELS = [
    "teamdrecksel",
    "teamtony",
    "teamnick",
    "teamshaw",
    "teamwayne",
    "teamdent",
    "teamwyman",
    "teamvogel",
    "teammillar",
    "eventstats",
    "expo",
]
OPTIONAL_CHANNELS = [
    "front-end-team",
    "ticketsales",
    "collections-allteams",
    "refunds-allteams",
    "fe-confirmations-team",
]
CHANNEL_ALIASES = {"teamvogal": "teamvogel"}


def now_dt() -> datetime:
    return datetime.now(TZ).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def source_id(channel: str) -> str:
    return f"slack_channel_{channel.replace('-', '_')}"


def load_slack():
    sys.path.insert(0, str(LINK_WORKSPACE))
    import sean_analytics as slack  # type: ignore

    token = slack.load_token()
    channel_map = slack.resolve_channel_map(token)
    return slack, token, channel_map


def ensure_schedule_artifact() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(GENERATE_DATA)],
        cwd=str(APP_ROOT),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "schedule generator failed").strip())
    if not SCHEDULE_JSON.exists():
        raise RuntimeError(f"schedule artifact missing: {SCHEDULE_JSON}")
    data = json.loads(SCHEDULE_JSON.read_text())
    if data.get("source", {}).get("source_id") != "upcoming_schedule":
        raise RuntimeError("schedule artifact does not name upcoming_schedule as source")
    if not data.get("records") or not data.get("route_blocks"):
        raise RuntimeError("schedule artifact is empty")
    return data


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(ARCHIVE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def upsert_slack_source(conn: sqlite3.Connection, channel: str, channel_id: str | None, required: bool) -> None:
    conn.execute(
        """
        insert into source_registry (
          source_id, source_name, source_type, source_family, trust_role,
          business_area, canonical_ref, external_id, enabled, access_status,
          owner_hint, notes, updated_at
        ) values (?, ?, 'slack_channel', 'slack_final', 'final_truth', 'TLWB', ?, ?, 1, ?, 'Link/sean_analytics', ?, CURRENT_TIMESTAMP)
        on conflict(source_id) do update set
          source_name=excluded.source_name,
          canonical_ref=excluded.canonical_ref,
          external_id=excluded.external_id,
          access_status=excluded.access_status,
          notes=excluded.notes,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            source_id(channel),
            f"Slack #{channel}",
            f"Slack channel #{channel}",
            channel_id,
            "ok" if channel_id else "missing_permission",
            "Required Phase 1 channel" if required else "Optional Phase 1 channel; not_in_channel does not block deploy",
        ),
    )


def insert_check_run(
    conn: sqlite3.Connection,
    channel: str,
    checked_at: str,
    status: str,
    rows_seen: int,
    records_seen: int,
    latest_source_record_at: str | None,
    error_class: str | None = None,
    error_message: str | None = None,
    notes: str | None = None,
) -> None:
    conn.execute(
        """
        insert into source_check_runs (
          source_id, checked_at, status, api_status, rows_seen, records_seen,
          latest_source_record_at, error_class, error_message, notes
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id(channel),
            checked_at,
            status,
            status,
            rows_seen,
            records_seen,
            latest_source_record_at,
            error_class,
            error_message,
            notes,
        ),
    )


def fetch_and_archive_slack(limit: int, simulate_failure: bool = False) -> dict[str, dict[str, Any]]:
    checked_at = iso(now_dt())
    outcomes: dict[str, dict[str, Any]] = {}
    slack = token = channel_map = None
    if not simulate_failure:
        slack, token, channel_map = load_slack()

    with connect_db() as conn:
        for alias, target in CHANNEL_ALIASES.items():
            outcomes[alias] = {
                "channel": alias,
                "alias_for": target,
                "required": False,
                "status": "alias",
                "rows_seen": 0,
                "new_rows_since_last_check": 0,
                "latest_source_post_date": None,
                "notes": f"Alias map #{alias} -> #{target}.",
            }

        for channel in [*REQUIRED_CHANNELS, *OPTIONAL_CHANNELS]:
            required = channel in REQUIRED_CHANNELS
            channel_id = None if simulate_failure else channel_map.get(channel)  # type: ignore[union-attr]
            upsert_slack_source(conn, channel, channel_id, required)
            if simulate_failure:
                status = "failed"
                insert_check_run(
                    conn,
                    channel,
                    checked_at,
                    status,
                    0,
                    0,
                    None,
                    "SimulatedSlackFetchFailure",
                    "Simulated Slack fetch failure for resilience gate.",
                    "Failure did not delete last-good static artifacts.",
                )
                outcomes[channel] = {
                    "channel": channel,
                    "required": required,
                    "status": status,
                    "rows_seen": 0,
                    "new_rows_since_last_check": 0,
                    "latest_source_post_date": None,
                    "notes": "Simulated Slack fetch failure.",
                }
                continue
            if not channel_id:
                status = "failed" if required else "not_in_channel"
                insert_check_run(
                    conn,
                    channel,
                    checked_at,
                    status,
                    0,
                    0,
                    None,
                    "channel_not_visible",
                    f"Channel #{channel} not visible to token.",
                    "Required channel blocks; optional channel is coverage-only.",
                )
                outcomes[channel] = {
                    "channel": channel,
                    "required": required,
                    "status": status,
                    "rows_seen": 0,
                    "new_rows_since_last_check": 0,
                    "latest_source_post_date": None,
                    "notes": f"Channel #{channel} not visible.",
                }
                continue

            try:
                messages = slack.fetch_history(token, channel_id, limit=limit)  # type: ignore[union-attr]
            except BaseException as exc:  # noqa: BLE001 - helper raises SystemExit for Slack API errors.
                if isinstance(exc, KeyboardInterrupt):
                    raise
                message = str(exc)
                status = "not_in_channel" if (not required and "not_in_channel" in message) else "failed"
                insert_check_run(
                    conn,
                    channel,
                    checked_at,
                    status,
                    0,
                    0,
                    None,
                    type(exc).__name__,
                    message[:500],
                    "Required channel blocks; optional channel is coverage-only.",
                )
                outcomes[channel] = {
                    "channel": channel,
                    "required": required,
                    "status": status,
                    "rows_seen": 0,
                    "new_rows_since_last_check": 0,
                    "latest_source_post_date": None,
                    "notes": message[:500],
                }
                continue

            new_rows = 0
            latest_post: str | None = None
            for msg in messages:
                ts = str(msg.get("ts", ""))
                if not ts:
                    continue
                posted_at = iso(datetime.fromtimestamp(float(ts), TZ))
                latest_post = max(latest_post or posted_at, posted_at)
                cursor = conn.execute(
                    "select 1 from slack_messages_raw where workspace_id=? and channel_id=? and message_ts=?",
                    ("tlwb_slack", channel_id, ts),
                )
                existed = cursor.fetchone() is not None
                conn.execute(
                    """
                    insert or ignore into slack_messages_raw (
                      workspace_id, channel_id, channel_name, message_ts, thread_ts,
                      user_id, username_snapshot, text, raw_json, permalink,
                      is_thread_reply, fetched_at, source_id
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "tlwb_slack",
                        channel_id,
                        channel,
                        ts,
                        msg.get("thread_ts"),
                        msg.get("user"),
                        msg.get("username"),
                        msg.get("text") or "",
                        json.dumps(msg, ensure_ascii=True),
                        msg.get("permalink"),
                        1 if msg.get("thread_ts") and msg.get("thread_ts") != ts else 0,
                        checked_at,
                        source_id(channel),
                    ),
                )
                if not existed:
                    new_rows += 1
            if latest_post:
                latest_dt = datetime.fromisoformat(latest_post)
                status = "ok_fresh" if (now_dt() - latest_dt).total_seconds() / 3600 <= 24 else "ok_no_new_expected"
            else:
                status = "ok_no_new_expected"
            insert_check_run(
                conn,
                channel,
                checked_at,
                status,
                len(messages),
                new_rows,
                latest_post,
                notes="Slack history checked; zero new rows is recorded explicitly.",
            )
            outcomes[channel] = {
                "channel": channel,
                "required": required,
                "status": status,
                "rows_seen": len(messages),
                "new_rows_since_last_check": new_rows,
                "latest_source_post_date": latest_post,
                "notes": "Slack history fetch ok.",
            }
    return outcomes


def latest_for(outcomes: dict[str, dict[str, Any]], channels: list[str]) -> str | None:
    dates = [outcomes.get(c, {}).get("latest_source_post_date") for c in channels]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def rows_for(outcomes: dict[str, dict[str, Any]], channels: list[str]) -> int:
    return sum(int(outcomes.get(c, {}).get("rows_seen") or 0) for c in channels)


def new_rows_for(outcomes: dict[str, dict[str, Any]], channels: list[str]) -> int:
    return sum(int(outcomes.get(c, {}).get("new_rows_since_last_check") or 0) for c in channels)


def outcome_failed(outcomes: dict[str, dict[str, Any]], channels: list[str]) -> list[str]:
    return [c for c in channels if outcomes.get(c, {}).get("status") == "failed"]


def stale_or_ambiguous_channels(outcomes: dict[str, dict[str, Any]], channels: list[str], expected_hours: int) -> list[str]:
    stale: list[str] = []
    checked_now = now_dt()
    for channel in channels:
        outcome = outcomes.get(channel, {})
        latest_source_post_date = outcome.get("latest_source_post_date")
        if outcome.get("status") != "ok_fresh" or not latest_source_post_date:
            stale.append(channel)
            continue
        try:
            latest = datetime.fromisoformat(latest_source_post_date)
        except ValueError:
            stale.append(channel)
            continue
        age_hours = (checked_now - latest).total_seconds() / 3600
        if age_hours > expected_hours:
            stale.append(channel)
    return stale


def freshness_status(
    latest_source_post_date: str | None,
    expected_hours: int,
    schedule_state: str,
    failed_channels: list[str],
    stale_channels: list[str] | None = None,
) -> tuple[str, str]:
    if failed_channels:
        return "red", f"Check failed for required channel(s): {', '.join(failed_channels)}."
    if stale_channels:
        return "yellow", f"Checked, but not every mapped source has a fresh positive assertion: {', '.join(stale_channels)}."
    if not latest_source_post_date:
        return "yellow", "No positive latest source timestamp; ambiguity cannot render green."
    latest = datetime.fromisoformat(latest_source_post_date)
    age_hours = (now_dt() - latest).total_seconds() / 3600
    if schedule_state in {"completed", "historical"}:
        if age_hours <= expected_hours:
            return "green", f"Completed route; source checked and latest data is within {expected_hours}h cadence. Latest data: {latest_source_post_date[:10]}."
        return "yellow", f"Completed route; latest source data is {age_hours:.0f}h old ({latest_source_post_date[:10]}). No new data expected but source was verified."
    if age_hours <= expected_hours:
        return "green", f"Successful check and latest source is within {expected_hours}h expected cadence."
    return "yellow", f"Checked, but latest source is {age_hours:.1f}h old against {expected_hours}h cadence."


def health_row(
    page: str,
    section: str,
    sources: list[str],
    latest_source_post_date: str | None,
    rows_seen: int,
    new_rows: int,
    status: str,
    notes: str,
    last_checked: str,
    blocker: str | None = None,
    schedule_state: str = "current",
    expected_cadence: str = "24h",
    source_location: str = "",
    last_synced: str | None = None,
    latest_data_date: str | None = None,
    rendered_values: str | None = None,
) -> dict[str, Any]:
    return {
        "page": page,
        "section": section,
        "sources": sources,
        "source_location": source_location,
        "last_checked": last_checked,
        "last_synced": last_synced,
        "latest_source_post_date": latest_source_post_date,
        "latest_data_date": latest_data_date,
        "rendered_values": rendered_values,
        "rows_seen": rows_seen,
        "new_rows_since_last_check": new_rows,
        "status": status,
        "schedule_state": schedule_state,
        "expected_cadence": expected_cadence,
        "notes": notes,
        "blocker": blocker,
    }


def build_source_health(schedule: dict[str, Any], outcomes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    last_checked = iso(now_dt())
    rows: list[dict[str, Any]] = []

    exec_synced = adapter_mtime("executiveAdapters")
    page_synced = adapter_mtime("tlwbPageAdapters")
    expo_synced = adapter_mtime("expoStrip")
    gen_synced = adapter_mtime("generatedData")
    mkt_synced = adapter_mtime("masterTrackerMarketing")
    exec_text = executive_adapter_text()
    expo_rendered_values = rendered_expo_values(exec_text)
    preview_rendered_values = rendered_preview_values(exec_text)
    me_rendered_values = rendered_middle_end_values(exec_text)
    upcoming_me_rendered_values = rendered_upcoming_me_values(exec_text)

    def add_slack(
        page: str, section: str, channels: list[str],
        expected_hours: int = 24, schedule_state: str = "current",
        adapter: str | None = None, data_date: str | None = None,
        rendered_values: str | None = None,
        extra_sources: list[str] | None = None,
        source_location_override: str | None = None,
    ) -> None:
        failed = outcome_failed(outcomes, channels)
        stale = stale_or_ambiguous_channels(outcomes, channels, expected_hours)
        latest = latest_for(outcomes, channels)
        status, note = freshness_status(latest, expected_hours, schedule_state, failed, stale)
        synced = adapter_mtime(adapter) if adapter else exec_synced
        rows.append(health_row(
            page,
            section,
            [f"slack:#{c}" for c in channels] + (extra_sources or []),
            latest,
            rows_for(outcomes, channels),
            new_rows_for(outcomes, channels),
            status,
            note,
            last_checked,
            note if status in {"yellow", "red"} else None,
            schedule_state,
            f"{expected_hours}h",
            source_location=source_location_override or source_location_for(channels),
            last_synced=synced,
            latest_data_date=data_date or (latest[:10] if latest else None),
            rendered_values=rendered_values,
        ))

    preview_channels = ["teamwayne", "teamdent", "teamwyman", "teamvogel"]
    active_preview_channels = active_preview_source_channels(exec_text)
    if not active_preview_channels:
        active_preview_channels = ["teamwayne", "teamdent", "teamvogel", "teammillar"]
    recent_final_preview_channels = recent_final_preview_source_channels(exec_text)
    me_channels = ["teamtony", "teamshaw", "teamnick", "teamdrecksel"]

    add_slack("Executive", "Expo count", ["expo"], 24, adapter="expoStrip", rendered_values=expo_rendered_values)
    add_slack("Executive", "Active preview pace", active_preview_channels, 24, adapter="executiveAdapters", rendered_values=preview_rendered_values)
    add_slack("Executive", "Completed ME show-rate groups", me_channels, 24, adapter="executiveAdapters", rendered_values=me_rendered_values)
    add_slack(
        "Executive",
        "Current upcoming ME pipeline",
        active_preview_channels,
        24,
        adapter="executiveAdapters",
        rendered_values=upcoming_me_rendered_values,
        extra_sources=["google_sheet:workshop_team_schedule"],
        source_location_override=f"{source_location_for(active_preview_channels)} · {SOURCE_LOCATIONS['workshop_team_schedule']}",
    )
    add_slack("Executive", "Active marketing", ["eventstats"], 24, adapter="executiveAdapters")
    add_slack("Marketing", "Active markets", ["eventstats"], 24, adapter="executiveAdapters")
    add_slack("Marketing", "Historical market comparisons", ["eventstats"], 24, adapter="masterTrackerMarketing")
    add_slack("Preview", "Current Preview Markets", active_preview_channels, 24, adapter="executiveAdapters", rendered_values=preview_rendered_values)
    add_slack("Preview", "Session Breakdown", active_preview_channels, 24, adapter="executiveAdapters")
    if recent_final_preview_channels:
        add_slack("Preview", "Recent final routes", recent_final_preview_channels, 72, "completed", adapter="executiveAdapters")
    add_slack("Preview", "Team historical performance", preview_channels, 24, "completed", adapter="tlwbPageAdapters")
    add_slack("Preview", "Coverage requirement: Team Wyman", ["teamwyman"], 24, "coverage_requirement", adapter="executiveAdapters")
    add_slack("Workshop / ME", "Current or Just Completed", me_channels, 24, adapter="tlwbPageAdapters")
    add_slack("Workshop / ME", "Historical ME performance", me_channels, 24, "completed", adapter="tlwbPageAdapters")

    schedule_latest = schedule.get("generated_at")
    schedule_status, schedule_note = freshness_status(schedule_latest, 24, "current", [])
    sched_loc = SOURCE_LOCATIONS["upcoming_schedule"]
    rows.append(health_row(
        "Executive",
        "Upcoming route blocks",
        ["google_sheet:upcoming_schedule"],
        schedule_latest,
        len(schedule.get("route_blocks", [])),
        0,
        schedule_status,
        schedule_note,
        last_checked,
        None if schedule_status == "green" else schedule_note,
        "current",
        "24h",
        source_location=sched_loc,
        last_synced=gen_synced,
        latest_data_date=schedule_latest[:10] if schedule_latest else None,
    ))
    rows.append(health_row(
        "Schedule",
        "Calendar and route blocks",
        ["google_sheet:upcoming_schedule"],
        schedule_latest,
        len(schedule.get("records", [])),
        0,
        schedule_status,
        "Schedule artifact parsed from TLWB/MO Schedule; current/upcoming route blocks sort first.",
        last_checked,
        None if schedule_status == "green" else "Schedule artifact is stale or ambiguous.",
        "current",
        "24h",
        source_location=sched_loc,
        last_synced=gen_synced,
        latest_data_date=schedule_latest[:10] if schedule_latest else None,
    ))
    rows.append(health_row(
        "Data QA",
        "Operational source ledger",
        ["data:source_health.json", "data:schedule.json"],
        last_checked,
        len(rows),
        0,
        "green" if not any(row["status"] == "red" for row in rows) else "red",
        "Rendered from committed static artifacts, not runtime SQLite.",
        last_checked,
        "One or more source-health rows are red." if any(row["status"] == "red" for row in rows) else None,
        "current",
        "each build",
        source_location="Local build artifact: data/source_health.json + data/schedule.json",
        last_synced=last_checked,
    ))


    inside_file = REPLIT_EXPORTS["inside_sales"]
    collections_file = REPLIT_EXPORTS["collections"]
    inside_ok = inside_file.exists() and inside_file.stat().st_size > 100
    collections_ok = collections_file.exists() and collections_file.stat().st_size > 100
    inside_mtime = file_mtime(inside_file)
    collections_mtime = file_mtime(collections_file)
    latest_replit = max(filter(None, [inside_mtime, collections_mtime]), default=None)

    replit_status = "green" if inside_ok and collections_ok and latest_replit else "red"
    replit_note = "Replit API exports present."
    if inside_ok and collections_ok and latest_replit:
        replit_age = (now_dt() - datetime.fromisoformat(latest_replit)).total_seconds() / 3600
        if replit_age > 24:
            replit_status = "yellow"
            replit_note = f"Replit exports exist but are {replit_age:.0f}h old."
        else:
            replit_note = f"Replit exports refreshed {replit_age:.0f}h ago."
    elif not inside_ok:
        replit_note = "Inside Sales DPL export missing or empty."
    elif not collections_ok:
        replit_note = "Collections Performance export missing or empty."

    rows.append(health_row(
        "Inside Sales",
        "DPL and collections",
        ["api:inside_replit_latest", "api:collections_replit_latest"],
        latest_replit,
        1,
        0,
        replit_status,
        replit_note,
        last_checked,
        replit_note if replit_status != "green" else None,
        "current",
        "24h",
        source_location=f"{SOURCE_LOCATIONS['inside_replit']} · {SOURCE_LOCATIONS['collections_replit']}",
        last_synced=page_synced,
        latest_data_date=latest_replit[:10] if latest_replit else None,
    ))

    current_blocks = [b for b in schedule.get("route_blocks", []) if b.get("status") in {"active", "upcoming"}]
    for block in current_blocks[:12]:
        risk_flags = []
        if block.get("teamKey") == "megan":
            risk_flags.append("unresolved_entity_megan")
        if block.get("teamKey") == "ops":
            risk_flags.append("unassigned_team")
        if "power" in str(block.get("market", "")).lower():
            risk_flags.append("parser_exception_possible_note_row")
        route_status = "yellow" if risk_flags else schedule_status
        route_note = f"{block.get('status')} route from TLWB/MO Schedule; rows {block.get('sourceRows')}."
        if risk_flags:
            route_note += f" Risk/exception flags: {', '.join(risk_flags)}."
        rows.append(health_row(
            "Schedule",
            f"Route block: {block.get('market')} / {block.get('team')}",
            ["google_sheet:upcoming_schedule"],
            schedule_latest,
            len(block.get("sourceRows", [])),
            0,
            route_status,
            route_note,
            last_checked,
            f"Risk/exception flags: {', '.join(risk_flags)}." if risk_flags else None,
            block.get("status", "current"),
            "24h while current/upcoming",
            source_location=sched_loc,
            last_synced=gen_synced,
            latest_data_date=block.get("startDate"),
        ))

    coverage_rows = []
    for optional in OPTIONAL_CHANNELS:
        outcome = outcomes.get(optional, {})
        probe_status = outcome.get("status", "unknown")
        probe_healthy = probe_status in {"ok", "ok_fresh", "ok_no_new_expected"}
        coverage_rows.append({
            "page": "Data QA",
            "section": f"Optional coverage: #{optional}",
            "sources": [f"slack:#{optional}"],
            "source_location": SOURCE_LOCATIONS.get(optional, f"Slack #{optional}"),
            "last_checked": last_checked,
            "last_synced": outcome.get("latest_checked_at") if probe_healthy else None,
            "latest_source_post_date": outcome.get("latest_source_post_date"),
            "latest_data_date": None,
            "rows_seen": outcome.get("rows_seen", 0),
            "new_rows_since_last_check": outcome.get("new_rows_since_last_check", 0),
            "status": "green" if probe_healthy else "yellow",
            "schedule_state": "coverage_requirement",
            "expected_cadence": "not blocking",
            "notes": (
                f"Optional channel is live-readable ({probe_status}); retained as non-blocking supplemental coverage."
                if probe_healthy
                else f"Optional channel logged as {probe_status}; does not block deploy."
            ),
            "blocker": None if probe_healthy else f"Optional channel probe is {probe_status}; non-blocking until promoted to required coverage.",
        })
    teamshaw = outcomes.get("teamshaw", {})
    teamshaw_status = "red" if teamshaw.get("status") == "failed" else "green"
    coverage_rows.append({
        "page": "Data QA",
        "section": "Coverage requirement: Megan",
        "sources": ["slack:#teamshaw", "coverage_requirement:megan"],
        "source_location": "Slack #teamshaw — Megan is Team Shaw",
        "last_checked": last_checked,
        "last_synced": None,
        "latest_source_post_date": teamshaw.get("latest_source_post_date"),
        "latest_data_date": None,
        "rows_seen": teamshaw.get("rows_seen", 0),
        "new_rows_since_last_check": teamshaw.get("new_rows_since_last_check", 0),
        "status": teamshaw_status,
        "schedule_state": "coverage_requirement",
        "expected_cadence": "covered by required #teamshaw hourly check",
        "notes": f"Megan confirmed as Team Shaw; covered by required #teamshaw check ({teamshaw.get('status', 'unknown')}).",
        "blocker": None if teamshaw_status == "green" else "Required #teamshaw source check failed.",
    })
    rows.extend(coverage_rows)

    visible_without_sources = [row for row in rows if not row.get("sources")]
    if visible_without_sources:
        raise RuntimeError(f"AC1 failed: rows without mapped sources: {visible_without_sources}")

    return {
        "generated_at": last_checked,
        "timezone": "America/Denver",
        "build_timestamp": last_checked,
        "git_sha": git_sha(),
        "deploy_id": None,
        "source": {
            "control_plane": "tlwb_source_archive.db",
            "runtime_rule": "Vercel runtime reads only committed static artifacts; no SQLite/cross-workspace runtime reads.",
        },
        "required_channels": REQUIRED_CHANNELS,
        "optional_channels": OPTIONAL_CHANNELS,
        "channel_aliases": CHANNEL_ALIASES,
        "rows": rows,
    }


def write_source_health(health: dict[str, Any]) -> None:
    SOURCE_HEALTH_JSON.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_HEALTH_JSON.write_text(json.dumps(health, indent=2, ensure_ascii=True) + "\n")


def build_phase2a_audit(schedule: dict[str, Any], health: dict[str, Any]) -> dict[str, Any]:
    generated_at = iso(now_dt())
    exec_text = executive_adapter_text()
    events = [
        *parse_active_preview_events(exec_text),
        *parse_middle_end_events(exec_text),
        *parse_upcoming_me_events(exec_text),
    ]

    route_events: list[dict[str, Any]] = []
    for block in schedule.get("route_blocks", []):
        status = block.get("status")
        if status not in {"active", "upcoming"}:
            continue
        start_date = block.get("startDate") or generated_at[:10]
        event_id = f"schedule_{slug(block.get('market'))}_{slug(block.get('team'))}_{start_date}"
        route_events.append({
            "event_id": event_id,
            "market_name": block.get("market") or "Unknown",
            "event_type": "preview",
            "segment": "TLWB",
            "team_name": block.get("team") or "Unassigned",
            "start_date": start_date,
            "end_date": block.get("endDate") or start_date,
            "source_id": "upcoming_schedule",
            "source_record_ref": f"phase2a:schedule:{event_id}",
            "status": status,
            "source_state": "event_roster",
            "metrics": {
                "scheduled_sessions": parse_number(str(block.get("eventCount") or 0)),
            },
        })
    events.extend(route_events[:12])

    metric_rows = []
    for event in events:
        for name, value in event.get("metrics", {}).items():
            metric_rows.append({
                "event_id": event["event_id"],
                "metric_name": name,
                "metric_value_num": value,
                "grain": "market",
                "source_id": event.get("source_id"),
                "source_record_ref": event.get("source_record_ref"),
            })

    freshness_manifest = []
    fail_closed_sections = []
    for row in health.get("rows", []):
        manifest_row = {
            "page": row.get("page"),
            "section": row.get("section"),
            "status": row.get("status"),
            "sources": row.get("sources", []),
            "last_checked": row.get("last_checked"),
            "latest_source_post_date": row.get("latest_source_post_date"),
            "latest_data_date": row.get("latest_data_date"),
            "rendered_values": row.get("rendered_values"),
            "blocker": row.get("blocker"),
        }
        freshness_manifest.append(manifest_row)
        if row.get("status") in {"yellow", "red"} and not str(row.get("schedule_state", "")).startswith("coverage_requirement"):
            fail_closed_sections.append(manifest_row)

    required_sections = {
        "Executive / Active preview pace",
        "Executive / Completed ME show-rate groups",
        "Executive / Current upcoming ME pipeline",
        "Marketing / Active markets",
        "Preview / Current Preview Markets",
        "Preview / Session Breakdown",
        "Workshop / ME / Current or Just Completed",
        "Schedule / Calendar and route blocks",
    }
    present_sections = {f"{row.get('page')} / {row.get('section')}" for row in health.get("rows", [])}
    missing_sections = sorted(required_sections - present_sections)

    return {
        "phase": "2A",
        "generated_at": generated_at,
        "timezone": "America/Denver",
        "source": {
            "control_plane": str(ARCHIVE_DB),
            "runtime_rule": "Dashboard runtime reads static phase2a_audit.json; refresh job writes SQLite normalized rows first.",
        },
        "counts": {
            "event_roster": len(events),
            "metric_rows": len(metric_rows),
            "freshness_rows": len(freshness_manifest),
            "fail_closed_sections": len(fail_closed_sections),
        },
        "event_roster": events,
        "normalized_metrics": metric_rows,
        "freshness_manifest": freshness_manifest,
        "fail_closed_sections": fail_closed_sections,
        "acceptance": {
            "required_sections_present": not missing_sections,
            "missing_sections": missing_sections,
            "high_risk_cards_from_normalized_records": len(events) >= 6 and len(metric_rows) >= 18,
            "stale_or_missing_sources_fail_closed": all(row.get("blocker") for row in fail_closed_sections),
        },
    }


def write_phase2a_db_and_artifact(audit: dict[str, Any]) -> None:
    PHASE2A_AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    PHASE2A_AUDIT_JSON.write_text(json.dumps(audit, indent=2, ensure_ascii=True) + "\n")
    with connect_db() as conn:
        conn.execute("delete from normalized_metrics where source_record_ref like 'phase2a:%'")
        conn.execute("delete from normalized_events where event_id like 'preview_%' or event_id like 'middle_end_%' or event_id like 'upcoming_middle_end_%' or event_id like 'schedule_%'")
        conn.execute("delete from reconciliation_items where source_a_ref like 'phase2a:%'")
        for event in audit["event_roster"]:
            conn.execute(
                """
                insert or replace into normalized_events (
                  event_id, market_name, segment, event_type, start_date, end_date,
                  team_name, source_confidence, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    event["event_id"],
                    event["market_name"],
                    event.get("segment"),
                    event.get("event_type"),
                    event.get("start_date"),
                    event.get("end_date"),
                    event.get("team_name"),
                    0.8 if event.get("status") in {"green", "final", "active", "upcoming"} else 0.55,
                ),
            )
        for metric in audit["normalized_metrics"]:
            value = metric.get("metric_value_num")
            conn.execute(
                """
                insert into normalized_metrics (
                  event_id, grain, metric_name, metric_value_num, unit, source_id,
                  source_record_ref, trust_role, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, 'phase2a_normalized', CURRENT_TIMESTAMP)
                """,
                (
                    metric.get("event_id"),
                    metric.get("grain"),
                    metric.get("metric_name"),
                    value,
                    "count" if value is not None else None,
                    metric.get("source_id"),
                    metric.get("source_record_ref"),
                ),
            )
        for row in audit["fail_closed_sections"]:
            conn.execute(
                """
                insert into reconciliation_items (
                  issue_type, status, summary, source_a_ref, decision_source, notes, created_at
                ) values ('stale_or_ambiguous_source', 'open', ?, 'phase2a:source_health', 'phase2a_audit', ?, CURRENT_TIMESTAMP)
                """,
                (
                    f"{row.get('page')} / {row.get('section')}: {row.get('status')}",
                    row.get("blocker") or row.get("latest_source_post_date") or "source not green",
                ),
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--simulate-slack-failure", action="store_true")
    args = parser.parse_args()

    schedule = ensure_schedule_artifact()
    outcomes = fetch_and_archive_slack(args.limit, simulate_failure=args.simulate_slack_failure)
    health = build_source_health(schedule, outcomes)
    write_source_health(health)
    audit = build_phase2a_audit(schedule, health)
    write_phase2a_db_and_artifact(audit)
    red = [row for row in health["rows"] if row["status"] == "red"]
    print(json.dumps({
        "schedule_records": len(schedule.get("records", [])),
        "schedule_route_blocks": len(schedule.get("route_blocks", [])),
        "health_rows": len(health["rows"]),
        "phase2a_event_roster": audit["counts"]["event_roster"],
        "phase2a_metric_rows": audit["counts"]["metric_rows"],
        "phase2a_fail_closed_sections": audit["counts"]["fail_closed_sections"],
        "red_rows": len(red),
        "source_health": str(SOURCE_HEALTH_JSON),
        "phase2a_audit": str(PHASE2A_AUDIT_JSON),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
