#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from datetime import date
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("generate-live-data-review.py")
SPEC = importlib.util.spec_from_file_location("generate_live_data_review", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class WorkshopScheduleParserTest(unittest.TestCase):
    def test_schedule_and_route_statuses_respect_live_window(self) -> None:
        today = date(2026, 7, 19)

        self.assertEqual(module.schedule_status("2026-07-18", today=today), "historical")
        self.assertEqual(module.schedule_status("2026-07-19", today=today), "active")
        self.assertEqual(module.schedule_status("2026-07-20", today=today), "upcoming")

        self.assertEqual(module.route_status("2026-07-10", "2026-07-12", today=today), "historical")
        self.assertEqual(module.route_status("2026-07-18", "2026-07-20", today=today), "active")
        self.assertEqual(module.route_status("2026-07-25", "2026-07-27", today=today), "upcoming")

    def test_written_date_ranges(self) -> None:
        self.assertEqual(
            module.parse_2026_written_range("July 24-26"),
            ("2026-07-24", "2026-07-26"),
        )
        self.assertEqual(
            module.parse_2026_written_range("July 31-Aug 2"),
            ("2026-07-31", "2026-08-02"),
        )
        self.assertEqual(
            module.parse_2026_written_range("Sep 3-5 THUR- SAT"),
            ("2026-09-03", "2026-09-05"),
        )
        self.assertIsNone(module.parse_2026_written_range("not scheduled"))

    def test_future_workshop_record_is_built(self) -> None:
        rows = [[] for _ in range(98)]
        rows[3] = ["Dates", "July 24-26"]
        rows[4] = ["Market A", "Long Island, NY"]
        rows[5] = ["Speaker", "Tony Rosenbum"]
        rows[23] = ["Rooming List", "LONG ISLAND ME Sleeping Room | Marriott Melville Long Island"]

        blocks, events = module.parse_workshop_schedule_rows(rows, today=date(2026, 7, 17))

        self.assertEqual(len(blocks), 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(blocks[0]["sourceKey"], "workshop_team_schedule")
        self.assertEqual(blocks[0]["market"], "Long Island, NY")
        self.assertEqual(blocks[0]["team"], "Team Tony")
        self.assertEqual(blocks[0]["status"], "upcoming")
        self.assertEqual(blocks[0]["startDate"], "2026-07-24")
        self.assertEqual(blocks[0]["endDate"], "2026-07-26")
        self.assertEqual(blocks[0]["venues"], ["Marriott Melville Long Island"])
        self.assertEqual(events[0]["eventType"], "middle_end_workshop")


if __name__ == "__main__":
    unittest.main()
