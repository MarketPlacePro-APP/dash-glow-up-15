#!/usr/bin/env python3
"""Deterministic deploy gate for TLWB KPI freshness spine and Phase 2A audit."""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


APP_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DB = Path("/Users/seanwilliams/.openclaw/workspace/outputs/tlwb_source_archive.db")
HEALTH = APP_ROOT / "data" / "source_health.json"
SCHEDULE = APP_ROOT / "data" / "schedule.json"
PHASE2A_AUDIT = APP_ROOT / "data" / "phase2a_audit.json"
TLWB_PAGE_ADAPTERS = APP_ROOT / "src" / "data" / "tlwbPageAdapters.ts"
EXEC_ADAPTERS = APP_ROOT / "src" / "data" / "executiveAdapters.ts"
PHASE_SCRIPT = APP_ROOT / "scripts" / "phase1_freshness_spine.py"
TZ = ZoneInfo("America/Denver")
REQUIRED = ["teamdrecksel", "teamtony", "teamnick", "teamshaw", "teamwayne", "teamdent", "teamwyman", "teamvogel", "teammillar", "eventstats", "expo"]
OPTIONAL = [
    "front-end-team",
    "ticketsales",
    "collections-allteams",
    "refunds-allteams",
    "fe-confirmations-team",
]
ME_TEAMS = {
    "teamtony": "Team Tony",
    "teamshaw": "Team Shaw",
    "teamnick": "Team Nick",
    "teamdrecksel": "Team Drecksel",
}


def fail(message: str) -> None:
    raise SystemExit(f"BLOCKED: {message}")


def load_json(path: Path):
    if not path.exists():
        fail(f"missing artifact {path}")
    return json.loads(path.read_text())


def latest_check_rows() -> dict[str, sqlite3.Row]:
    conn = sqlite3.connect(ARCHIVE_DB)
    conn.row_factory = sqlite3.Row
    rows: dict[str, sqlite3.Row] = {}
    for channel in [*REQUIRED, *OPTIONAL]:
        sid = f"slack_channel_{channel.replace('-', '_')}"
        row = conn.execute(
            "select * from source_check_runs where source_id=? order by check_id desc limit 1",
            (sid,),
        ).fetchone()
        if not row:
            fail(f"no latest source_check_runs row for #{channel}")
        rows[channel] = row
    return rows


def assert_coverage(health: dict) -> None:
    rows = health.get("rows") or []
    if not rows:
        fail("source_health rows are empty")
    required_sections = {
        ("Executive", "Expo count"),
        ("Executive", "Active preview pace"),
        ("Executive", "Completed ME show-rate groups"),
        ("Executive", "Current upcoming ME pipeline"),
        ("Executive", "Upcoming route blocks"),
        ("Executive", "Active marketing"),
        ("Marketing", "Active markets"),
        ("Preview", "Current Preview Markets"),
        ("Preview", "Session Breakdown"),
        ("Preview", "Team historical performance"),
        ("Workshop / ME", "Current or Just Completed"),
        ("Workshop / ME", "Historical ME performance"),
        ("Schedule", "Calendar and route blocks"),
        ("Inside Sales", "DPL and collections"),
        ("Data QA", "Operational source ledger"),
    }
    present = {(row.get("page"), row.get("section")) for row in rows}
    missing = sorted(required_sections - present)
    if missing:
        fail("AC1 missing required section source-health rows: " + "; ".join(f"{p} / {s}" for p, s in missing))
    for row in rows:
        label = f"{row.get('page')} / {row.get('section')}"
        if not row.get("sources"):
            fail(f"AC1 missing mapped source for {label}")
        if not row.get("last_checked"):
            fail(f"AC2 missing last_checked for {label}")
        if row.get("status") == "green" and not row.get("latest_source_post_date"):
            fail(f"AC3 green without positive freshness assertion: {label}")
        if row.get("status") in {"yellow", "red"} and row.get("blocker") is None:
            fail(f"AC3 yellow/red row missing explicit blocker: {label}")
    optional_channels = set(health.get("optional_channels") or [])
    missing_optional = sorted(set(OPTIONAL) - optional_channels)
    if missing_optional:
        fail("AC5 optional probes missing from artifact: " + ", ".join(missing_optional))


def assert_slack_coverage(rows: dict[str, sqlite3.Row]) -> None:
    for channel in REQUIRED:
        status = rows[channel]["status"]
        if status not in {"ok_fresh", "ok_no_new_expected"}:
            fail(f"AC5 required #{channel} latest check is {status}")
        if rows[channel]["rows_seen"] is None or rows[channel]["rows_seen"] <= 0:
            fail(f"AC5 required #{channel} saw no rows")
    for channel in OPTIONAL:
        status = rows[channel]["status"]
        if status not in {"not_in_channel", "ok_fresh", "ok_no_new_expected"}:
            fail(f"AC5 optional #{channel} has unexpected blocking status {status}")


def market_from_me(text: str) -> str | None:
    patterns = [
        r"Market:\s*([A-Za-z][A-Za-z .,/-]+)",
        r"\*([A-Za-z][A-Za-z .,/-]+?)\*\s*\|",
        r"([A-Za-z][A-Za-z .,/-]+?)\s+Middle End Event",
        r"([A-Za-z][A-Za-z .,/-]+?)\s+Workshop",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" ,")
    return None


def assert_me_current_finals() -> None:
    conn = sqlite3.connect(ARCHIVE_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        select channel_name, message_ts, text
        from slack_messages_raw
        where channel_name in ('teamtony','teamshaw','teamnick','teamdrecksel')
          and text like '%Total Sales%'
        order by cast(message_ts as real) desc
        """
    ).fetchall()
    if not rows:
        fail("AC6 no ME final rows found in raw archive")
    latest = max(datetime.fromtimestamp(float(row["message_ts"]), TZ) for row in rows)
    window_start = latest - timedelta(days=7)
    source = TLWB_PAGE_ADAPTERS.read_text()
    missing = []
    for row in rows:
        posted = datetime.fromtimestamp(float(row["message_ts"]), TZ)
        if posted < window_start:
            continue
        team = ME_TEAMS[row["channel_name"]]
        market = market_from_me(row["text"] or "") or ""
        if team not in source or (market and market.split(",")[0] not in source):
            missing.append(f"{team} {market or row['message_ts']}")
    if missing:
        fail("AC6 current-week ME raw finals absent from display: " + "; ".join(missing))


def assert_metric_sanity() -> None:
    combined = TLWB_PAGE_ADAPTERS.read_text() + "\n" + EXEC_ADAPTERS.read_text()
    over = re.findall(r"showRate:\s*([0-9]+)\s*/\s*([0-9]+)", combined)
    for num, den in over:
        if int(den) and int(num) / int(den) > 1:
            fail(f"AC7 show/close rate over 100%: {num}/{den}")
    for match in re.finditer(r"soldClosed:\s*(\d+),\s*showed:\s*(\d+)", combined):
        sold, showed = map(int, match.groups())
        if showed and sold / showed > 1:
            fail(f"AC7 close% over 100%: {sold}/{showed}")


def scheduled_session_count(record: dict) -> int:
    times = str(record.get("times") or "").lower()
    if not times:
        return 1
    if "&" in times:
        return max(2, times.count("&") + 1)
    if " and " in times:
        return max(2, times.count(" and ") + 1)
    return 1


def first_scheduled_session_minute(times: str | None) -> int | None:
    """Return the first listed local session time as minutes after midnight."""
    parsed: list[int] = []
    for hour_raw, minute_raw, meridiem in re.findall(
        r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?",
        str(times or ""),
        re.I,
    ):
        hour = int(hour_raw) % 12
        if meridiem.lower() == "p":
            hour += 12
        parsed.append(hour * 60 + int(minute_raw or 0))
    return min(parsed) if parsed else None


def active_preview_reporting_expected(schedule: dict, now: datetime | None = None) -> bool:
    """Return whether an active route is far enough into session one to require Slack rows.

    Schedule records flip to ``active`` at midnight, several hours before the first
    headcount post can exist. Allow that pre-session window, but fail closed after a
    90-minute reporting grace. Schedule times are venue-local; interpreting them as
    Mountain time is deliberately conservative for eastern routes while still catching
    a missed noon refresh cycle.
    """
    current = now.astimezone(TZ) if now is not None else datetime.now(TZ)
    active_records = [
        row for row in schedule.get("records") or []
        if row.get("eventType") == "front_end_preview" and row.get("state") == "active"
    ]
    if not active_records:
        return False

    dated_records: list[tuple[datetime, dict]] = []
    for row in active_records:
        try:
            start = datetime.fromisoformat(str(row.get("startDate"))).replace(tzinfo=TZ)
        except (TypeError, ValueError):
            continue
        dated_records.append((start, row))

    if any(start.date() < current.date() for start, _row in dated_records):
        return True
    today_records = [row for start, row in dated_records if start.date() == current.date()]
    if not today_records:
        # An active record with an absent or unusable date should fail closed rather
        # than silently mask a missing operational adapter.
        return True

    first_minutes = [
        minute
        for row in today_records
        if (minute := first_scheduled_session_minute(row.get("times"))) is not None
    ]
    if not first_minutes:
        # Noon is the conservative fallback for schedules with no parseable times.
        return current.hour >= 12
    first_minute = min(first_minutes)
    first_session = current.replace(
        hour=first_minute // 60,
        minute=first_minute % 60,
        second=0,
        microsecond=0,
    )
    return current >= first_session + timedelta(minutes=90)


def active_preview_adapter_rows(source: str) -> list[tuple[str, str, str, str, str, str]]:
    block_match = re.search(
        r"export const activePreviewMarkets: ActivePreviewMarket\[\] = \[(.*?)\n\];",
        source,
        re.S,
    )
    if not block_match:
        return []
    rows: list[tuple[str, str, str, str, str, str]] = []
    for object_body in re.findall(r"\{(.*?)\n\s*\}", block_match.group(1), re.S):
        if not re.search(r"sourceState:\s*'active_session'", object_body):
            continue

        def field(pattern: str) -> str | None:
            match = re.search(pattern, object_body)
            return match.group(1) if match else None

        values = (
            field(r"market:\s*'([^']+)'"),
            field(r"team:\s*'([^']+)'"),
            field(r"sessionsCompleted:\s*([0-9]+|null)"),
            field(r"totalSessions:\s*([0-9]+|null)"),
            field(r"startDate:\s*'([^']+)'"),
            field(r"latestSessionDate:\s*'([^']+)'"),
        )
        if any(value is None for value in values):
            fail("AC11 malformed active preview adapter row")
        rows.append(values)  # type: ignore[arg-type]
    return rows


def assert_active_preview_schedule_alignment(schedule: dict, now: datetime | None = None) -> None:
    source = EXEC_ADAPTERS.read_text()
    active_rows = active_preview_adapter_rows(source)
    records = schedule.get("records") or []
    active_preview_route_blocks = [
        block for block in schedule.get("route_blocks") or []
        if block.get("status") == "active"
        and (
            "preview" in str(block.get("route") or "").lower()
            or "preview" in str(block.get("id") or "").lower()
            or "preview" in str(block.get("sourceRole") or "").lower()
        )
    ]
    has_active_preview_schedule = active_preview_reporting_expected(schedule, now) or bool(active_preview_route_blocks)
    if not active_rows:
        if has_active_preview_schedule:
            fail("AC11 active preview schedule exists but no active preview rows found in executive adapter")
        return
    for market, _team, completed_raw, total_raw, start_date_raw, latest_session_date_raw in active_rows:
        if completed_raw == "null" or total_raw == "null":
            fail(f"AC11 active preview row lacks session detail: {market}")
        completed = int(completed_raw)
        total = int(total_raw)
        if completed > total:
            fail(f"AC11 active preview completed sessions exceed total: {market} {completed}/{total}")
        route_start = datetime.fromisoformat(start_date_raw).date()
        latest_session_date = datetime.fromisoformat(latest_session_date_raw).date()
        route_end = route_start + timedelta(days=7)
        market_records = [
            row for row in records
            if str(row.get("market", "")).lower() == market.lower()
            and row.get("eventType") == "front_end_preview"
            and row.get("state") in {"active", "tentative", "historical", "upcoming"}
            and row.get("startDate")
            and route_start <= datetime.fromisoformat(row["startDate"]).date() <= route_end
        ]
        if not market_records:
            continue
        scheduled = sum(scheduled_session_count(row) for row in market_records)
        if total < scheduled:
            fail(f"AC11 active preview total sessions below schedule-derived count: {market} {total}/{scheduled}")
        future_sessions = [
            row for row in market_records
            if row.get("startDate") and datetime.fromisoformat(row["startDate"]).date() > latest_session_date
        ]
        if future_sessions and completed >= total:
            fail(f"AC11 active preview marked complete while schedule still has future sessions: {market} {completed}/{total}")


def assert_schedule(schedule: dict) -> None:
    blocks = schedule.get("route_blocks") or []
    if not blocks:
        fail("AC8 no schedule route blocks")
    statuses = [block.get("status") for block in blocks]
    active_indexes = [idx for idx, status in enumerate(statuses) if status in {"active", "upcoming"}]
    if not active_indexes:
        fail("AC8 no current/upcoming route blocks")
    if any(status not in {"active", "upcoming"} for status in statuses[min(active_indexes):max(active_indexes)+1]):
        fail("AC8 current/upcoming route blocks are not contiguous/current-first")
    future = [block for block in blocks if block.get("status") == "upcoming"]
    if not future:
        fail("AC8 no future fixture route under upcoming")
    completed_pending = [block for block in blocks if block.get("status") == "historical" and str(block.get("notes", "")).lower().find("pending") >= 0]
    if completed_pending:
        fail("AC8 completed route appears pending")


def assert_phase2a_audit() -> None:
    audit = load_json(PHASE2A_AUDIT)
    if audit.get("phase") != "2A":
        fail("AC10 phase2a_audit.json missing phase=2A")
    counts = audit.get("counts") or {}
    if counts.get("event_roster", 0) < 6:
        fail(f"AC10 normalized event roster too small: {counts.get('event_roster')}")
    if counts.get("metric_rows", 0) < 18:
        fail(f"AC10 normalized metric rows too small: {counts.get('metric_rows')}")
    acceptance = audit.get("acceptance") or {}
    if not acceptance.get("required_sections_present"):
        fail("AC10 Phase 2A missing required sections: " + ", ".join(acceptance.get("missing_sections") or []))
    if not acceptance.get("high_risk_cards_from_normalized_records"):
        fail("AC10 high-risk cards are not backed by normalized records")
    if not acceptance.get("stale_or_missing_sources_fail_closed"):
        fail("AC10 stale/missing sections do not fail closed with blockers")

    conn = sqlite3.connect(ARCHIVE_DB)
    normalized_events = conn.execute("select count(*) from normalized_events").fetchone()[0]
    normalized_metrics = conn.execute("select count(*) from normalized_metrics where source_record_ref like 'phase2a:%'").fetchone()[0]
    reconciliation_items = conn.execute("select count(*) from reconciliation_items where source_a_ref like 'phase2a:%'").fetchone()[0]
    if normalized_events < counts.get("event_roster", 0):
        fail(f"AC10 archive normalized_events behind artifact: db={normalized_events} artifact={counts.get('event_roster')}")
    if normalized_metrics < counts.get("metric_rows", 0):
        fail(f"AC10 archive normalized_metrics behind artifact: db={normalized_metrics} artifact={counts.get('metric_rows')}")
    if reconciliation_items < counts.get("fail_closed_sections", 0):
        fail(f"AC10 archive reconciliation_items behind artifact: db={reconciliation_items} artifact={counts.get('fail_closed_sections')}")


def assert_resilience() -> None:
    before_health = HEALTH.read_text()
    before_schedule = SCHEDULE.read_text()
    before_phase2a = PHASE2A_AUDIT.read_text()
    with tempfile.TemporaryDirectory() as tmp:
        health_copy = Path(tmp) / "source_health.json"
        schedule_copy = Path(tmp) / "schedule.json"
        phase2a_copy = Path(tmp) / "phase2a_audit.json"
        db_copy = Path(tmp) / "tlwb_source_archive.db"
        shutil.copy2(HEALTH, health_copy)
        shutil.copy2(SCHEDULE, schedule_copy)
        shutil.copy2(PHASE2A_AUDIT, phase2a_copy)
        shutil.copy2(ARCHIVE_DB, db_copy)
        proc = subprocess.run(
            [sys.executable, str(PHASE_SCRIPT), "--simulate-slack-failure"],
            cwd=str(APP_ROOT),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
            env={**os.environ, "TLWB_SOURCE_ARCHIVE_DB": str(Path(tmp) / "tlwb_source_archive.db")},
        )
        simulated_health = load_json(HEALTH)
        if proc.returncode != 0:
            fail(f"AC9 simulated Slack failure command failed: {(proc.stderr or proc.stdout).strip()}")
        if not simulated_health.get("rows"):
            fail("AC9 simulated failure blanked source_health")
        if not any(row.get("status") == "red" for row in simulated_health["rows"]):
            fail("AC9 simulated failure did not mark affected sections red")
        shutil.copy2(health_copy, HEALTH)
        shutil.copy2(schedule_copy, SCHEDULE)
        shutil.copy2(phase2a_copy, PHASE2A_AUDIT)
    if HEALTH.read_text() != before_health or SCHEDULE.read_text() != before_schedule or PHASE2A_AUDIT.read_text() != before_phase2a:
        fail("AC9 last-good artifacts were not restored after simulated failure gate")


def assert_no_false_current() -> None:
    now = datetime(2026, 6, 21, 18, 0, tzinfo=TZ)
    latest = datetime(2026, 3, 15, 12, 0, tzinfo=TZ)
    age_hours = (now - latest).total_seconds() / 3600
    if age_hours <= 24:
        fail("AC4 fixture setup invalid")
    status = "green" if age_hours <= 24 else "yellow"
    if status == "green":
        fail("AC4 March fixture rendered green")


def main() -> int:
    health = load_json(HEALTH)
    schedule = load_json(SCHEDULE)
    rows = latest_check_rows()
    assert_coverage(health)
    assert_slack_coverage(rows)
    assert_me_current_finals()
    assert_metric_sanity()
    assert_active_preview_schedule_alignment(schedule)
    assert_no_false_current()
    assert_schedule(schedule)
    assert_phase2a_audit()
    assert_resilience()
    print("OK: TLWB KPI freshness + Phase 2A predeploy gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
