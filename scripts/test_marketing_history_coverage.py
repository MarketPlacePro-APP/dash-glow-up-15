#!/usr/bin/env python3
"""Require Marketing comparable-history keys for every current market card."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
adapter = (ROOT / "src/data/executiveAdapters.ts").read_text(encoding="utf-8")
history_text = (ROOT / "src/data/masterTrackerMarketing.ts").read_text(encoding="utf-8")

marker = "export const activeMarketingMarkets: ActiveMarketingMarket[] = ["
active_block = adapter.split(marker, 1)[1].split("];", 1)[0]
active = list(dict.fromkeys(re.findall(r"market:\s*'([^']+)'", active_block)))

history_json = history_text.split("= ", 1)[1].split(" as Record<", 1)[0].strip()
history = json.loads(history_json)

missing = [market for market in active if market not in history]
if missing:
    raise SystemExit(f"Marketing comparable-history keys missing for current markets: {missing}")
if "Portland" not in active:
    raise SystemExit("Portland missing from current Marketing roster")
if not history.get("Portland"):
    raise SystemExit("Portland comparable history is empty despite completed Master Tracker runs")
if len(history["Portland"]) > 3:
    raise SystemExit("Portland comparable history exceeded the three-run UI contract")

print(f"OK: comparable history covers {len(active)} current markets; Portland runs={len(history['Portland'])}")
