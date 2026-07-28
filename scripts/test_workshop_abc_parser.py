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

    def test_preserves_reported_zero_grade(self) -> None:
        body = (
            "*Market:* Birmingham, AL | *BU’s:* 39 | *Total Sales:* 16 | "
            "*WS Buyers Sold:*  | *A:* 0 | *B:* 3/5 = 60% | "
            "*C:* 13/31 = 42% | *Legacy Pro:* 0"
        )
        self.assertEqual(
            module.parse_me_abc(body),
            "A: 0 buyers · B: 5 buyers · 3 sold (60%) · C: 31 buyers · 13 sold (42%)",
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
