#!/usr/bin/env python3
"""Regression coverage for active marketing and pre-event Preview no-drop."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("update_tlwb_slack_operational_sections.py")
spec = importlib.util.spec_from_file_location("tlwb_slack_updater", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

SlackMessage = module.SlackMessage


def eventstats(market: str, start: str, posted_at: str, regs: int) -> SlackMessage:
    body = (
        f"{market}- 1 workshop (Starts, {start}) | "
        f"Facebook: Reg: {regs - 30} Spend: $10,000 CPR: $20 | "
        "Youtube: Reg: 20 Spend: $1,000 CPR: $50 | "
        "Google Search: Reg: 10 Spend: $500 CPR: $50 | "
        f"Total: Reg: {regs} Spend: $11,500 CPR: $23"
    )
    return SlackMessage(channel="eventstats", posted_at=posted_at, ts=posted_at, body=body)


def test_marketing_keeps_current_and_upcoming_without_first_n_drop() -> None:
    messages = [
        eventstats("Ann Arbor", "Saturday August 8th", "2026-08-21T08:10:00-06:00", 100),
        eventstats("Boise", "Saturday August 8th", "2026-08-21T08:11:00-06:00", 110),
        eventstats("Raleigh", "Saturday August 8th", "2026-08-21T08:12:00-06:00", 120),
        eventstats("Greenville", "Saturday August 15th", "2026-08-21T08:13:00-06:00", 130),
        eventstats("Little Rock", "Saturday August 15th", "2026-08-21T08:14:00-06:00", 140),
        eventstats("San Francisco", "Saturday August 15th", "2026-08-21T08:15:00-06:00", 150),
        eventstats("Charlotte", "Saturday August 22nd", "2026-08-21T08:16:00-06:00", 160),
        eventstats("St. Louis", "Saturday August 22nd", "2026-08-21T08:17:00-06:00", 170),
        eventstats("Portland", "Saturday August 22nd", "2026-08-21T08:18:00-06:00", 680),
        eventstats("Atlanta", "Saturday August 29th", "2026-08-21T08:19:00-06:00", 190),
        eventstats("White Plains", "Saturday August 29th", "2026-08-21T08:20:00-06:00", 200),
    ]

    rows, latest = module.parse_marketing(messages)
    rendered = "\n".join(rows)

    assert latest == "2026-08-21T08:20:00-06:00"
    assert "market: 'Portland'" in rendered
    assert "registered: 680" not in rendered  # Marketing rows use channel-level registration fields.
    assert "market: 'Atlanta'" in rendered
    assert "market: 'White Plains'" in rendered
    assert "market: 'Ann Arbor'" not in rendered
    assert "market: 'Boise'" not in rendered
    assert "market: 'Raleigh'" not in rendered
    assert len(rows) == 8


def test_pending_preview_rows_include_portland_eventstats_truth() -> None:
    messages = [
        eventstats("Portland", "Saturday August 22nd", "2026-08-21T08:18:00-06:00", 680),
        eventstats("Charlotte", "Saturday August 22nd", "2026-08-21T08:16:00-06:00", 160),
        eventstats("St. Louis", "Saturday August 22nd", "2026-08-21T08:17:00-06:00", 170),
        eventstats("Atlanta", "Saturday August 29th", "2026-08-21T08:19:00-06:00", 190),
    ]

    rows = module.parse_pending_preview_markets(messages, set(), [])
    rendered = "\n".join(rows)

    assert "market: 'Portland'" in rendered
    assert "registered: 680" in rendered
    assert "sourceState: 'pending_source'" in rendered
    assert "startDate: '2026-08-22'" in rendered
    assert "Pre-event #eventstats" in rendered


if __name__ == "__main__":
    test_marketing_keeps_current_and_upcoming_without_first_n_drop()
    test_pending_preview_rows_include_portland_eventstats_truth()
    print("OK: marketing + pending Preview no-drop regressions")
