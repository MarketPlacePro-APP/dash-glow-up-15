#!/usr/bin/env python3
"""Regression tests for the rolling TLWB Preview → Middle-End pipeline."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("update_tlwb_slack_operational_sections.py")
spec = importlib.util.spec_from_file_location("tlwb_slack_operational", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def write_schedule(
    root: Path,
    routes: list[dict],
    preview_routes: list[dict] | None = None,
    generated_at: str = "2026-07-19T19:00:00-06:00",
) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "schedule.json").write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "sections": {
                    "middle_end_workshop_routes": routes,
                    "preview_routes": preview_routes or [],
                },
            }
        ),
        encoding="utf-8",
    )


class UpcomingMePipelineTests(unittest.TestCase):
    def test_spelled_state_suffix_matches_abbreviation_without_damaging_city_name(self) -> None:
        self.assertEqual(
            module.normalize_market_name("Tulsa Oklahoma"),
            module.normalize_market_name("Tulsa, OK"),
        )
        self.assertEqual(module.normalize_market_name("Oklahoma City, OK"), "oklahoma city")
        self.assertEqual(
            module.normalize_market_name("Saint Louis, MO"),
            module.normalize_market_name("St. Louis"),
        )
        self.assertEqual(module.normalize_market_name("St. Louis"), "st louis")

    def test_schedule_rolls_forward_and_excludes_completed_or_far_future_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_schedule(
                root,
                [
                    {"market": "Orlando, FL", "team": "Team Tony", "teamKey": "tony", "startDate": "2026-07-10", "endDate": "2026-07-12", "status": "completed"},
                    {"market": "Long Island, NY", "team": "Team Tony", "teamKey": "tony", "startDate": "2026-07-24", "endDate": "2026-07-26", "status": "upcoming", "fetchedAt": "2026-07-19T18:00:00-06:00"},
                    {"market": "Late Future", "team": "Team Shaw", "teamKey": "shaw", "startDate": "2026-08-10", "endDate": "2026-08-12", "status": "upcoming"},
                ],
            )
            rows = module.parse_upcoming_pipeline([], root)
            rendered = "\n".join(rows)
            self.assertEqual(len(rows), 1)
            self.assertIn("market: 'Long Island, NY'", rendered)
            self.assertIn("previewSold: null", rendered)
            self.assertIn("projectedBuyingUnits: null", rendered)
            self.assertNotIn("Orlando", rendered)
            self.assertNotIn("Late Future", rendered)

    def test_confirmation_populates_sold_and_confirmed_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_schedule(
                root,
                [{"market": "Long Island, NY", "team": "Team Tony", "teamKey": "tony", "startDate": "2026-07-24", "endDate": "2026-07-26", "status": "upcoming"}],
            )
            message = module.SlackMessage(
                channel="teamtony",
                posted_at="2026-07-20T10:00:00-06:00",
                ts="test-confirmation",
                body="Long Island Update Sold: 34 Total Confirmed: 31 Guests: 2",
            )
            rendered = "\n".join(module.parse_upcoming_pipeline([message], root))
            self.assertIn("previewSold: 34", rendered)
            self.assertIn("projectedBuyingUnits: 31", rendered)
            self.assertIn("#teamtony update", rendered)

    def test_preview_final_never_becomes_confirmed_buying_units(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_schedule(
                root,
                [{"market": "Tulsa, OK", "team": "Team Nick", "teamKey": "nick", "startDate": "2026-07-31", "endDate": "2026-08-02", "status": "upcoming"}],
            )
            message = module.SlackMessage(
                channel="teamdent",
                posted_at="2026-07-15T20:00:00-06:00",
                ts="test-preview-final",
                body="Tulsa Final Numbers FINAL ROUTE NUMBERS Total Deals: 20",
            )
            rendered = "\n".join(module.parse_upcoming_pipeline([message], root))
            self.assertIn("previewSold: 20", rendered)
            self.assertIn("projectedBuyingUnits: null", rendered)
            self.assertIn("preview final: 20 buyers sold", rendered)

    def test_active_route_uses_floor_count_and_preserves_roster_discrepancy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_schedule(
                root,
                [{"market": "Tulsa, OK", "team": "Team Nick", "teamKey": "nick", "startDate": "2026-07-31", "endDate": "2026-08-02", "status": "active"}],
                generated_at="2026-08-01T09:00:00-06:00",
            )
            messages = [
                module.SlackMessage("teamnick", "2026-07-29T12:00:00-06:00", "confirmation", "Tulsa Update: 20 Sold / Total Confirmed 17"),
                module.SlackMessage("teamnick", "2026-07-31T10:00:00-06:00", "floor", "17 BU’s / 9 Guests"),
                module.SlackMessage("teamnick", "2026-07-31T10:15:00-06:00", "roster", "I'm counting 19 students on my roster."),
            ]
            rendered = "\n".join(module.parse_upcoming_pipeline(messages, root))
            self.assertIn("projectedBuyingUnits: 17", rendered)
            self.assertIn("17 BU on site and 9 guests", rendered)
            self.assertIn("later roster check reports 19 students", rendered)
            self.assertIn("reconciliation is pending", rendered)


if __name__ == "__main__":
    unittest.main()
