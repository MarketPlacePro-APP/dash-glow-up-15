#!/usr/bin/env python3
"""Regression tests for generated Preview team history."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MODULE_PATH = Path(__file__).resolve().parent / "tlwb_preview_history.py"
SPEC = importlib.util.spec_from_file_location("tlwb_preview_history_tested", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)
YEAR_START = datetime(2026, 1, 1, tzinfo=ZoneInfo("America/Denver"))


class PreviewHistoryTests(unittest.TestCase):
    def test_parses_simple_final_route_post(self) -> None:
        row = module.parse_history_row(
            "teamwayne",
            "1784168778.908349",
            "*Memphis Final Numbers* *Team Gray* Total Reg: 1745 Total Head Count: 235 "
            "Total Late Arrivals: 22 Total Attendees: 257 Closing Percentage: 36.2% "
            "Total Deals: 85 Sales: $33,745 Futures: 3",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.team, "Team Wayne")
        self.assertEqual(row.market, "Memphis")
        self.assertEqual(row.reg, 1745)
        self.assertEqual(row.attended, 235)
        self.assertEqual(row.sold, 85)
        self.assertIsNone(row.buying_units)

    def test_parses_combined_result_and_final_with_master_class(self) -> None:
        row = module.parse_history_row(
            "teamdent",
            "1784164605.992259",
            "*WK 29* *Tulsa, OK |* *Wednesday, 07/15/2026* *Results* "
            "Master Class: (Nick): 20 Total Route Conversion: 16.9% "
            "*::::FINAL ROUTE NUMBERS:::* *Tulsa, OK| Preview* "
            "Total Reg: 864 Total Head Count: 114 Total Deals: 20",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.date, "2026-07-15")
        self.assertEqual(row.buying_units, 20)
        self.assertEqual(row.sold, 20)

    def test_repairs_source_digit_typo_from_posted_show_factor(self) -> None:
        row = module.parse_history_row(
            "teamwyman",
            "1773194251.614139",
            "*Memphis, TN- Preview* *Tuesday, March 10th, 2026* *::::FINAL NUMBERS:::* "
            "Total Reg: 1,1661 Total Head Count: 297 Show Factor: 17.88% Total Deals: 67",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.reg, 1661)
        self.assertEqual(row.market, "Memphis, TN")

    def test_uses_post_timestamp_when_template_date_is_stale(self) -> None:
        row = module.parse_history_row(
            "teamwayne",
            "1779242433.899939",
            "_PREVIEW FINAL MARKET REPORT_ *Minneapolis Final Numbers* *Tuesday, April 19th 2026* "
            "Total Reg: 1,382 Total Head Count: 158 Total Deals: 51",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.market, "Minneapolis")
        self.assertEqual(row.date, "2026-05-19")

    def test_parses_uppercase_final_numbers_after_team_and_week(self) -> None:
        row = module.parse_history_row(
            "teamwayne",
            "1786581856.271499",
            "Raleigh, NC Team Wayne WK 30 FINAL NUMBERS: Total Reg: 888 "
            "Total Head Count: 93 Total Late Arrivals: 24 Total Attendees: 117 "
            "Show Factor: 10.47% Closing Percentage: 37.6% Total Deals: 35 Futures: 0",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.team, "Team Wayne")
        self.assertEqual(row.market, "Raleigh")
        self.assertEqual((row.reg, row.attended, row.sold), (888, 93, 35))

    def test_includes_team_millar_history(self) -> None:
        row = module.parse_history_row(
            "teammillar",
            "1786589701.405879",
            "WK 32 | Boise, Idaho | Wednesday, 08/12/2026 | Day 5 Session 2 | RESULTS "
            "Master Class: (Nick): 31 ::::FINAL ROUTE NUMBERS::: "
            "WK. 32 | FINAL NUMBERS Boise, Idaho | Preview | Total Reg: 460 "
            "Total Head Count: 106 Total Late Arrivals: 5 Total Attendees: 111 Total Deals: 37",
            YEAR_START,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.team, "Team Millar")
        self.assertEqual(row.market, "Boise, Idaho")
        self.assertEqual((row.reg, row.attended, row.buying_units, row.sold), (460, 106, 31, 37))

    def test_ignores_non_final_posts(self) -> None:
        row = module.parse_history_row(
            "teamvogel",
            "1784169807.736069",
            "Hartford Day 3 Session 2 Total Reg: 200 Total Head Count: 25 Total Deals: 8",
            YEAR_START,
        )
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
