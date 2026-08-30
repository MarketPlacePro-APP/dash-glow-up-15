#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("update_tlwb_slack_operational_sections.py")
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
    def test_flattened_weekday_suffix_joins_saint_louis_session_to_final(self):
        self.assertEqual(
            module.normalize_market_name("Saint Louis, MO Wednesday"),
            module.normalize_market_name("St. Louis, MO"),
        )

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

    def test_mislabeled_total_route_conversion_does_not_block_whole_route_reconciliation(self):
        messages = [
            msg("teamwayne", "2026-08-08T09:00:00-06:00", "Raleigh, NC | Saturday 8/8/26 | Day 1 Session 1 | Total Reg: 39 Total Count: 5"),
            msg("teamwayne", "2026-08-08T10:00:00-06:00", "Raleigh, NC | Saturday 8/8/26 | Day 1 Session 1 | Session Deals: 1 Session Conversion: 20% Master Class: (Megan): 1 Total Route Conversion: 20%"),
            msg("teamwayne", "2026-08-08T12:00:00-06:00", "Raleigh, NC | Saturday 8/8/26 | Day 1 Session 2 | Total Reg: 41 Total Count: 0"),
            msg("teamwayne", "2026-08-08T13:00:00-06:00", "Raleigh, NC | Saturday 8/8/26 | Day 1 Session 2 | Session Deals: 0 Session Conversion: 0% Master Class: (Megan): 1 Total Route Conversion: 0%"),
            msg("teamwayne", "2026-08-09T09:00:00-06:00", "Raleigh, NC | Sunday 8/9/26 | Day 2 Session 1 | Total Reg: 83 Total Count: 13"),
            msg("teamwayne", "2026-08-09T10:00:00-06:00", "Raleigh, NC | Sunday 8/9/26 | Day 2 Session 1 | Session Deals: 7 Session Conversion: 54% Master Class: (Megan): 8 Total Route Conversion: 54%"),
        ]

        rows, _session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        rendered = "\n".join(rows)

        self.assertEqual(len(rows), 1)
        self.assertIn("routeDeals: 8", rendered)
        self.assertIn("salesRate: 8 / 18", rendered)
        self.assertIn("matches the current-session conversion (7/13)", rendered)
        self.assertNotIn("Latest Slack-posted Total Route Conversion: 54.0%.", rendered)

    def test_final_without_explicit_team_falls_back_to_channel_team(self):
        body = "Tulsa, OK Final Numbers Total Reg: 100 Total Head Count: 10 Total Deals: 3"
        self.assertEqual(module.preview_team_from_final(body, "teamdent"), "Team Dent")


    def test_uppercase_final_numbers_closes_route_and_wins_over_partial_sessions(self):
        messages = [
            msg(
                "teamwayne",
                "2026-08-12T12:17:26-06:00",
                (
                    "Raleigh, NC | Monday 8/12/26 | Day 5 Session 1 | "
                    "Total Reg: 21 Total Count: 5 Session Deals: 5 "
                    "Master Class: (Megan): 28 Total Route Conversion: 40.6%"
                ),
            ),
            msg(
                "teamwayne",
                "2026-08-12T18:44:16-06:00",
                (
                    "Raleigh, NC | Team Wayne | WK 30 FINAL NUMBERS: | "
                    "Total Reg: 888 Total Head Count: 93 Total Late Arrivals: 24 "
                    "Total Attendees: 117 Total Deals: 35 Futures: 0"
                ),
            ),
            final("teammillar", "2026-08-12T20:55:01-06:00", "Boise, Idaho", "Team Millar", 460, 106, 14, 37),
            final("teamvogel", "2026-08-12T18:31:35-06:00", "Ann Arbor", "Team Vogel", 1421, 131, 27, 53),
        ]

        active_rows, _session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        final_rows, _latest = module.parse_preview(messages, [])
        sold = module.preview_sold_sources(messages)

        self.assertEqual(active_rows, [])
        self.assertEqual(len(final_rows), 3)
        raleigh = next(row for row in final_rows if "market: 'Raleigh, NC'" in row)
        self.assertIn("registered: 888", raleigh)
        self.assertIn("attendedCutoff: 93", raleigh)
        self.assertIn("sales: 35", raleigh)
        self.assertEqual(sold["raleigh"]["sold"], 35)


    def test_final_card_separates_master_class_sold_from_route_deals_and_futures(self):
        messages = [
            msg(
                "teammillar",
                "2026-08-12T20:55:01-06:00",
                (
                    "Boise, Idaho | Day 5 Session 2 RESULTS Session Futures: 1 "
                    "Master Class: (Nick): 31 ::::FINAL ROUTE NUMBERS::: "
                    "WK. 32 | FINAL NUMBERS Boise, Idaho | Preview Wednesday, 08/12/2026 "
                    "Total Reg: 460 Total Head Count: 106 Total Late Arrivals: 5 "
                    "Total Attendees: 111 Total Deals: 37 Futures: 6"
                ),
            ),
            final("teamwayne", "2026-08-12T18:44:16-06:00", "Raleigh", "Team Wayne", 888, 93, 24, 35),
            final("teamvogel", "2026-08-12T18:31:35-06:00", "Ann Arbor", "Team Vogel", 1421, 131, 27, 53),
        ]

        final_rows, _latest = module.parse_preview(messages, [])
        boise = next(row for row in final_rows if "market: 'Boise, Idaho'" in row)

        self.assertIn("sales: 31", boise)
        self.assertIn("routeDeals: 37", boise)
        self.assertIn("salesRate: 37 / 106", boise)
        self.assertIn("6 futures", boise)

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

    def test_recent_market_cards_keep_active_run_and_immediately_previous_run_only(self):
        candidates = [
            ("2026-07-29T20:00:00-06:00", "teammillar", "chicago", "2026-07-25", "CURRENT CHICAGO"),
            ("2026-07-15T20:43:00-06:00", "teamvogel", "hartford", "2026-07-12", "PRIOR HARTFORD"),
            ("2026-07-15T20:26:00-06:00", "teamwayne", "memphis", "2026-07-12", "PRIOR MEMPHIS"),
            ("2026-07-11T14:27:00-06:00", "teamwayne", "nashville", "2026-07-08", "OLD NASHVILLE"),
            ("2026-02-19T20:00:00-07:00", "teamvogel", "jacksonville", "2026-02-15", "OLD JACKSONVILLE"),
            ("2026-02-12T20:00:00-07:00", "teamwayne", "orlando", "2026-02-08", "OLD ORLANDO"),
        ]

        selected = module.select_recent_final_candidates(candidates, ["2026-07-25"])
        rendered = "\n".join(row[4] for row in selected)

        self.assertIn("CURRENT CHICAGO", rendered)
        self.assertIn("PRIOR HARTFORD", rendered)
        self.assertIn("PRIOR MEMPHIS", rendered)
        self.assertNotIn("OLD NASHVILLE", rendered)
        self.assertNotIn("OLD JACKSONVILLE", rendered)
        self.assertNotIn("OLD ORLANDO", rendered)

    def test_state_variant_uses_full_schedule_session_denominator(self):
        schedule = [
            {
                "market": "Indianapolis",
                "eventType": "front_end_preview",
                "state": state,
                "startDate": date,
                "times": times,
            }
            for date, times, state in (
                ("2026-07-25", "10:00AM & 2:00PM", "historical"),
                ("2026-07-26", "10:00AM & 2:00PM", "historical"),
                ("2026-07-27", "12:30PM (Only)", "historical"),
                ("2026-07-27", "7:00PM (Only)", "historical"),
                ("2026-07-28", "12:30PM & 7:00PM", "active"),
                ("2026-07-29", "12:30PM (Only)", "upcoming"),
                ("2026-07-29", "7:00PM (Only)", "upcoming"),
            )
        ]

        self.assertEqual(
            module.schedule_total_for_market(schedule, "Indianapolis, IN", "2026-07-25"),
            10,
        )

    def test_team_millar_channel_is_rendered_as_chicago_active_route(self):
        messages = [
            msg(
                "teammillar",
                "2026-07-25T09:31:46-06:00",
                "Chicago | Saturday 7/25/26 | Day 1 Session 1 | Total Reg: 252 Total Head Count: 30",
            ),
            msg(
                "teammillar",
                "2026-07-25T11:01:27-06:00",
                "Chicago | Saturday 7/25/26 | Day 1 Session 1 | Session Deals: 9 Master Class: (Jay): 9 Total Route Conversion: 30.0%",
            ),
        ]
        schedule = [
            {
                "market": "Chicago",
                "eventType": "front_end_preview",
                "state": state,
                "startDate": date,
                "times": times,
            }
            for date, times, state in (
                ("2026-07-25", "10:00AM & 2:00PM", "historical"),
                ("2026-07-26", "10:00AM & 2:00PM", "historical"),
                ("2026-07-27", "12:30PM (Only)", "historical"),
                ("2026-07-27", "7:00PM (Only)", "historical"),
                ("2026-07-28", "12:30PM & 7:00PM", "active"),
                ("2026-07-29", "12:30PM (Only)", "upcoming"),
                ("2026-07-29", "7:00PM (Only)", "upcoming"),
            )
        ]

        rows, _sessions, _latest_post, _latest_date = module.parse_active_preview_rows(messages, schedule)
        rendered = "\n".join(rows)
        self.assertIn("market: 'Chicago'", rendered)
        self.assertIn("Team Millar · Speaker Jay / #teammillar", rendered)
        self.assertIn("sessionsCompleted: 1", rendered)
        self.assertIn("totalSessions: 10", rendered)

    def test_late_duplicate_session_label_binds_headcount_to_following_result(self):
        messages = [
            msg("teamwayne", "2026-08-01T08:31:27-06:00", "Grand Rapids | Saturday 8/1/26 | Day 1 Session 1 | Total Reg: 278 Total Head Count: 27"),
            msg("teamwayne", "2026-08-01T10:07:02-06:00", "Grand Rapids | Saturday 8/1/26 | Day 1 Session 1 | Session Deals: 8 Master Class: (Tony): 8 Total Route Conversion: 30%"),
            msg("teamwayne", "2026-08-01T12:31:53-06:00", "Grand Rapids | Saturday 8/1/26 | Day 1 Session 1 | Total Reg: 186 Total Head Count: 19"),
            msg("teamwayne", "2026-08-01T13:39:40-06:00", "Grand Rapids | Saturday 8/1/26 | Day 1 Session 2 | Session Deals: 7 Master Class: (Tony): 15 Total Route Conversion: 32.6%"),
        ]

        rows, session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        rendered = "\n".join(rows)
        sessions = "\n".join(session_rows)

        self.assertIn("sessionsCompleted: 2", rendered)
        self.assertIn("routeDeals: 15", rendered)
        self.assertEqual(sessions.count("market: 'Grand Rapids'"), 2)
        self.assertIn("session: 'Day 1 Session 2'", sessions)
        self.assertIn("attendance: 19", sessions)

    def test_result_posted_before_headcount_keeps_deals_on_the_same_session(self):
        # Little Rock 2026-08-15: Team Wayne posted the Day 1 Session 2 result
        # 61 seconds BEFORE its headcount. Treating that trailing headcount as a
        # mislabeled next session stranded the session's 6 deals in a
        # registered==0 row, dropping whole-route deals to 24 against a
        # cumulative Master Class of 28 and blocking every downstream refresh.
        messages = [
            msg("teamwayne", "2026-08-15T09:31:14-06:00", "Little Rock | Saturday 8/15/26 | Day 1 Session 1 | Total Reg: 273 Total Head Count: 39"),
            msg("teamwayne", "2026-08-15T10:54:50-06:00", "Little Rock | Saturday 8/15/26 | Day 1 Session 1 | Session Deals: 8 Master Class: (Nick): 8 Total Route Conversion: 20.5%"),
            msg("teamwayne", "2026-08-15T14:37:22-06:00", "Little Rock | Saturday 8/15/26 | Day 1 Session 2 | Session Deals: 6 Master Class: (Nick): 14 Total Route Conversion: 25%"),
            msg("teamwayne", "2026-08-15T14:38:23-06:00", "Little Rock | Saturday 8/15/26 | Day 1 Session 2 | Total Reg: 152 Total Head Count: 17"),
            msg("teamwayne", "2026-08-16T09:33:52-06:00", "Little Rock | Sunday 8/16/26 | Day 2 Session 1 | Total Reg: 124 Total Head Count: 19"),
            msg("teamwayne", "2026-08-16T10:56:00-06:00", "Little Rock | Sunday 8/16/26 | Day 2 Session 1 | Session Deals: 6 Master Class: (Nick): 19 Total Route Conversion: 26.7%"),
            msg("teamwayne", "2026-08-16T13:29:28-06:00", "Little Rock | Sunday 8/16/26 | Day 2 Session 2 | Total Reg: 184 Total Head Count: 30"),
            msg("teamwayne", "2026-08-16T14:46:05-06:00", "Little Rock | Sunday 8/16/26 | Day 2 Session 2 | Session Deals: 10 Master Class: (Nick): 28 Total Route Conversion: 28.6%"),
        ]

        rows, session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        rendered = "\n".join(rows)
        sessions = "\n".join(session_rows)

        self.assertEqual(len(rows), 1)
        self.assertIn("market: 'Little Rock'", rendered)
        self.assertIn("sessionsCompleted: 4", rendered)
        self.assertIn("routeDeals: 30", rendered)
        self.assertIn("sales: 28", rendered)
        # 30 route deals over the 105 completed-session attendees reproduces the
        # team's own posted 28.6% Total Route Conversion; 24 deals would be 22.9%.
        self.assertIn("salesRate: 28.6 / 100", rendered)
        self.assertEqual(sessions.count("market: 'Little Rock'"), 4)
        self.assertIn("session: 'Day 1 Session 2'", sessions)
        self.assertIn("attendance: 17", sessions)

    def test_team_millar_final_two_chicago_sessions_are_attributed_to_lura(self):
        messages = [
            msg(
                "teammillar",
                "2026-07-29T13:04:55-06:00",
                "Chicago | Tuesday 7/29/26 | Day 5 Session 1 | Total Reg: 266 Total Head Count: 26",
            ),
            msg(
                "teammillar",
                "2026-07-29T14:00:00-06:00",
                "Chicago | Tuesday 7/29/26 | Day 5 Session 1 | Session Deals: 7 Master Class: (Jay): 69 Total Route Conversion: 31%",
            ),
            msg(
                "teammillar",
                "2026-07-29T18:33:27-06:00",
                "Chicago | Tuesday 7/29/26 | Day 5 Session 2 | Total Reg: 370 Total Head Count: 48",
            ),
            msg(
                "teammillar",
                "2026-07-29T19:30:00-06:00",
                "Chicago | Tuesday 7/29/26 | Day 5 Session 2 | Session Deals: 20 Master Class: (Jay): 89 Total Route Conversion: 33%",
            ),
            final("teammillar", "2026-07-29T20:31:38-06:00", "Chicago", "Team Millar", 2508, 249, 18, 89),
            result("teamvogel", "2026-07-15T19:32:00-06:00", "Hartford", "Wednesday 7/15/26", "Tony", 55),
            final("teamvogel", "2026-07-15T20:43:00-06:00", "Hartford", "Team Vogel", 1233, 137, 23, 58),
            result("teamwayne", "2026-07-15T20:23:00-06:00", "Memphis", "Wednesday 7/15/26", "Jay", 82),
            final("teamwayne", "2026-07-15T20:26:00-06:00", "Memphis", "Team Gray", 1745, 235, 22, 85),
        ]

        _active, session_rows, _latest_post, _latest_date = module.parse_active_preview_rows(messages, [])
        sessions = "\n".join(session_rows)
        final_rows, _latest = module.parse_preview(messages, [])
        final_rendered = "\n".join(final_rows)

        self.assertEqual(sessions.count("speaker: 'Lura'"), 2)
        self.assertNotIn("speaker: 'Jay'", sessions)
        self.assertIn("Team Millar · Speaker Lura / #teammillar", final_rendered)
        self.assertIn("final two Chicago sessions", final_rendered)
        self.assertIn("cumulative Master Class label remained Jay", final_rendered)


if __name__ == "__main__":
    unittest.main()
