#!/usr/bin/env python3
"""Headless Slack channel history collector for CI (replaces the Studio-only
skills/tlwb-preview-reporting/scripts/recent_slack.py).

Emits the exact per-message record format that
scripts/update_tlwb_slack_operational_sections.py::parse_messages consumes:

    --- #<channel> <posted_at> ts=<slack_ts>
    <message body>

Records are delimited by the next "--- #" (or a "## #" section header) and the
body is whitespace-normalized by the parser, so single-line bodies are emitted.
Uses a Slack bot token (SLACK_BOT_TOKEN) with channels:history and the bot
invited to each channel.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.slack.com/api"


def slack_get(method: str, token: str, params: dict) -> dict:
    url = f"{API}/{method}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


# This is ingestion lineage, not a current team/speaker assignment. Channel
# teamdent was renamed teamwollaston; preserve historical source keys by ID.
KNOWN_CHANNEL_IDENTITIES = {"teamdent": "C09Q2B8SNTX"}


def apply_known_channel_identities(channels: dict[str, str]) -> dict[str, str]:
    result = dict(channels)
    visible_ids = set(channels.values())
    for legacy_name, channel_id in KNOWN_CHANNEL_IDENTITIES.items():
        # A reused name must never silently point history at a different source.
        result.pop(legacy_name, None)
        if channel_id in visible_ids:
            result[legacy_name] = channel_id
    return result


def resolve_channel_map(token: str) -> dict[str, str]:
    result: dict[str, str] = {}
    cursor = ""
    while True:
        params = {"limit": 1000, "types": "public_channel,private_channel", "exclude_archived": "true"}
        if cursor:
            params["cursor"] = cursor
        data = slack_get("conversations.list", token, params)
        if not data.get("ok"):
            raise RuntimeError(f"conversations.list failed: {data.get('error', 'unknown')}")
        for channel in data.get("channels", []):
            name = channel.get("name")
            channel_id = channel.get("id")
            if name and channel_id:
                result[str(name)] = str(channel_id)
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            return apply_known_channel_identities(result)


def channel_records(name: str, channel_id: str | None, token: str, limit: int) -> tuple[bool, list[str], str, str | None]:
    if not channel_id:
        return False, [], "channel not found or bot not a member", None
    data = slack_get("conversations.history", token, {"channel": channel_id, "limit": limit})
    if not data.get("ok"):
        return False, [], str(data.get("error", "history_error")), None
    records = []
    # Oldest-first so posted_at ordering within a channel is chronological.
    for message in reversed(data.get("messages", [])):
        ts = str(message.get("ts", "0"))
        posted_at = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
        text = (message.get("text") or "").replace("\r", " ").replace("\n", " ").strip()
        records.append(f"--- #{name} {posted_at} ts={ts}\n{text}")
    newest = data.get("messages", [{}])[0].get("ts") if data.get("messages") else None
    latest = datetime.fromtimestamp(float(newest), tz=timezone.utc).isoformat() if newest else None
    return True, records, "", latest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channels", nargs="+")
    parser.add_argument("--optional", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--status-out", type=Path)
    args = parser.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise SystemExit("SLACK_BOT_TOKEN not set")

    channel_map = resolve_channel_map(token)
    required = {raw.lstrip("#") for raw in args.channels}
    requested = [*args.channels, *args.optional]
    checked, unavailable, sections, statuses = [], [], [], {}
    for raw in requested:
        name = raw.lstrip("#")
        is_required = name in required
        ok, records, err, latest = channel_records(name, channel_map.get(name), token, args.limit)
        if ok:
            checked.append(name)
            body = "\n".join(records) if records else "(no recent messages)"
            sections.append(f"## #{name}\n{body}")
            statuses[name] = {
                "channel": name,
                "required": is_required,
                "status": "ok_fresh" if latest else "ok_no_new_expected",
                "rows_seen": len(records),
                "new_rows_since_last_check": 0,
                "latest_source_post_date": latest,
            }
        else:
            unavailable.append(f"{name}: {err}")
            sections.append(f"## #{name}\nUNAVAILABLE: {err}")
            statuses[name] = {
                "channel": name,
                "required": is_required,
                "status": "failed" if is_required else "not_in_channel",
                "rows_seen": 0,
                "new_rows_since_last_check": 0,
                "latest_source_post_date": None,
                "error": err,
            }

    summary = [
        "Channels checked: " + (", ".join(checked) if checked else "none"),
        "Channels unavailable: " + (", ".join(unavailable) if unavailable else "none"),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(summary) + "\n\n" + "\n\n".join(sections) + "\n")
    if args.status_out:
        checked_at = datetime.now(timezone.utc).isoformat()
        for value in statuses.values():
            value["latest_checked_at"] = checked_at
        args.status_out.parent.mkdir(parents=True, exist_ok=True)
        args.status_out.write_text(json.dumps({"checked_at": checked_at, "channels": statuses}, indent=2) + "\n")
    print("\n".join(summary))
    required_unavailable = [name for name in required if statuses.get(name, {}).get("status") == "failed"]
    if required_unavailable:
        print("Required channels unavailable: " + ", ".join(sorted(required_unavailable)))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
