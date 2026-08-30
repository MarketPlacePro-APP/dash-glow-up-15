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

API = "https://slack.com/api"


def slack_get(method: str, token: str, params: dict) -> dict:
    url = f"{API}/{method}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def resolve_channel_id(name: str, token: str) -> str | None:
    cursor = ""
    while True:
        params = {"limit": 1000, "types": "public_channel,private_channel"}
        if cursor:
            params["cursor"] = cursor
        data = slack_get("conversations.list", token, params)
        if not data.get("ok"):
            return None
        for channel in data.get("channels", []):
            if channel.get("name") == name:
                return channel.get("id")
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            return None


def channel_records(name: str, token: str, limit: int) -> tuple[bool, list[str], str]:
    channel_id = resolve_channel_id(name, token)
    if not channel_id:
        return False, [], "channel not found or bot not a member"
    data = slack_get("conversations.history", token, {"channel": channel_id, "limit": limit})
    if not data.get("ok"):
        return False, [], str(data.get("error", "history_error"))
    records = []
    # Oldest-first so posted_at ordering within a channel is chronological.
    for message in reversed(data.get("messages", [])):
        ts = str(message.get("ts", "0"))
        posted_at = datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
        text = (message.get("text") or "").replace("\r", " ").replace("\n", " ").strip()
        records.append(f"--- #{name} {posted_at} ts={ts}\n{text}")
    return True, records, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("channels", nargs="+")
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise SystemExit("SLACK_BOT_TOKEN not set")

    checked, unavailable, sections = [], [], []
    for raw in args.channels:
        name = raw.lstrip("#")
        ok, records, err = channel_records(name, token, args.limit)
        if ok:
            checked.append(name)
            body = "\n".join(records) if records else "(no recent messages)"
            sections.append(f"## #{name}\n{body}")
        else:
            unavailable.append(f"{name}: {err}")
            sections.append(f"## #{name}\nUNAVAILABLE: {err}")

    summary = [
        "Channels checked: " + (", ".join(checked) if checked else "none"),
        "Channels unavailable: " + (", ".join(unavailable) if unavailable else "none"),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(summary) + "\n\n" + "\n\n".join(sections) + "\n")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
