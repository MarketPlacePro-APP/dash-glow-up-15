#!/usr/bin/env python3
"""Regression tests for the time-aware active Preview deploy gate."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE_PATH = Path(__file__).with_name("phase1_predeploy_gate.py")
SPEC = importlib.util.spec_from_file_location("phase1_predeploy_gate", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

FRESHNESS_PATH = Path(__file__).with_name("phase1_freshness_spine.py")
FRESHNESS_SPEC = importlib.util.spec_from_file_location("phase1_freshness_spine_test", FRESHNESS_PATH)
assert FRESHNESS_SPEC and FRESHNESS_SPEC.loader
freshness_module = importlib.util.module_from_spec(FRESHNESS_SPEC)
sys.modules[FRESHNESS_SPEC.name] = freshness_module
FRESHNESS_SPEC.loader.exec_module(freshness_module)

TZ = ZoneInfo("America/Denver")


def schedule(times: str = "10:00AM & 2:00PM") -> dict:
    return {
        "records": [
            {
                "eventType": "front_end_preview",
                "state": "active",
                "startDate": "2026-07-25",
                "market": "Denver",
                "times": times,
            }
        ],
        "route_blocks": [],
    }


class ActivePreviewReportingWindowTests(unittest.TestCase):
    def test_pending_rows_do_not_bleed_into_following_active_row(self) -> None:
        source = """export const activePreviewMarkets: ActivePreviewMarket[] = [
  {
    market: 'Baltimore', team: 'Team Wayne / #eventstats',
    sessionsCompleted: null, totalSessions: null,
    sourceState: 'pending_source', startDate: '2026-09-09'
  },
  {
    market: 'White Plains', team: 'Team Vogel / #teamvogel',
    sessionsCompleted: 2, totalSessions: 10,
    sourceState: 'active_session', startDate: '2026-08-29',
    latestSessionDate: '2026-08-29'
  }
];"""
        self.assertEqual(
            module.active_preview_adapter_rows(source),
            [("White Plains", "Team Vogel / #teamvogel", "2", "10", "2026-08-29", "2026-08-29")],
        )

    def test_pre_session_refresh_does_not_require_nonexistent_slack_rows(self) -> None:
        now = datetime(2026, 7, 25, 8, 5, tzinfo=TZ)
        self.assertFalse(module.active_preview_reporting_expected(schedule(), now))

    def test_gate_requires_rows_after_first_session_reporting_grace(self) -> None:
        now = datetime(2026, 7, 25, 12, 5, tzinfo=TZ)
        self.assertTrue(module.active_preview_reporting_expected(schedule(), now))

    def test_parser_accepts_common_schedule_time_variants(self) -> None:
        self.assertEqual(module.first_scheduled_session_minute("10:00AM & 2:00PM"), 600)
        self.assertEqual(module.first_scheduled_session_minute("9 AM and 1:30 p.m."), 540)

    def test_missing_time_falls_back_to_noon(self) -> None:
        self.assertFalse(
            module.active_preview_reporting_expected(
                schedule(""), datetime(2026, 7, 25, 11, 59, tzinfo=TZ)
            )
        )
        self.assertTrue(
            module.active_preview_reporting_expected(
                schedule(""), datetime(2026, 7, 25, 12, 0, tzinfo=TZ)
            )
        )

    def test_active_freshness_channels_follow_live_cards_only(self) -> None:
        adapter = """export const activePreviewMarkets: ActivePreviewMarket[] = [
  { team: 'Team Wayne · Speaker Megan / #teamwayne', sourceState: 'active_session' },
  { team: 'Team Millar · Speaker Jay / #teammillar', sourceState: 'active_session' },
  { team: 'Team Dent · Speaker Nick / #teamdent', sourceState: 'final_route_totals' }
];"""
        self.assertEqual(
            freshness_module.active_preview_source_channels(adapter),
            ["teamwayne", "teammillar"],
        )


if __name__ == "__main__":
    unittest.main()
