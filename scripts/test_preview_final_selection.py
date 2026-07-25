#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "update_tlwb_slack_operational_sections.py"
SPEC = importlib.util.spec_from_file_location("tlwb_slack_updater", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def msg(channel: str, posted_at: str, body: str):
    return module.SlackMessage(channel=channel, posted_at=posted_at, ts=posted_at, body=body)


def final(channel: str, posted_at: str, market: str, team: str, reg: int, headcount: int, late: int, deals: int):
    return msg(
        channel,
        posted_at,
        (
            f"{market} Final Numbers | {team} | | Total Reg: {reg} Total Head Count: {headcount} "
            f"Total Late Arrivals: {late} Total Attendees: {headcount + late} Total Deals: {deals}"
        ),
    )


def result(channel: str, posted_at: str, market: str, date: str, speaker: str, cumulative: int):
    return msg(
        channel,
        posted_at,
        (
            f"{market} | {date} | Day 4 Session 2 | Session Deals: 3 "
            f"Master Class: ({speaker}): {cumulative} Total Route Conversion: 30%"
        ),
    )


class PreviewFinalSelectionTests(unittest.TestCase):
    def test_preserves_team_channel_coverage_and_uses_explicit_team_and_speaker(self):
        # Bundle order intentionally groups #teamwayne first, reproducing the old
        # rows[:6] bug that hid all #teamvogel cards.
        messages = [
            final("teamwayne", "2026-07-15T20:26:00-06:00", "Memphis", "Team Gray", 1745, 235, 22, 85),
            result("teamwayne", "2026-07-12T15:01:00-06:00", "Memphis", "Sunday 7/12/26", "Jay", 16),
            final("teamwayne", "2026-07-11T14:27:00-06:00", "Nashville", "Team Gray", 923, 114, 10, 40),
            final("teamwayne", "2026-07-01T21:33:00-06:00", "Phoenix", "Team Wayne", 1022, 111, 2, 35),
            result("teamwayne", "2026-07-15T20:23:00-06:00", "Memphis", "Wednesday 7/15/26", "Jay", 82),
            result("teamwayne", "2026-07-11T14:23:00-06:00", "Nashville", "Saturday 7/11/26", "Jay", 38),
            final("teamdent", "2026-07-15T19:16:00-06:00", "Tulsa, OK", "Team Dent", 864, 114, 14, 20),
            final("teamdent", "2026-07-11T14:23:00-06:00", "Oklahoma City", "Team Dent", 1302, 130, 16, 32),
            result("teamdent", "2026-07-15T19:15:00-06:00", "Tulsa, OK", "Wednesday 7/15/26", "Nick", 20),
            result("teamdent", "2026-07-11T14:22:00-06:00", "Oklahoma City", "Saturday 7/11/26", "Megan", 29),
            final("teamvogel", "2026-07-15T20:43:00-06:00", "Hartford", "Team Vogel", 1233, 137, 23, 58),
            final("teamvogel", "2026-07-11T13:37:00-06:00", "Long Island", "Team Vogel", 1686, 120, 39, 64),
            result("teamvogel", "2026-07-15T19:32:00-06:00", "Hartford", "Wednesday 7/15/26", "Tony", 55),
            result("teamvogel", "2026-07-11T13:35:00-06:00", "Long Island", "Saturday 7/11/26", "Tony", 62),
        ]

        rows, latest = module.parse_preview(messages, [])
        rendered = "\n".join(rows)

        self.assertEqual(latest, "2026-07-15T20:43:00-06:00")
        self.assertEqual(len(rows), 6)
        self.assertIn("market: 'Hartford'", rendered)
        self.assertIn("market: 'Long Island'", rendered)
        self.assertIn("Team Vogel · Speaker Tony / #teamvogel", rendered)
        self.assertIn("Team Gray · Speaker Jay / #teamwayne", rendered)
        self.assertIn("Team Dent · Speaker Nick / #teamdent", rendered)
        memphis_row = next(row for row in rows if "market: 'Memphis'" in row)
        self.assertIn("startDate: '2026-07-12'", memphis_row)
        self.assertNotIn("market: 'Phoenix'", rendered)
        self.assertNotIn("Team Wayne · Speaker Wayne / #teamwayne", rendered)

    def test_final_without_explicit_team_falls_back_to_channel_team(self):
        body = "Tulsa, OK Final Numbers Total Reg: 100 Total Head Count: 10 Total Deals: 3"
        self.assertEqual(module.preview_team_from_final(body, "teamdent"), "Team Dent")


    def test_indiana_state_variant_reconciles_result_to_headcount(self):
        messages = [
            msg(
                "teamwayne",
                "2026-07-25T08:30:28-06:00",
                (
                    "WK 30 | Indianapolis, IN | Saturday, 07/25/2026 | Day 1 Session 1 | "
                    "30-Minute Headcount | Total Reg: 118 Total Count: 11 Show Factor: 9.3%"
                ),
            ),
            msg(
                "teamwayne",
                "2026-07-25T10:23:47-06:00",
                (
                    "WK 30 | Indianapolis, IND | Saturday, 07/25/2026 | Day 1 Session 1 | "
                    "Session Deals: 5 Session Conversion: 45% Master Class: (Megan): 5 "
                    "Total Route Conversion: 45.5%"
                ),
            ),
        ]

        rows, session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        rendered = "\n".join(rows)
        sessions = "\n".join(session_rows)

        self.assertEqual(len(rows), 1)
        self.assertIn("market: 'Indianapolis, IN'", rendered)
        self.assertIn("Team Wayne · Speaker Megan / #teamwayne", rendered)
        self.assertIn("sessionsCompleted: 1", rendered)
        self.assertIn("sales: 5", rendered)
        self.assertIn("routeDeals: 5", rendered)
        self.assertIn("sales: 5", sessions)


if __name__ == "__main__":
    unittest.main()
