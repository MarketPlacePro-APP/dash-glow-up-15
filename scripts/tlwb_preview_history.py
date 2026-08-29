#!/usr/bin/env python3
"""Backfill and generate TLWB Preview team history from archived Slack finals.

The dashboard's team history had been a hand-written snapshot that stopped in
May 2026. This command can backfill the canonical SQLite archive from Slack and
then rewrites ``teamPreviewHistory`` from final route posts. Normal scheduled
runs use the accumulated archive; ``--backfill`` is only needed when coverage
has a gap or the archive is rebuilt.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
PREVIEW_CHANNELS = {
    "teamwayne": "Team Wayne",
    "teamdent": "Team Dent",
    "teamwyman": "Team Wyman",
    "teamvogel": "Team Vogel",
    "teammillar": "Team Millar",
}
DEFAULT_DB = Path("/Users/seanwilliams/.openclaw/workspace/outputs/tlwb_source_archive.db")
UPDATER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "update_tlwb_slack_operational_sections.py"


def load_updater():
    spec = importlib.util.spec_from_file_location("tlwb_slack_history_updater", UPDATER_PATH)
    if not spec or not spec.loader:
        raise SystemExit(f"Cannot load Slack updater: {UPDATER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


UPDATER = load_updater()


@dataclass(frozen=True)
class PreviewHistoryRow:
    team: str
    market: str
    date: str
    reg: int
    attended: int
    buying_units: int | None
    sold: int
    message_ts: str


def local_year_start() -> datetime:
    now = datetime.now(TZ)
    return datetime(now.year, 1, 1, tzinfo=TZ)


def slack_api_module():
    sys.path.insert(0, "/Users/seanwilliams/.openclaw/workspace")
    import sean_analytics as slack  # type: ignore

    return slack


def fetch_channel_history(slack: Any, token: str, channel_id: str, oldest: float) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    cursor = ""
    while True:
        params: dict[str, Any] = {
            "channel": channel_id,
            "limit": 200,
            "oldest": str(oldest),
            "inclusive": "true",
        }
        if cursor:
            params["cursor"] = cursor
        response = slack.slack_api("conversations.history", token, params)
        if not response.get("ok"):
            raise SystemExit(f"Slack history fetch failed: {response.get('error', 'unknown_error')}")
        messages.extend(response.get("messages", []))
        cursor = str(response.get("response_metadata", {}).get("next_cursor") or "")
        if not cursor:
            break
    return messages


def backfill_archive(conn: sqlite3.Connection, oldest: datetime) -> tuple[int, dict[str, int]]:
    slack = slack_api_module()
    token = slack.load_token()
    channel_map = slack.resolve_channel_map(token)
    checked_at = datetime.now(TZ).isoformat()
    inserted = 0
    counts: dict[str, int] = {}

    for channel in PREVIEW_CHANNELS:
        channel_id = channel_map.get(channel)
        if not channel_id:
            raise SystemExit(f"Required Slack channel is not visible: #{channel}")
        messages = fetch_channel_history(slack, token, channel_id, oldest.timestamp())
        counts[channel] = len(messages)
        for msg in messages:
            ts = str(msg.get("ts") or "")
            if not ts:
                continue
            before = conn.total_changes
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
                    f"slack_channel_{channel}",
                ),
            )
            if conn.total_changes > before:
                inserted += 1
        conn.commit()
    return inserted, counts


def is_final_route(body: str) -> bool:
    lowered = body.lower()
    return any(marker in lowered for marker in ("final route numbers", "market report", "final numbers"))


def clean_market_name(value: str) -> str:
    market = UPDATER.active_preview_market_display(value)
    market = re.sub(
        r"^(?:TLT\s+MARKET\s+REPORT|PREVIEW\s+FINAL\s+MARKET\s+REPORT|FINAL\s+MARKET\s+REPORT|FINAL\s+NUMBERS|Tax\s+Lien\s+Tour)\s+",
        "",
        market,
        flags=re.I,
    )
    market = re.split(
        r"\s*(?:-\s*)?(?:TDAI\s+)?PREVIEW(?:\s+Team\b.*)?$",
        market,
        maxsplit=1,
        flags=re.I,
    )[0]
    market = re.sub(r"\s+Team\s+(?:Wayne|Dent|Wyman|Vogel|Millar|Gray|Brown)\s*$", "", market, flags=re.I)
    market = re.sub(r"\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*$", "", market, flags=re.I)
    return re.sub(r"\s+", " ", market).strip(" ,-|")


def reconcile_registration(body: str, reg: int, attended: int) -> int:
    """Repair an obvious digit typo only when Slack's posted show factor proves it."""
    if reg <= 5000 or attended <= 0:
        return reg
    match = re.search(r"\bShow\s+Factor\s*:?\s*([0-9]+(?:\.[0-9]+)?)%", body, re.I)
    if not match:
        return reg
    posted_rate = float(match.group(1)) / 100
    if not posted_rate:
        return reg
    candidate = round(attended / posted_rate)
    if 100 <= candidate <= 5000 and abs((attended / candidate) - posted_rate) <= 0.001:
        return candidate
    return reg


def parse_history_row(channel: str, message_ts: str, text: str, year_start: datetime) -> PreviewHistoryRow | None:
    body = UPDATER.clean_body(text)
    if channel not in PREVIEW_CHANNELS or not is_final_route(body):
        return None
    market = UPDATER.market_from_preview(body)
    reg = UPDATER.number_after(body, ("Total Reg",))
    attended = UPDATER.number_after(body, ("Total Head Count",))
    sold = UPDATER.number_after(body, ("Total Deals",))
    if not market or reg is None or attended is None or sold is None:
        return None

    reg = reconcile_registration(body, reg, attended)
    posted = datetime.fromtimestamp(float(message_ts), TZ)
    parsed_event_date = UPDATER.body_date(body)
    event_date = parsed_event_date or posted.date().isoformat()
    if parsed_event_date:
        parsed_dt = datetime.fromisoformat(parsed_event_date).date()
        if abs((posted.date() - parsed_dt).days) > 10:
            # Teams occasionally reuse a prior month/day in the final template.
            # The message timestamp is the safer route-final date in that case.
            event_date = posted.date().isoformat()
    if event_date < year_start.date().isoformat():
        return None
    buying_units = UPDATER.cumulative_master_class(body)
    return PreviewHistoryRow(
        team=PREVIEW_CHANNELS[channel],
        market=clean_market_name(market),
        date=event_date,
        reg=reg,
        attended=attended,
        buying_units=buying_units,
        sold=sold,
        message_ts=message_ts,
    )


def collect_history(conn: sqlite3.Connection, year_start: datetime) -> list[PreviewHistoryRow]:
    placeholders = ",".join("?" for _ in PREVIEW_CHANNELS)
    rows = conn.execute(
        f"""
        select channel_name, message_ts, text
        from slack_messages_raw
        where channel_name in ({placeholders})
          and cast(message_ts as real) >= ?
        order by cast(message_ts as real) desc
        """,
        (*PREVIEW_CHANNELS.keys(), year_start.timestamp()),
    ).fetchall()

    selected: dict[tuple[str, str, str], PreviewHistoryRow] = {}
    for channel, message_ts, text in rows:
        parsed = parse_history_row(str(channel), str(message_ts), str(text or ""), year_start)
        if not parsed:
            continue
        key = (parsed.team, UPDATER.normalize_market_name(parsed.market), parsed.date)
        current = selected.get(key)
        if current is None or float(parsed.message_ts) > float(current.message_ts):
            selected[key] = parsed
    return sorted(selected.values(), key=lambda row: (row.date, float(row.message_ts)), reverse=True)


def ts_row(row: PreviewHistoryRow) -> str:
    buying_units = "null" if row.buying_units is None else str(row.buying_units)
    market = UPDATER.ts_literal(row.market)
    return (
        f"  {{ team: '{row.team}', market: '{market}', date: '{row.date}', "
        f"reg: {row.reg}, attended: {row.attended}, showRate: {row.attended} / {row.reg}, "
        f"salesRate: {row.sold} / {row.attended}, buyingUnits: {buying_units}, "
        f"sold: {row.sold}, workshopAttendance: null }}"
    )


def write_adapter(src: Path, rows: list[PreviewHistoryRow]) -> None:
    page_path = src / "src/data/tlwbPageAdapters.ts"
    text = page_path.read_text(encoding="utf-8")
    replacement = "export const teamPreviewHistory: TeamPreviewHistoryRow[] = [\n" + ",\n".join(ts_row(row) for row in rows) + "\n];"
    page_path.write_text(
        UPDATER.replace_block(text, "export const teamPreviewHistory: TeamPreviewHistoryRow[] = [", "];", replacement),
        encoding="utf-8",
    )


def verify_coverage(rows: list[PreviewHistoryRow]) -> dict[str, tuple[int, str, str]]:
    coverage: dict[str, tuple[int, str, str]] = {}
    for team in PREVIEW_CHANNELS.values():
        team_rows = [row for row in rows if row.team == team]
        if not team_rows:
            raise SystemExit(f"No YTD final Preview rows parsed for {team}; refusing to replace history")
        coverage[team] = (len(team_rows), max(row.date for row in team_rows), min(row.date for row in team_rows))
    return coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--since", help="Backfill start date, YYYY-MM-DD. Defaults to local year start.")
    args = parser.parse_args()

    year_start = local_year_start()
    since = datetime.fromisoformat(args.since).replace(tzinfo=TZ) if args.since else year_start
    conn = sqlite3.connect(args.db)
    if args.backfill:
        inserted, fetched = backfill_archive(conn, since)
        print("Slack backfill fetched " + ", ".join(f"#{name}={count}" for name, count in fetched.items()))
        print(f"Slack backfill inserted {inserted} previously unseen message(s) into {args.db}")

    rows = collect_history(conn, year_start)
    coverage = verify_coverage(rows)
    write_adapter(args.src, rows)
    print(f"Generated {len(rows)} YTD Preview final row(s) in {args.src / 'src/data/tlwbPageAdapters.ts'}")
    for team, (count, newest, oldest) in coverage.items():
        print(f"  {team}: {count} finals · newest {newest} · oldest {oldest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
