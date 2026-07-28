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
from datetime import datetime, timedelta
from pathlib import Path


PREVIEW_CHANNELS = {
    "teamwayne": "Team Wayne",
    "teamdent": "Team Dent",
    "teamwyman": "Team Wyman",
    "teamvogel": "Team Vogel",
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
    for row in schedule_records:
        if str(row.get("market", "")).lower() != market.lower():
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


def numeric_literal(value: int | str | None) -> str:
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


def parse_marketing(messages: list[SlackMessage]) -> tuple[list[str], str]:
    rows: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    event_messages = [msg for msg in messages if msg.channel == "eventstats"]
    latest_at = ""
    for msg in event_messages:
        body = msg.body
        if "workshop" not in body.lower() or "Total:" not in body:
            continue
        market_match = re.search(r"^\s*:?\w*:?\s*([A-Za-z][A-Za-z., /-]+?)\s*-\s*1\s+workshop", body, re.I)
        starts_match = re.search(r"Starts,\s*([^)]+)\)", body, re.I)
        if not market_match or not starts_match:
            continue
        market = market_match.group(1).strip().replace(" ,", ",")
        starts = starts_match.group(1).strip()
        start_date = parse_start_date(starts) or "9999-12-31"
        key = market.lower()
        if key in seen:
            continue
        seen.add(key)
        latest_at = max(latest_at, msg.posted_at)
        channels = []
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
            channels.append(f"      {{ channel: '{out_label}', regs: {regs}, spend: {spend}, cpr: {cpr} }}")
        rows.append((
            start_date,
            msg.posted_at,
            "  {\n"
            f"    market: '{ts_literal(market)}',\n"
            f"    starts: '{ts_literal(starts)}',\n"
            "    channels: [\n"
            + ",\n".join(channels)
            + "\n    ]\n"
            "  }"
        ))
    if len(rows) < 4:
        raise SystemExit(f"Parsed only {len(rows)} active #eventstats markets; refusing to ship partial marketing state")
    rows.sort(key=lambda row: (row[0], row[1]))
    return [row for _, _, row in rows[:8]], latest_at


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
        projected = int(confirmation["confirmed"]) if confirmation and int(confirmation.get("confirmed") or 0) else None
        preview_team = str(preview_final["team"]) if preview_final else (preceding[0][1] if preceding else "Pending preview source")
        if preview_final:
            preview_team = f"{preview_team} / #{preview_final['channel']}"
        source_posted_at = str(confirmation["posted_at"]) if confirmation else str(route.get("fetchedAt") or generated_raw)
        if confirmation:
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


def active_preview_market_display(value: str) -> str:
    market = re.sub(r"\s+", " ", value).strip(" ,")
    market = re.sub(r",\s*(AL|FL|TX|NC|SC|OH|MA|AZ|WA)\b\.?", "", market, flags=re.I)
    market = re.sub(r"\b(Previews?|Preview)\b$", "", market, flags=re.I).strip(" ,")
    return market.replace("Meyers", "Myers")


def preview_sold_sources(messages: list[SlackMessage]) -> dict[str, dict[str, int | str]]:
    sold_by_market: dict[str, dict[str, int | str]] = {}
    for msg in messages:
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        body = msg.body
        if not (
            "FINAL ROUTE NUMBERS" in body
            or "MARKET REPORT" in body
            or "Final Numbers" in body
        ):
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
    match = re.search(r"Day\s+(\d+)\s+Session\s+(\d+)", body, re.I)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


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
        if not ("FINAL ROUTE NUMBERS" in msg.body or "Final Numbers" in msg.body or "MARKET REPORT" in msg.body):
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
        if "FINAL ROUTE NUMBERS" in body or "Final Numbers" in body or "MARKET REPORT" in body:
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
                "route_sales_pct": 0.0,
                "master_class_sales": -1,
                "master_class_speaker": "",
                "total_futures": 0,
            })
        row["posted_at"] = max(str(row["posted_at"]), msg.posted_at)
        row["date"] = max(str(row["date"]), date)
        route_sales_match = re.search(r"Total\s+Route\s+Conversion\s*:\s*([0-9]+(?:\.[0-9]+)?)%", body, re.I)
        master_class_sales = cumulative_master_class(body)
        speaker_name = master_class_speaker(body)
        total_futures = number_after(body, ("Total Futures",))
        if reg is not None:
            row["registered"] = reg
        if attendance is not None:
            row["attendance"] = attendance
        if sales is not None:
            row["sales"] = sales
            row["result_received"] = 1
        if route_sales_match:
            row["route_sales_pct"] = float(route_sales_match.group(1))
        if master_class_sales is not None:
            row["master_class_sales"] = master_class_sales
            row["master_class_speaker"] = speaker_name or row.get("master_class_speaker") or ""
            # Teams omit Total Futures when the cumulative value is zero.
            row["total_futures"] = total_futures or 0

    if not latest_session_date:
        return [], [], "", ""

    latest_dt = datetime.fromisoformat(latest_session_date)
    active_sessions = [
        row for row in sessions.values()
        # Live cards must reflect the current route window. A missing final report
        # must not leave an old market marked LIVE indefinitely.
        if (latest_dt - datetime.fromisoformat(str(row["date"]))).days <= 3
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
            session_rows.append((
                str(row["date"]),
                f"{market}-{int(row['day'])}-{int(row['session'])}",
                int(row["day"]),
                int(row["session"]),
                (
                    f"  {{ market: '{ts_literal(market)}', team: '{team}', "
                    f"session: 'Day {int(row['day'])} Session {int(row['session'])}', "
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
        posted_route_rates = [
            (str(row["posted_at"]), float(row.get("route_sales_pct") or 0.0))
            for row in market_rows if float(row.get("route_sales_pct") or 0.0) > 0
        ]
        latest_posted_route_rate = max(posted_route_rates)[1] if posted_route_rates else None
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


def parse_preview(messages: list[SlackMessage], schedule_records: list[dict] | None = None) -> tuple[list[str], str]:
    active_rows, _active_session_rows, active_at, _active_data_date = parse_active_preview_rows(messages, schedule_records)
    rows: list[str] = [*active_rows]
    latest = active_at
    active_market_keys = {
        normalize_market_name(current.split("market: '", 1)[1].split("'", 1)[0])
        for current in active_rows if "market: '" in current
    }

    # Speaker attribution comes from the latest cumulative Master Class line
    # for the same market/channel. The final post itself often omits speaker.
    speaker_sources: dict[tuple[str, str], tuple[str, str]] = {}
    route_date_sources: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for msg in messages:
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        market = market_from_preview(msg.body)
        if not market:
            continue
        key = (msg.channel, normalize_market_name(active_preview_market_display(market)))
        session_date = body_date(msg.body)
        if session_date:
            route_date_sources.setdefault(key, []).append((msg.posted_at, session_date))
        speaker = master_class_speaker(msg.body)
        if not speaker:
            continue
        current = speaker_sources.get(key)
        if current is None or msg.posted_at > current[0]:
            speaker_sources[key] = (msg.posted_at, speaker)

    final_candidates: list[tuple[str, str, str, str]] = []
    seen_markets: set[str] = set()
    for msg in sorted(messages, key=lambda current: current.posted_at, reverse=True):
        if msg.channel not in PREVIEW_CHANNELS:
            continue
        body = msg.body
        if not (
            "FINAL ROUTE NUMBERS" in body
            or "MARKET REPORT" in body
            or "Final Numbers" in body
        ):
            continue
        market = market_from_preview(body)
        reg = number_after(body, ("Total Reg",))
        headcount = number_after(body, ("Total Head Count",))
        late = number_after(body, ("Total Late Arrivals",)) or 0
        attendees = number_after(body, ("Total Attendees",))
        deals = number_after(body, ("Total Deals",))
        if not market or reg is None or headcount is None or deals is None:
            continue
        market_key = normalize_market_name(active_preview_market_display(market))
        if market_key in active_market_keys:
            continue
        if market_key in seen_markets:
            continue
        seen_markets.add(market_key)
        attended = attendees or (headcount + late)
        team = preview_team_from_final(body, msg.channel)
        speaker = speaker_sources.get((msg.channel, market_key), ("", ""))[1] or team.removeprefix("Team ").strip()
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
            f"    sales: {deals},\n"
            f"    previewShowRate: {percent_rate(headcount, reg)},\n"
            f"    salesRate: {percent_rate(deals, headcount)},\n"
            "    status: 'yellow',\n"
            "    sourceState: 'final_route_totals',\n"
            f"    startDate: '{route_start_date}',\n"
            f"    latestSessionDate: '{msg.posted_at[:10]}',\n"
            f"    sourcePostedAt: '{msg.posted_at}',\n"
            f"    sourceNote: 'Final route report from #{msg.channel}, labeled {ts_literal(team)}, at {msg.posted_at}: {reg} reg, {headcount} cutoff headcount, {attended} attendees including late arrivals, {deals} deals.'\n"
            "  }"
        )
        final_candidates.append((msg.posted_at, msg.channel, market_key, rendered))

    # Preserve recent coverage from every visible preview team channel. The old
    # global rows[:6] cap consumed all slots with #teamwayne/#teamdent because
    # the Slack bundle is grouped by channel, hiding current #teamvogel finals.
    finals_per_channel: dict[str, int] = {}
    selected_finals: list[str] = []
    for _posted_at, channel, _market_key, rendered in final_candidates:
        if finals_per_channel.get(channel, 0) >= 2:
            continue
        selected_finals.append(rendered)
        finals_per_channel[channel] = finals_per_channel.get(channel, 0) + 1
    rows.extend(selected_finals)

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
                parts.append(f"{grade}: {value} (as reported)")
                continue
            buyer_label = "buyer" if buyers == 1 else "buyers"
            parts.append(f"{grade}: {buyers} {buyer_label} · {sold} sold ({percent}%)")
            continue
        zero_match = re.fullmatch(r"0(?:\s*=\s*0\s*%)?", value)
        if zero_match:
            parts.append(f"{grade}: 0 buyers")
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
                "slack://channels/teamwayne,teamdent,teamwyman,teamvogel/latest-final-route-reports",
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
