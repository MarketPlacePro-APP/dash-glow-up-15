#!/usr/bin/env python3
"""Refresh Slack-backed TLWB KPI dashboard sections from a Slack bundle.

This script intentionally parses a small set of operational post shapes and
fails closed when required current sections cannot be reconciled. It updates
only dashboard adapter files; it never writes back to Slack or source systems.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


PREVIEW_CHANNELS = {
    "teamwayne": "Team Wayne",
    "teamdent": "Team Dent",
    "teamwyman": "Team Wyman",
    "teamvogel": "Team Vogel",
    "teammillar": "Team Millar",
}

ME_CHANNELS = {
    "teamtony": "Team Tony",
    "teamshaw": "Team Shaw",
    "teamdrecksel": "Team Drecksel",
    "teamnick": "Team Nick",
}


def team_speaker_label(team: str, speaker: str | None = None) -> str:
    speaker = speaker or team.removeprefix("Team ").strip()
    return f"{team} · Speaker {speaker}"


@dataclass
class SlackMessage:
    channel: str
    posted_at: str
    ts: str
    body: str


def clean_body(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_int(value: str | None) -> int | None:
    if not value:
        return None
    return int(value.replace(",", "").strip())


def clean_money(value: str | None) -> int | None:
    if not value:
        return None
    return int(round(float(value.replace(",", "").replace("$", "").strip())))


def number_after(body: str, labels: tuple[str, ...]) -> int | None:
    for label in labels:
        pattern = r"\s*".join(re.escape(part) for part in label.split())
        match = re.search(rf"{pattern}\s*:?\s*\$?\s*([0-9][0-9,]*(?:\.\d+)?)", body, re.I)
        if match:
            if "." in match.group(1):
                return clean_money(match.group(1))
            return clean_int(match.group(1))
    return None


def cumulative_master_class(body: str) -> int | None:
    """Return the cumulative Master Class registrations in a result post."""
    match = re.search(
        r"Master\s*Class(?:\s+Tampa)?\s*:?\s*(?:\([^)]+\)\s*:?)?\s*([0-9][0-9,]*)",
        body,
        re.I,
    )
    return clean_int(match.group(1)) if match else None


def master_class_speaker(body: str) -> str | None:
    match = re.search(
        r"Master\s*Class(?:\s+Tampa)?\s*:?\s*\(([^)]+)\)\s*:",
        body,
        re.I,
    )
    return re.sub(r"\s+", " ", match.group(1)).strip().title() if match else None


def body_date(body: str) -> str | None:
    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", body)
    if match:
        month, day, year = (int(part) for part in match.groups())
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return None

    month_match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b",
        body,
        re.I,
    )
    if not month_match:
        return None
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    month = months[month_match.group(1).lower()]
    day = int(month_match.group(2))
    year = int(month_match.group(3))
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def money_after(body: str, labels: tuple[str, ...]) -> int | None:
    for label in labels:
        pattern = r"\s*".join(re.escape(part) for part in label.split())
        match = re.search(rf"{pattern}\s*:?\s*\$?\s*([0-9][0-9,]*(?:\.\d+)?)", body, re.I)
        if match:
            return clean_money(match.group(1))
    return None


def percent_rate(numerator: int | None, denominator: int | None) -> str:
    if not numerator or not denominator:
        return "0"
    return f"{numerator} / {denominator}"


def scheduled_session_count(record: dict) -> int:
    times = str(record.get("times") or "").lower()
    if not times:
        return 1
    if "&" in times:
        return max(2, times.count("&") + 1)
    if " and " in times:
        return max(2, times.count(" and ") + 1)
    return 1


def schedule_total_for_market(schedule_records: list[dict], market: str, route_start: str) -> int:
    try:
        start = datetime.fromisoformat(route_start).date()
    except ValueError:
        return 0
    end = start + timedelta(days=7)
    total = 0
    market_key = normalize_market_name(market)
    for row in schedule_records:
        # Slack headings commonly carry a state suffix (for example
        # ``Indianapolis, IN`` / ``Indianapolis, IND``) while the schedule
        # route is stored as ``Indianapolis``. Compare canonical market keys so
        # the denominator comes from the schedule instead of collapsing to the
        # number of sessions seen so far.
        if normalize_market_name(str(row.get("market", ""))) != market_key:
            continue
        if row.get("eventType") != "front_end_preview":
            continue
        if row.get("state") not in {"active", "tentative", "historical", "upcoming"}:
            continue
        if not row.get("startDate"):
            continue
        try:
            row_date = datetime.fromisoformat(str(row["startDate"])).date()
        except ValueError:
            continue
        if start <= row_date <= end:
            total += scheduled_session_count(row)
    return total


def parse_messages(slack_text: str) -> list[SlackMessage]:
    pattern = re.compile(
        r"--- #(?P<channel>[a-z0-9_-]+) (?P<posted_at>[^ ]+) ts=(?P<ts>[0-9.]+)[^\n]*\n(?P<body>.*?)(?=\n--- #|\n## #|\Z)",
        re.S,
    )
    return [
        SlackMessage(
            channel=match.group("channel"),
            posted_at=match.group("posted_at"),
            ts=match.group("ts"),
            body=clean_body(match.group("body")),
        )
        for match in pattern.finditer(slack_text)
    ]


def latest_fetched_at(messages: list[SlackMessage]) -> str:
    if not messages:
        raise SystemExit("No Slack messages parsed from bundle")
    latest = max(messages, key=lambda msg: msg.posted_at)
    return latest.posted_at


def ts_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def numeric_literal(value: int | float | str | None) -> str:
    return "null" if value is None else str(value)


def replace_block(text: str, start: str, end: str, replacement: str) -> str:
    start_idx = text.index(start)
    end_idx = text.index(end, start_idx) + len(end)
    return text[:start_idx] + replacement + text[end_idx:]


def channel_segment(body: str, label: str, next_labels: tuple[str, ...]) -> str:
    start = re.search(rf"{re.escape(label)}\s*:?", body, re.I)
    if not start:
        return ""
    end = len(body)
    for next_label in next_labels:
        match = re.search(rf"{re.escape(next_label)}\s*:?", body[start.end() :], re.I)
        if match:
            end = min(end, start.end() + match.start())
    return body[start.end() : end]


def current_marketing_facts(messages: list[SlackMessage]) -> list[dict]:
    """Return the current rolling #eventstats market population.

    The bundle is newest-first by convention, but sort explicitly and dedupe by
    market so collection order cannot change the result. Keep every market whose
    advertised start is within seven days before the latest Event Stats post or
    later. This preserves just-started routes plus upcoming campaigns without a
    fixed first-N cap that can silently drop later markets such as Portland.
    """
    facts: list[dict] = []
    seen: set[str] = set()
    event_messages = sorted(
        (msg for msg in messages if msg.channel == "eventstats"),
        key=lambda msg: msg.posted_at,
        reverse=True,
    )
    for msg in event_messages:
        body = msg.body
        if "workshop" not in body.lower() or "Total:" not in body:
            continue
        market_match = re.search(r"^(?:\s*:[^:\s]+:)?\s*([A-Za-z][A-Za-z., /-]+?)\s*-\s*1\s+workshop", body, re.I)
        starts_match = re.search(r"Starts,\s*([^)]+)\)", body, re.I)
        if not market_match or not starts_match:
            continue
        market = market_match.group(1).strip().replace(" ,", ",")
        key = market.lower()
        if key in seen:
            continue
        starts = starts_match.group(1).strip()
        start_date = parse_start_date(starts)
        if not start_date:
            raise SystemExit(f"Could not parse #eventstats start date for {market} from ts={msg.ts}")
        channels: list[dict[str, int | str]] = []
        for label, out_label in (
            ("Facebook", "Facebook"),
            ("Youtube", "YouTube"),
            ("Google Search", "Google Search"),
            ("Total", "Total"),
        ):
            segment = channel_segment(body, label, ("Facebook", "Youtube", "Google Search", "Total"))
            # Some valid Event Stats posts omit an unused optional channel
            # entirely (for example Grand Rapids had no Google Search row).
            # Preserve a stable four-row UI shape without rejecting the whole
            # dashboard refresh; Total remains mandatory and malformed rows
            # that are actually present still fail closed.
            if not segment.strip() and label != "Total":
                regs = spend = cpr = 0
            else:
                regs = number_after(segment, ("Reg",))
                spend = money_after(segment, ("Spend",))
                cpr = money_after(segment, ("CPR",))
            if regs is None or spend is None or cpr is None:
                raise SystemExit(f"Could not parse #eventstats {market} {label} row from ts={msg.ts}")
            channels.append({"channel": out_label, "regs": regs, "spend": spend, "cpr": cpr})
        seen.add(key)
        facts.append({
            "market": market,
            "starts": starts,
            "start_date": start_date,
            "posted_at": msg.posted_at,
            "channels": channels,
        })

    if not facts:
        return []
    reference_date = max(datetime.fromisoformat(str(row["posted_at"])).date() for row in facts)
    cutoff = reference_date - timedelta(days=7)
    current = [row for row in facts if datetime.fromisoformat(str(row["start_date"])).date() >= cutoff]
    current.sort(key=lambda row: (str(row["start_date"]), str(row["market"])))
    return current


def parse_marketing(messages: list[SlackMessage]) -> tuple[list[str], str]:
    facts = current_marketing_facts(messages)
    if len(facts) < 4:
        raise SystemExit(f"Parsed only {len(facts)} active #eventstats markets; refusing to ship partial marketing state")
    rows: list[str] = []
    for fact in facts:
        channels = [
            f"      {{ channel: '{row['channel']}', regs: {row['regs']}, spend: {row['spend']}, cpr: {row['cpr']} }}"
            for row in fact["channels"]
        ]
        rows.append(
            "  {\n"
            f"    market: '{ts_literal(str(fact['market']))}',\n"
            f"    startDate: '{fact['start_date']}',\n"
            f"    starts: '{ts_literal(str(fact['starts']))}',\n"
            "    channels: [\n"
            + ",\n".join(channels)
            + "\n    ]\n"
            "  }"
        )
    latest_at = max(str(row["posted_at"]) for row in facts)
    return rows, latest_at


def parse_pending_preview_markets(
    messages: list[SlackMessage],
    represented_market_keys: set[str],
    schedule_records: list[dict] | None = None,
) -> list[str]:
    """Create pre-event Preview cards from current Event Stats registration truth."""
    schedule_records = schedule_records or []
    rendered: list[str] = []
    for fact in current_marketing_facts(messages):
        market = str(fact["market"])
        market_key = normalize_market_name(market)
        if market_key in represented_market_keys:
            continue
        start_date = str(fact["start_date"])
        start = datetime.fromisoformat(start_date).date()
        candidates: list[tuple[int, str]] = []
        for row in schedule_records:
            if row.get("eventType") != "front_end_preview":
                continue
            if normalize_market_name(str(row.get("market") or "")) != market_key:
                continue
            row_date_text = str(row.get("startDate") or "")
            if not row_date_text:
                continue
            row_date = datetime.fromisoformat(row_date_text).date()
            if abs((row_date - start).days) <= 7:
                candidates.append((abs((row_date - start).days), str(row.get("team") or "")))
        candidates.sort()
        team = candidates[0][1] if candidates else ""
        if not team or re.search(r"unassigned|pending|ops\s*/", team, re.I):
            team = "Preview team pending"
        total = next((row for row in fact["channels"] if row["channel"] == "Total"), None)
        if total is None:
            raise SystemExit(f"Current #eventstats market {market} has no Total row")
        registered = int(total["regs"])
        source_note = (
            f"Pre-event #eventstats registration and spend source at {fact['posted_at']}: "
            f"{registered} total registrations; route starts {fact['starts']}. "
            "Slack floor/session results are pending until the first Preview session posts."
        )
        rendered.append(
            "  {\n"
            f"    market: '{ts_literal(market)}',\n"
            f"    team: '{ts_literal(team)} / #eventstats',\n"
            "    sessionsCompleted: null,\n"
            "    totalSessions: null,\n"
            f"    registered: {registered},\n"
            "    attendedCutoff: 0,\n"
            "    sales: 0,\n"
            "    routeDeals: 0,\n"
            "    previewShowRate: 0,\n"
            "    salesRate: 0,\n"
            "    status: 'yellow',\n"
            "    sourceState: 'pending_source',\n"
            f"    startDate: '{start_date}',\n"
            f"    sourcePostedAt: '{fact['posted_at']}',\n"
            f"    sourceNote: '{ts_literal(source_note)}'\n"
            "  }"
        )
    return rendered


def parse_start_date(starts: str, reference_year: int = 2026) -> str | None:
    match = re.search(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?\b",
        starts,
        re.I,
    )
    if not match:
        return None
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    month = months[match.group(1).lower()]
    day = int(match.group(2))
    return datetime(reference_year, month, day).date().isoformat()


def schedule_team_lookup(src: Path) -> dict[tuple[str, str], str]:
    path = src / "data/schedule.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    blocks = data.get("sections", {}).get("preview_routes") or data.get("route_blocks") or []
    lookup: dict[tuple[str, str], str] = {}
    for block in blocks:
        market = normalize_market_name(str(block.get("market") or ""))
        start = str(block.get("startDate") or "")
        team = str(block.get("team") or "")
        if market and start and team:
            lookup[(market, start)] = team
    return lookup


def parse_upcoming_pipeline(messages: list[SlackMessage], src: Path) -> list[str]:
    """Build the current/next ME pipeline from the schedule and live Slack.

    The old implementation hard-coded one July cohort, so it became empty as
    soon as those three finals landed. The schedule now defines the rolling
    route population; Slack confirmations fill sold/projected values when they
    exist, and unsourced values remain explicitly pending.
    """
    schedule_path = src / "data" / "schedule.json"
    if not schedule_path.exists():
        raise SystemExit("Schedule artifact missing; cannot build upcoming ME pipeline")
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    generated_raw = str(schedule.get("generated_at") or latest_fetched_at(messages)).replace("Z", "+00:00")
    today = datetime.fromisoformat(generated_raw).date()
    horizon = today + timedelta(days=14)
    routes = schedule.get("sections", {}).get("middle_end_workshop_routes") or []
    preview_routes = schedule.get("sections", {}).get("preview_routes") or []
    confirmations = me_confirmation_sources(messages)
    preview_finals = preview_sold_sources(messages)

    final_dates: dict[str, list[str]] = {}
    for msg in messages:
        if msg.channel not in ME_CHANNELS or "Total Sales" not in msg.body or "Written" not in msg.body or "Collected" not in msg.body:
            continue
        market = market_from_me(msg.body)
        if market:
            final_dates.setdefault(normalize_market_name(market), []).append(msg.posted_at[:10])

    rendered: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for route in sorted(routes, key=lambda row: (str(row.get("startDate") or ""), str(row.get("market") or ""))):
        market = str(route.get("market") or "").strip()
        start_text = str(route.get("startDate") or "")
        end_text = str(route.get("endDate") or start_text)
        if not market or not start_text:
            continue
        start = datetime.fromisoformat(start_text).date()
        end = datetime.fromisoformat(end_text).date()
        if end < today or start > horizon or str(route.get("status")) not in {"active", "upcoming"}:
            continue
        market_key = normalize_market_name(market)
        dedupe_key = (market_key, start_text)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        if any(start <= datetime.fromisoformat(final_date).date() <= end + timedelta(days=1) for final_date in final_dates.get(market_key, [])):
            continue

        team_key = str(route.get("teamKey") or "").lower()
        channel = "teamdrecksel" if team_key in {"drexel", "drecksel"} else f"team{team_key}" if team_key else ""
        confirmation = confirmations.get((market_key, channel))
        if confirmation:
            posted = datetime.fromisoformat(str(confirmation["posted_at"])).date()
            if not (start - timedelta(days=10) <= posted <= end + timedelta(days=1)):
                confirmation = None
        floor_count = me_floor_count_source(messages, channel, start, end) if start <= today <= end + timedelta(days=1) else None

        preview_final = preview_finals.get(market_key)
        if preview_final:
            posted = datetime.fromisoformat(str(preview_final["posted_at"])).date()
            if not (start - timedelta(days=60) <= posted <= end):
                preview_final = None

        preceding = []
        for preview_route in preview_routes:
            if normalize_market_name(str(preview_route.get("market") or "")) != market_key:
                continue
            preview_end_text = str(preview_route.get("endDate") or preview_route.get("startDate") or "")
            if not preview_end_text:
                continue
            preview_end = datetime.fromisoformat(preview_end_text).date()
            if start - timedelta(days=60) <= preview_end <= start:
                preceding.append((preview_end_text, str(preview_route.get("team") or "")))
        preceding.sort(reverse=True)

        preview_sold = int(confirmation["sold"]) if confirmation and int(confirmation.get("sold") or 0) else int(preview_final["sold"]) if preview_final else None
        projected = int(floor_count["count"]) if floor_count else int(confirmation["confirmed"]) if confirmation and int(confirmation.get("confirmed") or 0) else None
        preview_team = str(preview_final["team"]) if preview_final else (preceding[0][1] if preceding else "Pending preview source")
        if preview_final:
            preview_team = f"{preview_team} / #{preview_final['channel']}"
        source_posted_at = str(floor_count["posted_at"]) if floor_count else str(confirmation["posted_at"]) if confirmation else str(route.get("fetchedAt") or generated_raw)
        if floor_count:
            guests = int(floor_count.get("guests") or 0)
            preview_context = f"{preview_sold} preview sold; " if preview_sold is not None else "Preview sold pending; "
            discrepancy = (
                f"A later roster check reports {int(floor_count['roster_count'])} students; reconciliation is pending. "
                if floor_count.get("roster_count") is not None
                else ""
            )
            source_note = (
                f"Workshop Team Scheduling plus #{channel} current floor count at {floor_count['posted_at']}: "
                f"{preview_context}{projected} BU on site"
                + (f" and {guests} guests" if guests else "")
                + f". {discrepancy}ME sold remains pending until the final Event Stats post lands."
            )
        elif confirmation:
            source_note = (
                f"Workshop Team Scheduling plus #{confirmation['channel']} update: "
                f"{preview_sold} preview sold and {projected} currently confirmed BU. "
                "ME sold remains pending until the final Event Stats post lands."
            )
        elif preview_final:
            source_note = (
                f"Workshop Team Scheduling plus #{preview_final['channel']} preview final: {preview_sold} buyers sold. "
                "Confirmed BU are pending until the matching ME team update; ME sold remains pending until the final Event Stats post."
            )
        else:
            source_note = (
                "Workshop Team Scheduling defines this upcoming route. Preview sold and confirmed BU are pending "
                "until a matching team update or preview final is available; ME sold remains pending until the final Event Stats post."
            )
        rendered.append((
            start_text,
            "  {\n"
            f"    market: '{ts_literal(market)}',\n"
            f"    previewTeam: '{ts_literal(preview_team)}',\n"
            f"    middleEndTeam: '{ts_literal(str(route.get('team') or 'Pending team'))}',\n"
            f"    startDate: '{start_text}',\n"
            f"    endDate: '{end_text}',\n"
            f"    previewSold: {numeric_literal(preview_sold)},\n"
            f"    projectedBuyingUnits: {numeric_literal(projected)},\n"
            "    middleEndSold: null,\n"
            f"    source: '{ts_literal(source_note)}',\n"
            f"    sourcePostedAt: '{ts_literal(source_posted_at)}'\n"
            "  }"
        ))
    return [row for _start, row in rendered[:6]]


def parse_expo(messages: list[SlackMessage]) -> tuple[dict[str, int | str | None], str]:
    def expo_count(body: str, label: str) -> int | None:
        match = re.search(rf"([0-9][0-9,]*)\s+{re.escape(label)}", body, re.I)
        if match:
            return clean_int(match.group(1))
        return number_after(body, (label,))

    for msg in [m for m in messages if m.channel == "expo"]:
        body = msg.body
        if "Investor Expo" not in body or "Total Headcount" not in body:
            continue
        label_match = re.search(r"([A-Za-z]+ Investor Expo)", body)
        keyspire = expo_count(body, "KeySpire")
        if keyspire is None:
            keyspire = expo_count(body, "Keyspire")
        if keyspire is None:
            keyspire = 0
        return (
            {
                "label": label_match.group(1) if label_match else "Investor Expo",
                "bus": expo_count(body, "BU"),
                "guests": expo_count(body, "Guests") or expo_count(body, "Guest"),
                "utl": expo_count(body, "UTL"),
                "tlwb": expo_count(body, "TLWB"),
                "keyspire": keyspire,
                "total": number_after(body, ("Total Headcount",)),
                "sourcePostedAt": msg.posted_at,
            },
            msg.posted_at,
        )
    raise SystemExit("No current #expo Investor Expo count post found")


def market_from_preview(body: str) -> str | None:
    patterns = [
        # ``parse_messages`` normalizes Slack mrkdwn before this parser runs, so
        # the same heading normally arrives as ``White Plains Saturday ...``.
        r"^([A-Za-z][A-Za-z .,/'-]+?)\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
        # Several preview teams post plain Slack-mrkdwn headings with no WK
        # prefix or pipe: ``*White Plains* *Saturday 8/29/26* ...``.
        r"^\*+([A-Za-z][A-Za-z .,/'-]+?)\*+\s+\*+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
        # Raw Slack finals may flatten the title to
        # ``Raleigh, NC Team Wayne WK 30 FINAL NUMBERS`` with no pipe before
        # the team/week label. Capture only the leading market segment.
        r"^([A-Za-z][A-Za-z .,/\'-]+?)\s+Team\s+[A-Za-z]+\s+WK\s+\d+\s+FINAL\s+NUMBERS\b",
        r"([A-Za-z][A-Za-z .,/'-]+?)\s+Final Numbers",
        # Combined result/final posts sometimes render the final heading as
        # ``FINAL ROUTE NUMBERS … FINAL NUMBERS Tulsa, OK| Preview`` instead
        # of ``Tulsa - Preview``. Handle those explicit shapes before the
        # broader route patterns.
        r"FINAL ROUTE NUMBERS[^A-Za-z]*(?:WK\.?\s*\d+\s*\|\s*)?(?:FINAL NUMBERS\s+)?([A-Za-z][A-Za-z .,/'-]+?)\s*\|\s*Preview",
        r"FINAL NUMBERS\s+([A-Za-z][A-Za-z .,/'-]+?)\s*\|\s*Preview",
        r"([A-Za-z][A-Za-z .,/'-]+?)\s*-\s*Preview",
        r"([A-Za-z][A-Za-z .,/'-]+?)\s+Previews",
        r"WK\s+\d+\s*-\s*([A-Za-z][A-Za-z .,/'-]+)",
        r"WK\s+\d+\s*\|\s*\|\s*([A-Za-z][A-Za-z .,/'-]+)",
        r"WK\s+\d+\s*\|\s*([A-Za-z][A-Za-z .,/'-]+)",
        r"^\s*([A-Za-z][A-Za-z .,/'-]+?)\s*\|",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.I)
        if match:
            market = match.group(1).strip()
            if re.fullmatch(r"WK\.?\s*\d+", market, re.I):
                continue
            # Some result headings insert the venue between the city/state and
            # weekday, for example ``Atlanta, Georgia Courtyard Atlanta Decatur
            # Downtown/Emory Saturday``. The broad WK heading patterns must
            # accept those posts, but the venue must not become part of the
            # market key or the result will be orphaned from its headcount.
            city_state = re.match(
                r"^(.+?,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IND|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|"
                r"Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia))\b",
                market,
                re.I,
            )
            if city_state:
                market = city_state.group(1)
            market = re.sub(r"\s+Final\s+Numbers\s*$", "", market, flags=re.I)
            market = re.sub(r"\bSaint\b", "St.", market)
            return market.replace("Meyers", "Myers")
    return None


def preview_team_from_final(body: str, channel: str) -> str:
    """Prefer the team explicitly printed in a final over the channel alias.

    Preview channels can be reused by another floor team (for example, Team
    Gray posts in #teamwayne). Treating the channel name as team ownership
    silently mislabels those final cards.
    """
    match = re.search(
        r"\bTeam\s+([A-Za-z][A-Za-z '&/-]{0,40}?)(?:\s*\|\s*)*Total\s+Reg\b",
        body,
        re.I,
    )
    if not match:
        return PREVIEW_CHANNELS[channel]
    team_name = re.sub(r"\s+", " ", match.group(1)).strip()
    return f"Team {team_name}"


def normalize_market_name(value: str) -> str:
    market = value.lower()
    market = market.replace("wpb", "west palm beach")
    market = market.replace("fort meyers", "fort myers")
    # Slack session/final posts often spell Saint Louis while #eventstats and
    # the schedule use St. Louis. Treat saint/st as the same city token.
    market = re.sub(r"\bsaint\b", "st", market)
    # Some flattened Slack headings let the weekday immediately following the
    # market bleed into the market capture (for example ``Saint Louis, MO
    # Wednesday``). Remove only a trailing weekday before state normalization so
    # the session key still joins its explicit final-route report.
    market = re.sub(
        r"(?:,\s*|\s+)(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s*$",
        "",
        market,
    )
    # Slack finals sometimes spell out the trailing state while Preview and
    # schedule sources use the abbreviation (for example, ``Tulsa Oklahoma``
    # versus ``Tulsa, OK``). Remove only a *trailing* full state name so city
    # names such as ``Oklahoma City`` remain intact.
    market = re.sub(
        r"(?:,\s*|\s+)(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming)\s*$",
        "",
        market,
    )
    market = re.sub(
        r"\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy|dc|ind)\b",
        "",
        market,
    )
    market = re.sub(r"[^a-z]+", " ", market)
    return re.sub(r"\s+", " ", market).strip()


def me_confirmation_sources(messages: list[SlackMessage]) -> dict[tuple[str, str], dict[str, int | str]]:
    """Return the latest pre-workshop sold/confirmed update per ME market/channel.

    ME teams normally post a short ``<Market> Update`` before the workshop,
    followed by a separate Event Stats final. These updates are the current
    source for preview-sold and projected/confirmed BU pipeline values.
    Keying by both market and channel prevents a copied market heading in one
    team's channel from overwriting another team's valid update.
    """
    sources: dict[tuple[str, str], dict[str, int | str]] = {}
    patterns = (
        r"^\s*([A-Za-z][A-Za-z .,'/-]+?)\s+(?:Final\s+)?Update\b",
        r"^\s*([A-Za-z][A-Za-z .,'/-]+?)\s+Final\s+Details\b",
    )
    for msg in messages:
        if msg.channel not in ME_CHANNELS:
            continue
        market = None
        for pattern in patterns:
            match = re.search(pattern, msg.body, re.I)
            if match:
                market = re.sub(r"\s+", " ", match.group(1)).strip(" ,")
                break
        if not market:
            continue
        sold = number_after(msg.body, ("Sold",))
        confirmed = number_after(msg.body, ("Total Confirmed", "Confirmed"))
        guests = number_after(msg.body, ("Guests", "Guest"))
        if sold is None and confirmed is None:
            continue
        key = (normalize_market_name(market), msg.channel)
        current = sources.get(key)
        if current and str(current["posted_at"]) >= msg.posted_at:
            continue
        sources[key] = {
            "market": market,
            "sold": sold if sold is not None else 0,
            "confirmed": confirmed if confirmed is not None else 0,
            "guests": guests if guests is not None else 0,
            "channel": msg.channel,
            "team": ME_CHANNELS[msg.channel],
            "posted_at": msg.posted_at,
        }
    return sources


def me_floor_count_source(
    messages: list[SlackMessage],
    channel: str,
    start: date,
    end: date,
) -> dict[str, int | str] | None:
    """Return the latest explicit on-floor BU count for one active workshop.

    Active workshop channels often stop repeating the market name once check-in
    begins. Bind concise floor-count posts to the scheduled team/channel and
    route window instead of leaving the pre-event confirmation frozen in place.
    """
    floor: dict[str, int | str] | None = None
    roster: dict[str, int | str] | None = None
    for msg in messages:
        if msg.channel != channel:
            continue
        posted = datetime.fromisoformat(msg.posted_at).date()
        if not (start <= posted <= end + timedelta(days=1)):
            continue
        count_match = re.search(r"\bBU[’']?s?\s*=\s*([0-9][0-9,]*)\b", msg.body, re.I)
        if not count_match:
            count_match = re.search(r"\b([0-9][0-9,]*)\s+BU(?:[’']?s)?\b", msg.body, re.I)
        guest_match = re.search(r"\bGuests?\s*=\s*([0-9][0-9,]*)\b", msg.body, re.I)
        if not guest_match:
            guest_match = re.search(r"\b([0-9][0-9,]*)\s+Guests?\b", msg.body, re.I)
        if count_match and (floor is None or str(floor["posted_at"]) < msg.posted_at):
            floor = {
                "count": clean_int(count_match.group(1)) or 0,
                "guests": (clean_int(guest_match.group(1)) or 0) if guest_match else 0,
                "posted_at": msg.posted_at,
            }
        roster_match = re.search(r"\bcounting\s+([0-9][0-9,]*)\s+students?\b.*\broster\b", msg.body, re.I)
        if roster_match and (roster is None or str(roster["posted_at"]) < msg.posted_at):
            roster = {"count": clean_int(roster_match.group(1)) or 0, "posted_at": msg.posted_at}
    if floor and roster and str(roster["posted_at"]) > str(floor["posted_at"]) and int(roster["count"]) != int(floor["count"]):
        floor["roster_count"] = int(roster["count"])
        floor["roster_posted_at"] = str(roster["posted_at"])
    return floor


def active_preview_market_display(value: str) -> str:
    market = re.sub(r"\s+", " ", value).strip(" ,")
    market = re.sub(r"\bSaint\b", "St.", market, flags=re.I)
    market = re.sub(
        r"\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$",
        "",
        market,
        flags=re.I,
    )
    market = re.sub(r",\s*(AL|FL|TX|NC|SC|OH|MA|AZ|WA)\b\.?", "", market, flags=re.I)
    market = re.sub(r"\b(Previews?|Preview)\b$", "", market, flags=re.I).strip(" ,")
    return market.replace("Meyers", "Myers")


def is_preview_final(body: str) -> bool:
    """Return True for any supported preview final-report heading, case-insensitively."""
    return bool(re.search(r"\b(?:FINAL\s+ROUTE\s+NUMBERS|FINAL\s+NUMBERS|MARKET\s+REPORT)\b", body, re.I))


def preview_final_futures(body: str) -> int:
    """Return the Futures count from the final report, not the live session.

    Combined Slack posts can contain ``Session Futures`` before the final-route
    block. Slice from the last final marker so Master Class sold can remain
    distinct from total route deals including futures.
    """
    lowered = body.lower()
    positions = [lowered.rfind(marker) for marker in ("final route numbers", "final numbers", "market report")]
    start = max(positions)
    final_body = body[start:] if start >= 0 else body
    return number_after(final_body, ("Futures",)) or 0


def preview_sold_sources(messages: list[SlackMessage]) -> dict[str, dict[str, int | str]]:
    sold_by_market: dict[str, dict[str, int | str]] = {}
    for msg in messages:
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        body = msg.body
        if not is_preview_final(body):
            continue
        market = market_from_preview(body)
        deals = number_after(body, ("Total Deals",))
        if not market or deals is None:
            continue
        key = normalize_market_name(market)
        current = sold_by_market.get(key)
        if current and str(current["posted_at"]) >= msg.posted_at:
            continue
        sold_by_market[key] = {
            "market": market,
            "sold": deals,
            "channel": msg.channel,
            "team": PREVIEW_CHANNELS[msg.channel],
            "posted_at": msg.posted_at,
        }
    return sold_by_market


def session_key(body: str) -> tuple[int, int] | None:
    for pattern in (
        r"\bDay\s+(\d+)\s+Session\s+(\d+)\b",
        r"\bD\s*(\d+)\s*S\s*(\d+)\b",
    ):
        match = re.search(pattern, body, re.I)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


def preview_session_speaker(
    channel: str,
    market_key: str,
    date_value: str,
    day: int,
    session: int,
    reported_speaker: str | None,
) -> tuple[str, str]:
    """Return the speaker who delivered a preview session.

    Slack's ``Master Class: (Name)`` value is cumulative and can retain the
    earlier speaker after the floor speaker changes. Troy confirmed that Lura
    delivered Team Millar's final two Chicago sessions on 2026-07-29, even
    though both cumulative Master Class lines remained labeled Jay.
    """
    if (
        channel == "teammillar"
        and market_key == "chicago"
        and date_value == "2026-07-29"
        and day == 5
        and session in {1, 2}
    ):
        return "Lura", "Troy-confirmed floor-speaker correction for Team Millar's final two Chicago sessions"
    speaker = (reported_speaker or "").strip()
    return speaker, "Slack Master Class label" if speaker else "team-name fallback"


def parse_active_preview_rows(messages: list[SlackMessage], schedule_records: list[dict] | None = None) -> tuple[list[str], list[str], str, str]:
    schedule_records = schedule_records or []
    sessions: dict[tuple[str, str, str, int, int], dict[str, int | str | float]] = {}
    latest_session_date = ""
    latest_posted_at = ""

    finalized_markets: set[str] = set()
    final_totals: dict[str, tuple[int, int, int]] = {}
    for msg in messages:
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        if not is_preview_final(msg.body):
            continue
        final_market = market_from_preview(msg.body)
        if not final_market:
            continue
        final_key = normalize_market_name(active_preview_market_display(final_market))
        finalized_markets.add(final_key)
        final_reg = number_after(msg.body, ("Total Reg",))
        final_headcount = number_after(msg.body, ("Total Head Count",))
        final_deals = number_after(msg.body, ("Total Deals",))
        if final_reg is not None and final_headcount is not None and final_deals is not None:
            final_totals[final_key] = (final_reg, final_headcount, final_deals)

    # Process chronologically so a result post can reconcile to the nearest
    # preceding headcount post even when pasted Day/Session labels are wrong.
    for msg in sorted(messages, key=lambda current: current.posted_at):
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        body = msg.body
        if is_preview_final(body):
            continue
        key = session_key(body)
        market = market_from_preview(body)
        date = body_date(body)
        if not key or not market or not date:
            continue
        if "Session Deals" not in body and "Total Reg" not in body:
            continue
        posted_date = msg.posted_at[:10]
        if "Session Deals" in body and date != posted_date:
            body_dt = datetime.fromisoformat(date)
            posted_dt = datetime.fromisoformat(posted_date)
            posted_hour = datetime.fromisoformat(msg.posted_at).hour
            if timedelta(0) < posted_dt - body_dt <= timedelta(days=1) and posted_hour >= 6:
                # Result posts are normally entered right after the session. This
                # handles a known Memphis copy/paste that retained yesterday's date.
                date = posted_date
        market = active_preview_market_display(market)
        market_key = normalize_market_name(market)
        latest_session_date = max(latest_session_date, date)
        latest_posted_at = max(latest_posted_at, msg.posted_at)
        reg = number_after(body, ("Total Reg",))
        attendance = number_after(body, ("Total Head Count", "Total Count"))
        sales = number_after(body, ("Session Deals",))
        row = None
        if reg is None and sales is not None:
            result_dt = datetime.fromisoformat(msg.posted_at)
            candidates = [
                candidate for candidate in sessions.values()
                if candidate.get("channel") == msg.channel
                and candidate.get("market_key") == market_key
                and candidate.get("date") == date
                and int(candidate.get("registered") or 0) > 0
                and int(candidate.get("sales") or 0) == 0
                and timedelta(0) <= result_dt - datetime.fromisoformat(str(candidate["posted_at"])) <= timedelta(hours=4)
            ]
            if candidates:
                row = max(candidates, key=lambda candidate: str(candidate["posted_at"]))
                # A late headcount may have been posted with the previous
                # session's label. Once the following result arrives, bind the
                # pending row to the result's actual day/session key.
                row["day"], row["session"] = key
        if row is None:
            row = sessions.setdefault((msg.channel, market_key, date, key[0], key[1]), {
                "channel": msg.channel,
                "market": market,
                "market_key": market_key,
                "day": key[0],
                "session": key[1],
                "date": date,
                "posted_at": msg.posted_at,
                "registered": 0,
                "attendance": 0,
                "sales": 0,
                # Headcount posts arrive before result posts. Track completion
                # explicitly so an in-progress session does not dilute the latest
                # Slack-posted route conversion denominator.
                "result_received": 0,
                "result_posted_at": "",
                "route_sales_pct": 0.0,
                "master_class_sales": -1,
                "master_class_speaker": "",
                "speaker_attribution_source": "",
                "total_futures": 0,
            })
        # Once a result has closed a session, do not let a later same-key
        # headcount post rewrite its denominator. Teams occasionally copy the
        # prior session label onto the next session's headcount (Grand Rapids
        # Day 1 on 2026-08-01 exposed this), which otherwise creates a false
        # route-conversion mismatch and blocks every downstream refresh.
        #
        # A closed row that still has no headcount is the opposite case: the
        # team posted the result before the headcount for the same session
        # (Little Rock Day 1 Session 2 on 2026-08-15 posted them 61 seconds
        # apart, result first). That headcount belongs to this row, so filling
        # it in is correct. Splitting it off would strand the session's deals
        # in a registered==0 row that the active-session filter drops, which
        # under-counts route deals and trips the fail-closed reconciliation.
        completed_session_locked = bool(
            reg is not None
            and int(row.get("registered") or 0) > 0
            and row.get("result_received")
            and row.get("result_posted_at")
            and msg.posted_at > str(row["result_posted_at"])
        )
        if completed_session_locked:
            # Preserve the completed row and hold this late headcount as a
            # pending session. The next result post is matched by chronology
            # and supplies the correct day/session label.
            row = {
                "channel": msg.channel,
                "market": market,
                "market_key": market_key,
                "day": key[0],
                "session": key[1],
                "date": date,
                "posted_at": msg.posted_at,
                "registered": 0,
                "attendance": 0,
                "sales": 0,
                "result_received": 0,
                "result_posted_at": "",
                "route_sales_pct": 0.0,
                "master_class_sales": -1,
                "master_class_speaker": "",
                "speaker_attribution_source": "",
                "total_futures": 0,
            }
            sessions[(msg.channel, market_key, date, key[0], key[1] + 1000)] = row
            completed_session_locked = False
        if not completed_session_locked:
            row["posted_at"] = max(str(row["posted_at"]), msg.posted_at)
            row["date"] = max(str(row["date"]), date)
        route_sales_match = re.search(r"Total\s+Route\s+Conversion\s*:\s*([0-9]+(?:\.[0-9]+)?)%", body, re.I)
        master_class_sales = cumulative_master_class(body)
        speaker_name, speaker_attribution_source = preview_session_speaker(
            msg.channel,
            market_key,
            date,
            key[0],
            key[1],
            master_class_speaker(body),
        )
        total_futures = number_after(body, ("Total Futures",))
        if reg is not None and not completed_session_locked:
            row["registered"] = reg
        if attendance is not None and not completed_session_locked:
            row["attendance"] = attendance
        if sales is not None:
            row["sales"] = sales
            row["result_received"] = 1
            row["result_posted_at"] = msg.posted_at
        if route_sales_match:
            row["route_sales_pct"] = float(route_sales_match.group(1))
        if master_class_sales is not None:
            row["master_class_sales"] = master_class_sales
            row["master_class_speaker"] = speaker_name or row.get("master_class_speaker") or ""
            row["speaker_attribution_source"] = speaker_attribution_source
            # Teams omit Total Futures when the cumulative value is zero.
            row["total_futures"] = total_futures or 0

    if not latest_session_date:
        return [], [], "", ""

    latest_dt = datetime.fromisoformat(latest_session_date)
    active_sessions = [
        row for row in sessions.values()
        # Live cards must reflect the current route window. A missing final report
        # must not leave an old market marked LIVE indefinitely. Preview routes
        # routinely run Saturday through Wednesday (4 calendar days), so a 3-day
        # cutoff drops Day 1 and falsely fails cumulative Master Class vs deals.
        if (latest_dt - datetime.fromisoformat(str(row["date"]))).days <= 7
        and int(row.get("registered") or 0) > 0
        and int(row.get("attendance") or 0) >= 0
    ]

    by_market: dict[tuple[str, str], list[dict[str, int | str | float]]] = {}
    for row in active_sessions:
        by_market.setdefault((str(row["channel"]), str(row["market_key"])), []).append(row)

    rendered: list[tuple[str, str]] = []
    session_rows: list[tuple[str, str, int, int, str]] = []
    for (channel, _market_key), market_rows in by_market.items():
        market_rows.sort(key=lambda row: (str(row["date"]), int(row["day"]), int(row["session"])))
        market = min((str(row["market"]) for row in market_rows), key=lambda value: (len(value), value))
        registered = sum(int(row.get("registered") or 0) for row in market_rows)
        attendance = sum(int(row.get("attendance") or 0) for row in market_rows)
        completed_rows = [row for row in market_rows if int(row.get("result_received") or 0) == 1]
        sales_attendance = sum(int(row.get("attendance") or 0) for row in completed_rows)
        pending_result_sessions = len(market_rows) - len(completed_rows)
        route_deals = sum(int(row.get("sales") or 0) for row in market_rows)
        if not registered:
            continue
        latest_row = market_rows[-1]
        team = PREVIEW_CHANNELS[channel]
        for row in market_rows:
            session_speaker = str(row.get("master_class_speaker") or team.removeprefix("Team ").strip())
            session_rows.append((
                str(row["date"]),
                f"{market}-{int(row['day'])}-{int(row['session'])}",
                int(row["day"]),
                int(row["session"]),
                (
                    f"  {{ market: '{ts_literal(market)}', team: '{team}', "
                    f"session: 'Day {int(row['day'])} Session {int(row['session'])}', "
                    f"speaker: '{ts_literal(session_speaker)}', "
                    f"reg: {int(row.get('registered') or 0)}, "
                    f"attendance: {int(row.get('attendance') or 0)}, "
                    f"sales: {int(row.get('sales') or 0)} }}"
                ),
            ))
        start_date = min(str(row["date"]) for row in market_rows)
        latest_date = max(str(row["date"]) for row in market_rows)
        latest_post = max(str(row["posted_at"]) for row in market_rows)
        sessions_seen = len({(str(row["date"]), int(row["day"]), int(row["session"])) for row in market_rows})
        sessions_completed = len({
            (str(row["date"]), int(row["day"]), int(row["session"]))
            for row in completed_rows
        })
        scheduled_total = schedule_total_for_market(schedule_records, market, start_date)
        total_sessions = max(6, sessions_seen, scheduled_total)
        is_finalized = _market_key in finalized_markets
        if is_finalized:
            sessions_completed = total_sessions
            final_reg, final_headcount, final_deals = final_totals.get(_market_key, (registered, attendance, route_deals))
            registered, attendance, route_deals = final_reg, final_headcount, final_deals
        if is_finalized:
            # Final-route markets belong in the completed cards below, never in LIVE.
            continue
        posted_route_rows = [
            row for row in market_rows if float(row.get("route_sales_pct") or 0.0) > 0
        ]
        latest_posted_route_row = max(posted_route_rows, key=lambda row: str(row["posted_at"])) if posted_route_rows else None
        latest_posted_route_rate = (
            float(latest_posted_route_row.get("route_sales_pct") or 0.0)
            if latest_posted_route_row else None
        )
        posted_route_rate_note = ""
        if latest_posted_route_row and len(completed_rows) > 1:
            latest_session_attendance = int(latest_posted_route_row.get("attendance") or 0)
            latest_session_sales = int(latest_posted_route_row.get("sales") or 0)
            latest_session_rate = (
                latest_session_sales / latest_session_attendance * 100
                if latest_session_attendance else None
            )
            if latest_posted_route_rate is not None and latest_session_rate is not None and abs(latest_posted_route_rate - latest_session_rate) <= 0.6:
                # Some live result posts duplicate the current-session
                # conversion under the label "Total Route Conversion". Once a
                # route has multiple completed sessions, that field is not an
                # independent whole-route assertion. Keep the fail-closed gate
                # for genuine cumulative conflicts, but do not compare the
                # calculated whole-route rate against a mislabeled session rate.
                posted_route_rate_note = (
                    f" Latest post labels {latest_posted_route_rate:.1f}% as Total Route Conversion, "
                    f"but it matches the current-session conversion ({latest_session_sales}/"
                    f"{latest_session_attendance}); treated as a duplicated session rate. "
                    f"Dashboard whole-route conversion is calculated across all {sales_attendance} "
                    f"completed-session attendees."
                )
                latest_posted_route_rate = None
        posted_master_class = [
            (
                str(row["posted_at"]),
                int(row.get("master_class_sales") or 0),
                str(row.get("master_class_speaker") or ""),
            )
            for row in market_rows if int(row.get("master_class_sales") or -1) >= 0
        ]
        latest_master_class = max(posted_master_class, key=lambda item: item[0]) if posted_master_class else None
        sales = latest_master_class[1] if latest_master_class else route_deals
        futures = route_deals - sales
        if futures < 0:
            raise SystemExit(
                f"Preview route reconciliation failed for {market}: cumulative Master Class sold "
                f"{sales} exceeds {route_deals} summed route deals"
            )
        if latest_posted_route_rate is not None and sales_attendance:
            calculated_route_rate = route_deals / sales_attendance * 100
            if abs(calculated_route_rate - latest_posted_route_rate) > 0.6:
                raise SystemExit(
                    f"Preview route reconciliation failed for {market}: calculated route conversion "
                    f"{calculated_route_rate:.1f}% from {sales_attendance} completed-session attendees "
                    f"vs latest posted {latest_posted_route_rate:.1f}%"
                )
        speaker = (
            latest_master_class[2]
            if latest_master_class and latest_master_class[2]
            else team.removeprefix("Team ").strip()
        )
        speaker_source = (
            "latest Master Class result"
            if latest_master_class and latest_master_class[2]
            else "team-name fallback"
        )
        team_label = f"{team_speaker_label(team, speaker)} / #{channel}"
        source_note = (
            f"Live preview session posts from #{channel}; route start {start_date}; latest source {latest_post}; "
            f"latest session Day {latest_row['day']} Session {latest_row['session']}; "
            f"whole-market totals: {registered} reg, {attendance} attendance, {sales} Master Class sold, "
            f"{route_deals} route deals including {futures} futures."
            + (
                f" Dashboard route conversion is provisional across all {attendance} current cutoff attendees while "
                f"{pending_result_sessions} session result is pending; the latest Slack-posted rate uses "
                f"{sales_attendance} attendees from {sessions_completed} completed result posts."
                if pending_result_sessions
                else f" Route conversion uses {sales_attendance} cutoff attendees from all {sessions_completed} completed result posts."
            )
            + (f" Latest Slack-posted Total Route Conversion: {latest_posted_route_rate:.1f}%." if latest_posted_route_rate is not None else "")
            + posted_route_rate_note
            + f" Speaker attribution uses the {speaker_source}: {speaker}."
            + (" FINAL route report received for this market — route complete; totals reflect the final route report." if is_finalized else "")
        )
        rendered.append((
            latest_post,
            "  {\n"
            f"    market: '{ts_literal(market)}',\n"
            f"    team: '{ts_literal(team_label)}',\n"
            f"    sessionsCompleted: {sessions_completed},\n"
            f"    totalSessions: {total_sessions},\n"
            f"    registered: {registered},\n"
            f"    attendedCutoff: {attendance},\n"
            f"    sales: {sales},\n"
            f"    routeDeals: {route_deals},\n"
            f"    futures: {futures},\n"
            f"    previewShowRate: {percent_rate(attendance, registered)},\n"
            f"    salesRate: {percent_rate(route_deals, attendance) if pending_result_sessions else (f'{latest_posted_route_rate} / 100' if latest_posted_route_rate is not None else percent_rate(route_deals, attendance))},\n"
            "    status: 'green',\n"
            "    sourceState: 'active_session',\n"
            f"    startDate: '{start_date}',\n"
            f"    latestSessionDate: '{latest_date}',\n"
            f"    sourcePostedAt: '{latest_post}',\n"
            f"    sourceNote: '{ts_literal(source_note)}'\n"
            "  }"
        ))

    market_order = {"Seattle": 0, "Columbus": 1, "Orlando, FL": 2}
    rendered.sort(
        key=lambda row: (
            market_order.get(row[1].split("market: '", 1)[1].split("'", 1)[0], 99),
            row[0],
        )
    )
    session_rows.sort(key=lambda row: (row[0], row[1], row[2], row[3]))
    return [row for _, row in rendered], [row for *_sort, row in session_rows], latest_posted_at, latest_session_date


def select_recent_final_candidates(
    candidates: list[tuple[str, str, str, str, str]],
    active_route_starts: list[str],
) -> list[tuple[str, str, str, str, str]]:
    """Keep current-run finals plus only the immediately preceding run.

    Preview cards are an operating view, not an archive. When a route is live,
    current-run finals are identified by their route start and the previous run
    is the most recent final-post cohort before it. Between routes, retain the
    two most recent final-post cohorts. A one-day cohort window tolerates a
    team posting its final after midnight without reviving older markets.
    """
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda row: row[0], reverse=True)

    def latest_cohorts(pool: list[tuple[str, str, str, str, str]], count: int) -> list[tuple[str, str, str, str, str]]:
        anchors: list[date] = []
        selected: list[tuple[str, str, str, str, str]] = []
        for candidate in pool:
            posted_date = datetime.fromisoformat(candidate[0]).date()
            cohort = next((anchor for anchor in anchors if abs((anchor - posted_date).days) <= 1), None)
            if cohort is None:
                if len(anchors) >= count:
                    continue
                anchors.append(posted_date)
            selected.append(candidate)
        return selected

    if not active_route_starts:
        return latest_cohorts(ordered, 2)

    active_floor = min(datetime.fromisoformat(value).date() for value in active_route_starts) - timedelta(days=2)
    current_run = [row for row in ordered if datetime.fromisoformat(row[3]).date() >= active_floor]
    previous_pool = [row for row in ordered if datetime.fromisoformat(row[3]).date() < active_floor]
    previous_run = latest_cohorts(previous_pool, 1)
    selected_ids = {id(row) for row in current_run + previous_run}
    return [row for row in ordered if id(row) in selected_ids]


def parse_preview(messages: list[SlackMessage], schedule_records: list[dict] | None = None) -> tuple[list[str], str]:
    active_rows, _active_session_rows, active_at, _active_data_date = parse_active_preview_rows(messages, schedule_records)
    rows: list[str] = [*active_rows]
    latest = active_at
    active_market_keys = {
        normalize_market_name(current.split("market: '", 1)[1].split("'", 1)[0])
        for current in active_rows if "market: '" in current
    }
    active_route_starts = [
        match.group(1)
        for current in active_rows
        if (match := re.search(r"startDate: '(\d{4}-\d{2}-\d{2})'", current))
    ]

    # Speaker attribution comes from the latest cumulative Master Class line
    # for the same market/channel. The final post itself often omits speaker.
    speaker_sources: dict[tuple[str, str], tuple[str, str, str]] = {}
    route_date_sources: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for msg in messages:
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        market = market_from_preview(msg.body)
        if not market:
            continue
        market_key = normalize_market_name(active_preview_market_display(market))
        key = (msg.channel, market_key)
        session_date = body_date(msg.body)
        if session_date:
            route_date_sources.setdefault(key, []).append((msg.posted_at, session_date))
        reported_speaker = master_class_speaker(msg.body)
        parsed_session = session_key(msg.body)
        if parsed_session and session_date:
            speaker, attribution_source = preview_session_speaker(
                msg.channel,
                market_key,
                session_date,
                parsed_session[0],
                parsed_session[1],
                reported_speaker,
            )
        else:
            speaker = reported_speaker or ""
            attribution_source = "Slack Master Class label" if speaker else "team-name fallback"
        if not speaker:
            continue
        current = speaker_sources.get(key)
        if current is None or msg.posted_at > current[0]:
            speaker_sources[key] = (msg.posted_at, speaker, attribution_source)

    final_candidates: list[tuple[str, str, str, str, str]] = []
    seen_markets: set[str] = set()
    for msg in sorted(messages, key=lambda current: current.posted_at, reverse=True):
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        body = msg.body
        if not is_preview_final(body):
            continue
        market = market_from_preview(body)
        reg = number_after(body, ("Total Reg",))
        headcount = number_after(body, ("Total Head Count",))
        late = number_after(body, ("Total Late Arrivals",)) or 0
        attendees = number_after(body, ("Total Attendees",))
        deals = number_after(body, ("Total Deals",))
        if not market or reg is None or headcount is None or deals is None:
            continue
        futures = preview_final_futures(body)
        if futures > deals:
            raise SystemExit(f"Preview final futures {futures} exceed total route deals {deals} for {market}; refusing to ship")
        master_class_sold = deals - futures
        market_key = normalize_market_name(active_preview_market_display(market))
        if market_key in active_market_keys:
            continue
        if market_key in seen_markets:
            continue
        seen_markets.add(market_key)
        attended = attendees or (headcount + late)
        team = preview_team_from_final(body, msg.channel)
        speaker_source = speaker_sources.get((msg.channel, market_key), ("", "", "team-name fallback"))
        speaker = speaker_source[1] or team.removeprefix("Team ").strip()
        attribution_note = (
            " Team Millar's final two Chicago sessions (Day 5 Sessions 1–2) are attributed to Lura per Troy's confirmed floor-speaker correction; Slack's cumulative Master Class label remained Jay."
            if speaker_source[2].startswith("Troy-confirmed")
            else ""
        )
        team_label = team_speaker_label(team, speaker)
        final_date = datetime.fromisoformat(msg.posted_at).date()
        route_dates = [
            session_date
            for source_posted_at, session_date in route_date_sources.get((msg.channel, market_key), [])
            if source_posted_at <= msg.posted_at
            and 0 <= (final_date - datetime.fromisoformat(session_date).date()).days <= 10
        ]
        route_start_date = min(route_dates) if route_dates else msg.posted_at[:10]
        latest = max(latest, msg.posted_at)
        rendered = (
            "  {\n"
            f"    market: '{ts_literal(market)}',\n"
            f"    team: '{ts_literal(team_label)} / #{msg.channel}',\n"
            "    sessionsCompleted: null,\n"
            "    totalSessions: null,\n"
            f"    registered: {reg},\n"
            f"    attendedCutoff: {headcount},\n"
            f"    sales: {master_class_sold},\n"
            f"    routeDeals: {deals},\n"
            f"    previewShowRate: {percent_rate(headcount, reg)},\n"
            f"    salesRate: {percent_rate(deals, headcount)},\n"
            "    status: 'yellow',\n"
            "    sourceState: 'final_route_totals',\n"
            f"    startDate: '{route_start_date}',\n"
            f"    latestSessionDate: '{msg.posted_at[:10]}',\n"
            f"    sourcePostedAt: '{msg.posted_at}',\n"
            f"    sourceNote: 'Final route report from #{msg.channel}, labeled {ts_literal(team)}, at {msg.posted_at}: {reg} reg, {headcount} cutoff headcount, {attended} attendees including late arrivals, {deals} route deals ({master_class_sold} Master Class sold + {futures} futures).{ts_literal(attribution_note)}'\n"
            "  }"
        )
        final_candidates.append((msg.posted_at, msg.channel, market_key, route_start_date, rendered))

    # Preview market cards are intentionally a two-run operating view: the
    # current run (LIVE plus any markets that already finalized) and the one
    # immediately preceding run. Older markets remain available in team history,
    # but must not linger beside current routes.
    selected_finals = select_recent_final_candidates(final_candidates, active_route_starts)
    rows.extend(rendered for _posted_at, _channel, _market_key, _route_start, rendered in selected_finals)

    represented_market_keys = active_market_keys | {candidate[2] for candidate in selected_finals}
    pending_rows = parse_pending_preview_markets(messages, represented_market_keys, schedule_records)
    # Put upcoming/pre-event markets first so the next routes are visible before
    # the first Slack floor post, while keeping LIVE and recent FINAL cards below.
    rows = [*pending_rows, *rows]

    # A live route can transition market-by-market: once a FINAL ROUTE NUMBERS
    # post arrives that market moves from active_rows into final-route rows.
    # Gate the combined current route population, not active-only rows, or the
    # hourly refresh falsely fails as soon as the first city finishes.
    if len(rows) < 3:
        raise SystemExit(f"Parsed only {len(rows)} preview final market(s); refusing to ship partial preview state")
    return rows, latest


def market_from_me(body: str) -> str | None:
    # Workflow-bot Event Stats finals normally put the market in a delimited
    # ``Market: ... |`` field. Some teams prefix that field with a compact date
    # range and suffix it with the ME team (for example
    # ``7.24-26.26 Long Island ME Tony``), which the older letters-only regex
    # rejected even though the rest of the final was valid.
    market_field = re.search(r"\bMarket:\s*(.*?)(?=\s*\||$)", body, re.I)
    if market_field:
        market = re.sub(r"[*_`]", "", market_field.group(1))
        market = re.sub(r"\s+", " ", market).strip(" ,")
        market = re.sub(r"^\d[\d./-]*\s+", "", market)
        market = re.sub(r"\s+ME(?:\s+(?:Tony|Shaw|Drecksel|Drexel|Nick))?\s*$", "", market, flags=re.I)
        market = market.strip(" ,")
        if market and re.search(r"[A-Za-z]", market):
            return market

    # Older human-entered finals can start with ``City. ST Venue ...`` rather
    # than a workflow-bot ``Market:`` field. Capture only the leading city/state
    # pair; venue and date text after the state are not part of the market key.
    heading_market = re.search(
        r"([A-Z][A-Za-z .'-]*?)[.,]\s*([A-Z]{2})\b",
        body,
    )
    if heading_market:
        city = re.sub(r"\s+", " ", heading_market.group(1)).strip(" .,\t")
        return f"{city}, {heading_market.group(2).upper()}"

    patterns = [
        r"UPDATED #'?s[:!]?\s*\|\s*([A-Za-z][A-Za-z .,/-]+?)\s*\|",
        r"([A-Za-z][A-Za-z .,/-]+?)\s+Workshop",
        r"([A-Za-z0-9][A-Za-z0-9# .,/-]+?)\s+Middle End Event",
        r"^\s*([A-Za-z][A-Za-z .,/-]+?)\s*\|",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.I)
        if match:
            market = match.group(1).strip()
            market = re.sub(r"\s+", " ", market)
            return market.rstrip(" ,")
    return None


def parse_me_abc(body: str) -> str | None:
    """Extract the A/B/C buyer mix from Slack's ME Event Stats final."""
    # Slack export text preserves mrkdwn asterisks around every field label.
    # Normalize those markers before slicing the buyer-mix block; the previous
    # regex expected bare ``WS Buyers Sold: A:`` text and returned null for every
    # current final even though the A/B/C values were present in Slack.
    cleaned = body.replace("*", "")
    match = re.search(
        r"WS Buyers Sold:\s*(.*?)(?=\|\s*(?:Legacy Pro|Legacy|Scale Pro|Scale|Launch|Starters|Copper Rock|Avvance|JumpStart|PIF Deals):|$)",
        cleaned,
        re.I,
    )
    if not match:
        return None

    section = match.group(1)
    parts: list[str] = []
    for grade in ("A", "B", "C"):
        grade_match = re.search(
            rf"(?:^|\|)\s*{grade}:\s*(.*?)(?=\s*\|\s*[ABC]:|\s*$)",
            section,
            re.I,
        )
        if not grade_match:
            continue
        value = grade_match.group(1).strip(" |")
        ratio_match = re.fullmatch(r"(\d+)\s*/\s*(\d+)\s*(?:=\s*)?(\d+(?:\.\d+)?)\s*%", value)
        if ratio_match:
            left, right, percent = ratio_match.groups()
            left_count, right_count = int(left), int(right)
            rate = float(percent) / 100
            if right_count and abs((left_count / right_count) - rate) <= 0.02:
                sold, buyers = left_count, right_count
            elif left_count and abs((right_count / left_count) - rate) <= 0.02:
                sold, buyers = right_count, left_count
            else:
                # The ratio still carries source-supported sold/buyer counts,
                # but the posted percentage does not reconcile arithmetically.
                # Preserve all three source values with explicit semantics and
                # an audit note instead of dropping the component downstream.
                parts.append(f"{grade}: {right_count} buyers · {left_count} sold ({percent}% as reported)")
                continue
            buyer_label = "buyer" if buyers == 1 else "buyers"
            parts.append(f"{grade}: {buyers} {buyer_label} · {sold} sold ({percent}%)")
            continue
        count_only_match = re.fullmatch(r"(\d+)", value)
        if count_only_match:
            # Under WS Buyers Sold, an unqualified number is a sold count.
            # Do not invent buyer counts or a percentage for count-only posts.
            parts.append(f"{grade}: {count_only_match.group(1)} sold")
            continue
        value = re.sub(r"\s*=\s*", " = ", value)
        value = re.sub(r"\s*%", "%", value)
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            parts.append(f"{grade}: {value}")
    return " · ".join(parts) if parts else None


def parse_me(messages: list[SlackMessage]) -> tuple[list[str], list[str], str]:
    current_rows: list[str] = []
    summary_rows: list[str] = []
    parsed_rows: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    latest = ""
    preview_sources = preview_sold_sources(messages)
    confirmation_sources = me_confirmation_sources(messages)
    corrected_me_summary = {
        "dallas": {
            "sold": 60,
            "period": "Two weeks prior",
            "source": "Slack final preview route report: Dallas Team Vogel final shows 60 preview buying units sold.",
        },
        "charlotte": {
            "sold": 50,
            "period": "Two weeks prior",
            "source": "Canonical preview sheet row 240: 50 preview buying units sold.",
        },
        "fort myers": {
            "sold": 58,
            "period": "Two weeks prior",
            "source": "Canonical preview sheet row 239: 58 preview buying units sold.",
        },
        "tampa": {
            "sold": 53,
            "period": "Two weeks prior",
            "source": "Canonical preview sheet row 237: 53 preview buying units sold.",
        },
        "orlando": {
            "sold": 40,
            "period": "Last week",
            "source": "Canonical preview sheet row 245: 40 preview buying units sold.",
        },
        "columbus": {
            "sold": 41,
            "period": "Last week",
            "source": "Canonical preview sheet row 246: 41 preview buying units sold.",
        },
        "seattle": {
            "sold": 42,
            "period": "Last week",
            "source": "Canonical preview sheet row 247: 42 preview buying units sold.",
        },
    }
    for msg in messages:
        if msg.channel not in ME_CHANNELS:
            continue
        body = msg.body
        if "Total Sales" not in body or "Written" not in body or "Collected" not in body:
            continue
        market = market_from_me(body)
        bu = number_after(body, ("BU's", "BU’s", "BUs", "BU"))
        sales = number_after(body, ("Total Sales",))
        written = money_after(body, ("Written",))
        collected = money_after(body, ("Collected",))
        if not market or bu is None or sales is None or written is None or collected is None:
            raise SystemExit(f"Could not parse ME final in #{msg.channel} ts={msg.ts}")
        key = f"{market.lower()}::{msg.channel}"
        if key in seen:
            continue
        seen.add(key)
        latest = max(latest, msg.posted_at)
        team = team_speaker_label(ME_CHANNELS[msg.channel])
        abc = parse_me_abc(body)
        note = (
            f"Final workshop post from #{msg.channel} at {msg.posted_at}: "
            f"{bu} BU, {sales} total sales, ${written:,} written, ${collected:,} collected."
        )
        current_row = (
            "  {\n"
            f"    market: '{ts_literal(market)}', team: '{team}', eventDate: '{msg.posted_at[:10]}', buyingUnits: {bu},\n"
            f"    soldClosed: {sales}, showed: {bu}, totalWritten: {written}, totalCollected: {collected},\n"
            f"    abcBreakdown: {repr(abc) if abc else 'null'}, notes: '{ts_literal(note)}'\n"
            "  }"
        )
        # Executive ME pipeline shows workshop BU / preview buyers sold. Prefer
        # the current team's pre-workshop confirmation update, then a matching
        # preview final, and retain older certified corrections as fallbacks.
        normalized_market = normalize_market_name(market)
        correction = corrected_me_summary.get(normalized_market)
        if correction:
            preview_sold = int(correction["sold"])
            preview_note = f"{correction['source']} Final workshop post from #{msg.channel} shows {bu} BU attended and {sales} ME sales."
            period = str(correction["period"])
        else:
            confirmation = confirmation_sources.get((normalized_market, msg.channel))
            preview_source = preview_sources.get(normalized_market)
            live_source = confirmation if confirmation and int(confirmation.get("sold") or 0) else preview_source
            if live_source:
                preview_sold = int(live_source["sold"])
                source_channel = str(live_source["channel"])
                source_posted = str(live_source["posted_at"])
                preview_note = (
                    f"Live preview-sold source from #{source_channel} at {source_posted}: {preview_sold} buyers sold. "
                    f"Final workshop post from #{msg.channel} shows {bu} BU attended and {sales} ME sales."
                )
                period = "Last week"
            else:
                preview_sold = 0
                preview_note = ""
                period = "Last week"
        if preview_sold and bu <= preview_sold:
            summary_row = (
                f"  {{ label: 'Final ME', period: '{period}', market: '{ts_literal(market)}', team: '{team}', sold: {preview_sold}, attended: {bu}, showRate: {bu} / {preview_sold}, startDate: '{msg.posted_at[:10]}', workshopSales: {sales}, sourceNote: '{ts_literal(preview_note)}' }}"
            )
            parsed_rows.append((msg.posted_at, msg.channel, current_row, summary_row))
        else:
            parsed_rows.append((msg.posted_at, msg.channel, current_row, ""))
    if len(parsed_rows) < 4:
        raise SystemExit(f"Parsed only {len(parsed_rows)} current ME/workshop final(s); refusing to ship partial ME state")
    parsed_rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
    current_rows = [row[2] for row in parsed_rows]
    summary_rows = [row[3] for row in parsed_rows if row[3]]
    return current_rows[:8], summary_rows[:6], latest


def render_inside_sales_adapters(src: Path, fetched_at: str) -> tuple[str, str, str, str, str] | None:
    inside_path = src / "../data/inside_replit_latest.json"
    collections_path = src / "../data/collections_replit_latest.json"
    if not inside_path.exists() or not collections_path.exists():
        return None
    inside = json.loads(inside_path.read_text(encoding="utf-8"))
    collections = json.loads(collections_path.read_text(encoding="utf-8"))
    groups = inside.get("groups") or []
    if not groups:
        raise SystemExit("Inside Sales Replit source returned no groups; refusing to ship stale adapter state")
    source_note = f"Lindsey/Replit › TLWB Inside Sales DPL › groups · fetched {inside.get('lastUpdated') or fetched_at}"
    category_totals: dict[str, dict[str, float]] = {}
    for group in groups:
        for item in group.get("byLeadType") or []:
            source = str(item.get("leadType") or "Unknown")
            bucket = category_totals.setdefault(source, {"leads": 0.0, "revenue": 0.0})
            bucket["leads"] += float(item.get("leads") or 0)
            bucket["revenue"] += float(item.get("revenue") or 0)
    total_revenue = sum(bucket["revenue"] for bucket in category_totals.values())
    category_rows = []
    for source, bucket in sorted(category_totals.items(), key=lambda item: (-item[1]["revenue"], item[0].lower())):
        leads = int(bucket["leads"])
        revenue = bucket["revenue"]
        dpl = revenue / leads if leads else 0
        share = revenue / total_revenue if total_revenue else 0
        category_rows.append(
            f"  {{ source: '{ts_literal(source)}', leads: {leads}, revenue: {numeric_literal(revenue)}, dpl: {numeric_literal(round(dpl))}, revenueShare: {numeric_literal(share)} }}"
        )
    rep_rows = []
    for group in sorted(groups, key=lambda item: (-float(item.get("ytdDpl") or 0), str(item.get("group") or "").lower())):
        rep = str(group.get("group") or "Unknown")
        leads = int(group.get("totalLeads") or 0)
        revenue = float(group.get("totalRevenue") or 0)
        dpl = float(group.get("ytdDpl") or 0)
        rep_rows.append(
            f"  {{ rep: '{ts_literal(rep)}', leads: {leads}, revenue: {numeric_literal(revenue)}, dpl: {numeric_literal(dpl)}, collected: null, collectedDpl: null, source: '{ts_literal(source_note)}' }}"
        )
    ytd = {str(row.get("speaker")): row for row in collections.get("ytd") or []}
    past6 = {str(row.get("speaker")): row for row in collections.get("past6Weeks") or []}
    past10 = {str(row.get("speaker")): row for row in collections.get("past10Weeks") or []}
    pending = {str(row.get("speaker")): row for row in collections.get("ytdPending") or []}
    collection_rows = []
    for speaker, row in ytd.items():
        collection_rows.append(
            f"  {{ speaker: '{ts_literal(speaker)}', amountIntoCollections: {numeric_literal(row.get('amountIntoCollections'))}, collectionsOut: {numeric_literal(row.get('weeklyCollected'))}, pendingOutstanding: {numeric_literal((pending.get(speaker) or {}).get('amount'))}, sixWeekCollected: {numeric_literal((past6.get(speaker) or {}).get('weeklyCollected'))}, tenWeekCollected: {numeric_literal((past10.get(speaker) or {}).get('weeklyCollected'))}, dplOrCollectionMetric: 'YTD collections performance · fetched {ts_literal(fetched_at)}' }}"
        )
    return (
        "export const insideSalesSourceCategories: InsideSalesSourceRow[] = [\n" + ",\n".join(category_rows) + "\n];",
        "export const insideSalesRepRows: InsideSalesRepRow[] = [\n" + ",\n".join(rep_rows) + "\n];",
        "export const speakerCollectionRows: SpeakerCollectionRow[] = [\n" + ",\n".join(collection_rows) + "\n];",
        str(inside.get("lastUpdated") or fetched_at),
        fetched_at,
    )


def render_source(key: str, name: str, url: str, fetched_at: str, role: str, caveat: str) -> str:
    return (
        "  {\n"
        f"    sourceKey: '{key}',\n"
        f"    sourceName: '{name}',\n"
        f"    sourceUrl: '{url}',\n"
        f"    fetchedAt: '{fetched_at}',\n"
        "    trustLevel: 'operational',\n"
        "    sampleData: false,\n"
        f"    sourceRole: '{role}',\n"
        f"    caveat: '{ts_literal(caveat)}'\n"
        "  }"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slack", required=True, type=Path)
    parser.add_argument("--src", required=True, type=Path)
    args = parser.parse_args()

    messages = parse_messages(args.slack.read_text(encoding="utf-8", errors="replace"))
    schedule_path = args.src / "data" / "schedule.json"
    schedule_records = []
    if schedule_path.exists():
        schedule_records = json.loads(schedule_path.read_text(encoding="utf-8")).get("records") or []
    fetched_at = latest_fetched_at(messages)
    marketing_rows, marketing_at = parse_marketing(messages)
    upcoming_pipeline_rows = parse_upcoming_pipeline(messages, args.src)
    expo, expo_at = parse_expo(messages)
    preview_rows, preview_at = parse_preview(messages, schedule_records)
    _active_rows, active_session_rows, _active_at, _active_data_date = parse_active_preview_rows(messages, schedule_records)
    me_current_rows, me_summary_rows, me_at = parse_me(messages)
    inside_sales_adapters = render_inside_sales_adapters(args.src, fetched_at)

    exec_path = args.src / "src/data/executiveAdapters.ts"
    exec_text = exec_path.read_text(encoding="utf-8")
    source_key_suffix = fetched_at[:10].replace("-", "_")
    exec_sources = "export const executiveSources: SourceMeta[] = [\n" + ",\n".join(
        [
            render_source(
                f"slack_expo_current_{source_key_suffix}",
                "Slack #expo — current Investor Expo count",
                f"slack://channel/expo/posts/{expo_at}",
                fetched_at,
                "expo_strip_current_count",
                f"{expo['label']} current count parsed from live #expo: {expo['bus']} BU, {expo['guests']} guests, total {expo['total']}.",
            ),
            render_source(
                f"slack_active_preview_{source_key_suffix}",
                "Slack preview team channels — latest final route reports",
                "slack://channels/teamwayne,teamdent,teamwyman,teamvogel,teammillar/latest-final-route-reports",
                fetched_at,
                "active_preview_slack_export",
                "Latest final route reports are parsed from visible preview team channels. Cron fails if fewer than three final market reports parse.",
            ),
            render_source(
                f"slack_eventstats_active_marketing_{source_key_suffix}",
                "Slack #eventstats — active marketing posts",
                "slack://channel/eventstats/latest-active-workshop-posts",
                fetched_at,
                "active_marketing_eventstats_export",
                "Active marketing cards are rebuilt from the latest unique #eventstats workshop posts before deploy.",
            ),
            render_source(
                f"slack_me_finals_{source_key_suffix}",
                "Slack ME team channels — current workshop finals",
                "slack://channels/teamtony,teamshaw,teamdrecksel,teamnick/latest-workshop-finals",
                fetched_at,
                "middle_end_show_rate_slack_export",
                "Current Workshop/ME rows are rebuilt from latest visible final workshop posts before deploy.",
            ),
        ]
    ) + "\n];"

    exec_text = replace_block(exec_text, "export const executiveSources: SourceMeta[] = [", "];", exec_sources)
    exec_text = replace_block(exec_text, "export const expoCounts: ExpoCount[] = [", "];", "export const expoCounts: ExpoCount[] = [\n" + ",\n".join(
        [
            f"  {{ label: 'BU', value: {numeric_literal(expo['bus'])}, delta: null }}",
            f"  {{ label: 'Guests', value: {numeric_literal(expo['guests'])}, delta: null }}",
            f"  {{ label: 'UTL', value: {numeric_literal(expo['utl'])}, delta: null }}",
            f"  {{ label: 'TLWB', value: {numeric_literal(expo['tlwb'])}, delta: null }}",
            f"  {{ label: 'KeySpire', value: {numeric_literal(expo['keyspire'])}, delta: null }}",
            f"  {{ label: 'Total', value: {numeric_literal(expo['total'])}, delta: null }}",
        ]
    ) + "\n];")
    exec_text = replace_block(exec_text, "export const activePreviewMarkets: ActivePreviewMarket[] = [", "];", "export const activePreviewMarkets: ActivePreviewMarket[] = [\n" + ",\n".join(preview_rows) + "\n];")
    exec_text = replace_block(exec_text, "export const activeMarketingMarkets: ActiveMarketingMarket[] = [", "];", "export const activeMarketingMarkets: ActiveMarketingMarket[] = [\n" + ",\n".join(marketing_rows) + "\n];")
    exec_text = replace_block(exec_text, "export const middleEndSummary: MiddleEndSummary[] = [", "];", "export const middleEndSummary: MiddleEndSummary[] = [\n" + ",\n".join(me_summary_rows) + "\n];")
    exec_text = replace_block(exec_text, "export const upcomingMePipeline: UpcomingMePipelineMarket[] = [", "];", "export const upcomingMePipeline: UpcomingMePipelineMarket[] = [\n" + ",\n".join(upcoming_pipeline_rows) + "\n];")
    exec_path.write_text(exec_text, encoding="utf-8")

    page_path = args.src / "src/data/tlwbPageAdapters.ts"
    page_text = page_path.read_text(encoding="utf-8")
    page_text = replace_block(page_text, "export const previewSessions: PreviewSessionRow[] = [", "];", "export const previewSessions: PreviewSessionRow[] = [\n" + ",\n".join(active_session_rows) + "\n];")
    page_text = replace_block(page_text, "export const currentMiddleEndWorkshops: MiddleEndCurrentWorkshop[] = [", "];", "export const currentMiddleEndWorkshops: MiddleEndCurrentWorkshop[] = [\n" + ",\n".join(me_current_rows) + "\n];")
    if inside_sales_adapters:
        inside_source_block, inside_rep_block, collections_block, inside_updated_at, collections_fetched_at = inside_sales_adapters
        page_text = replace_block(page_text, "export const insideSalesSourceCategories: InsideSalesSourceRow[] = [", "];", inside_source_block)
        page_text = replace_block(page_text, "export const insideSalesRepRows: InsideSalesRepRow[] = [", "];", inside_rep_block)
        page_text = replace_block(page_text, "export const speakerCollectionRows: SpeakerCollectionRow[] = [", "];", collections_block)
        source_meta = (
            f"export const insideSalesSourceUpdatedAt = '{ts_literal(inside_updated_at)}';\n"
            f"export const collectionsSourceFetchedAt = '{ts_literal(collections_fetched_at)}';"
        )
        if "export const insideSalesSourceUpdatedAt =" in page_text:
            page_text = re.sub(r"export const insideSalesSourceUpdatedAt = .*?;\nexport const collectionsSourceFetchedAt = .*?;", source_meta, page_text, count=1)
        else:
            page_text = page_text.replace("export type MarketingHistoryChannel = {", source_meta + "\n\nexport type MarketingHistoryChannel = {", 1)
    page_path.write_text(page_text, encoding="utf-8")

    expo_path = args.src / "src/data/expoStrip.ts"
    expo_text = expo_path.read_text(encoding="utf-8")
    expo_text = re.sub(r"status: 'next-count-needed';", "status: 'next-count-needed' | 'current';", expo_text)
    expo_text = re.sub(r"sourceMode: 'post-event-reset';", "sourceMode: 'post-event-reset' | 'slack-count';", expo_text)
    expo_text = re.sub(
        r"export const expoStrip: ExpoStrip = \{.*?\n\};",
        "export const expoStrip: ExpoStrip = {\n"
        f"  bus: {numeric_literal(expo['bus'])},\n"
        f"  guests: {numeric_literal(expo['guests'])},\n"
        f"  utl: {numeric_literal(expo['utl'])},\n"
        f"  tlwb: {numeric_literal(expo['tlwb'])},\n"
        f"  keyspire: {numeric_literal(expo['keyspire'])},\n"
        f"  total: {numeric_literal(expo['total'])},\n"
        "  status: 'current',\n"
        f"  label: '{ts_literal(expo['label'])}',\n"
        "  sourceMode: 'slack-count',\n"
        f"  sourcePostedAt: '{expo_at}',\n"
        f"  lastFetchedAt: '{fetched_at}',\n"
        "  source: {\n"
        f"    sourceKey: 'slack_expo_current_{source_key_suffix}',\n"
        "    sourceName: 'Slack #expo — current Investor Expo count',\n"
        f"    sourceUrl: 'slack://channel/expo/posts/{expo_at}',\n"
        f"    fetchedAt: '{fetched_at}',\n"
        "    trustLevel: 'operational',\n"
        "    sampleData: false,\n"
        "    sourceRole: 'expo_strip_current_count',\n"
        f"    caveat: '{ts_literal(expo['label'])} count parsed from live #expo at {expo_at}.'\n"
        "  }\n"
        "};",
        expo_text,
        flags=re.S,
    )
    expo_path.write_text(expo_text, encoding="utf-8")

    print("OK: refreshed Slack-backed KPI sections")
    print(f"- marketing markets: {len(marketing_rows)} from #eventstats {marketing_at}")
    print(f"- upcoming workshop pipeline: {len(upcoming_pipeline_rows)} market(s) from Workshop Team Scheduling + live team updates")
    print(f"- expo: {expo['label']} total={expo['total']} from #expo {expo_at}")
    print(f"- preview finals: {len(preview_rows)} latest={preview_at}")
    print(f"- ME/workshop finals: {len(me_current_rows)} latest={me_at}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
