#!/usr/bin/env python3
"""Regression tests for Slack ME/workshop A/B/C buyer-mix extraction."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "update_tlwb_slack_operational_sections.py"
SPEC = importlib.util.spec_from_file_location("tlwb_slack_updater_abc", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class WorkshopAbcParserTests(unittest.TestCase):
    def test_extracts_market_from_dated_workflow_bot_field(self) -> None:
        body = (
            "<@U02P1N1EAF5> submitted Event Stats. | "
            "*Market:* 7.24-26.26 Long Island ME Tony | Mariott Melville | 7.24-26.26 | "
            "*BU’s:* 54 | *Total Sales:* 27 | *Written:* $348,100.00 | *Collected:* $199,350.00"
        )
        self.assertEqual(module.market_from_me(body), "Long Island")

    def test_extracts_current_slack_mrkdwn_abc_mix(self) -> None:
        body = (
            "*Market:* Phoenix, AZ | *BU’s:* 33 | *Total Sales:* 21 | "
            "*WS Buyers Sold:*  | *A:* 8/6 = 75% | *B:* 5/5 = 100% | "
            "*C:* 19/10 = 53% | *Legacy Pro:* 5"
        )
        self.assertEqual(
            module.parse_me_abc(body),
            "A: 8 buyers · 6 sold (75%) · B: 5 buyers · 5 sold (100%) · C: 19 buyers · 10 sold (53%)",
        )

    def test_preserves_count_only_sold_grade(self) -> None:
        body = (
            "*Market:* Tulsa Oklahoma | *BU’s:* 16 | *Total Sales:* 7 | "
            "*WS Buyers Sold:* | *A:* 2 | *B:* 0 | *C:* 5 | *Legacy Pro:* 1"
        )
        self.assertEqual(
            module.parse_me_abc(body),
            "A: 2 sold · B: 0 sold · C: 5 sold",
        )

    def test_preserves_inconsistent_reported_ratio_with_semantics(self) -> None:
        body = (
            "*Market:* Memphis, TN | *BU’s:* 77 | *Total Sales:* 24 | "
            "*WS Buyers Sold:* | *A:* 4/7 = 57% | *B:* 4/8 = 50% | "
            "*C:* 16/57 = 26% | *Legacy Pro:* 2"
        )
        self.assertEqual(
            module.parse_me_abc(body),
            "A: 7 buyers · 4 sold (57%) · B: 8 buyers · 4 sold (50%) · C: 57 buyers · 16 sold (26% as reported)",
        )

    def test_returns_none_when_final_has_no_buyer_mix(self) -> None:
        self.assertIsNone(module.parse_me_abc("Market: Test | BU's: 10 | Total Sales: 2"))

    def test_extracts_abc_mix_when_workflow_bot_omits_equals_sign(self) -> None:
        body = (
            "*Market:* 7.24-26.26 Long Island ME Tony | *BU’s:* 54 | *Total Sales:* 27 | "
            "*WS Buyers Sold:* | *A:* 3/4 75% | *B:* 3/5 60% | *C:* 21/44 48% | *Legacy Pro:* 3"
        )
        self.assertEqual(
            module.parse_me_abc(body),
            "A: 4 buyers · 3 sold (75%) · B: 5 buyers · 3 sold (60%) · C: 44 buyers · 21 sold (48%)",
        )


if __name__ == "__main__":
    unittest.main()
