#!/usr/bin/env python3
"""Generate dashboard Marketing comparable rows from the live TLWB Master Tracker export."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTOR = ROOT / "scripts/tlwb_master_tracker_extract.py"
OUT = ROOT / "dash-glow-up-15/src/data/masterTrackerMarketing.ts"
ADAPTER = ROOT / "dash-glow-up-15/src/data/executiveAdapters.ts"

spec = importlib.util.spec_from_file_location("tlwb_master_tracker_extract", EXTRACTOR)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[union-attr]

CHANNEL_SHEETS = {
    "Facebook": "FB YTD",
    "YouTube": "YouTube YTD",
    "TikTok": "TikTok YTD",
    "Radio": "Radio YTD",
    "TV": "TV YTD",
}


def same_run(a, b):
    return a.get("date") == b.get("date") and a.get("market") == b.get("market")


def money(v):
    return round(float(v or 0), 2)


def active_marketing_names() -> list[str]:
    """Read the freshly generated current market roster from the Slack adapter."""
    text = ADAPTER.read_text(encoding="utf-8")
    marker = "export const activeMarketingMarkets: ActiveMarketingMarket[] = ["
    try:
        block = text.split(marker, 1)[1].split("];", 1)[0]
    except IndexError as exc:
        raise SystemExit("Could not locate activeMarketingMarkets in executiveAdapters.ts") from exc
    names = list(dict.fromkeys(re.findall(r"market:\s*'([^']+)'", block)))
    if not names:
        raise SystemExit("No active marketing markets found; refusing to generate empty comparable history")
    return names


def search_terms(display: str) -> list[str]:
    terms = [display]
    punctuation_free = re.sub(r"[^A-Za-z0-9 ]+", "", display)
    if punctuation_free and punctuation_free != display:
        terms.append(punctuation_free)
    return terms


def main():
    mod.download()
    wb = mod.Workbook(mod.XLSX)
    all_recs = mod.all_rows(wb)
    channel_recs = {label: mod.channel_rows(wb, sheet) for label, sheet in CHANNEL_SHEETS.items()}
    history = {}
    for display in active_marketing_names():
        rows = mod.latest_matches(all_recs, search_terms(display), 3, require_completed=True)
        runs = []
        for row in rows:
            channels = []
            for label, recs in channel_recs.items():
                match = next((r for r in recs if same_run(row, r)), None)
                if not match:
                    continue
                if match["registered"] <= 0 and match["spend"] <= 0 and match["buyers"] <= 0:
                    continue
                channels.append({
                    "channel": label,
                    "registrations": match["registered"],
                    "attended": match["attended"],
                    "buyers": match["buyers"],
                    "spend": money(match["spend"]),
                    "cpr": money(match["spend"] / match["registered"]) if match["registered"] else None,
                })
            total_spend = money(sum(c["spend"] for c in channels))
            channels.append({
                "channel": "Total",
                "registrations": row["totalRegistered"],
                "attended": row["totalAttended"],
                "buyers": row["totalBuyers"],
                "spend": total_spend,
                "cpr": money(total_spend / row["totalRegistered"]) if row["totalRegistered"] else None,
            })
            runs.append({
                "market": row["market"],
                "eventDate": row["date"],
                "registrations": row["totalRegistered"],
                "attended": row["totalAttended"],
                "sold": row["totalBuyers"],
                "spend": total_spend,
                "cpr": money(total_spend / row["totalRegistered"]) if row["totalRegistered"] else None,
                "channels": channels,
                "notes": "Live TLWB Master Tracker export",
            })
        history[display] = runs
    OUT.write_text(
        "import type { MarketingHistoryRun } from './tlwbPageAdapters';\n\n"
        "// Generated from live TLWB Master Tracker (1miRUadPo0WsB9tAZ2XgJ3xgyV3CY0Z4xGUNd8eRY4EU).\n"
        "// Regenerate with: scripts/generate_master_tracker_marketing_ts.py\n"
        "export const masterTrackerMarketingHistory: Record<string, MarketingHistoryRun[]> = "
        + json.dumps(history, indent=2)
        + " as Record<string, MarketingHistoryRun[]>;\n"
    )
    print(f"wrote {OUT}")
    print({k: len(v) for k, v in history.items()})


if __name__ == "__main__":
    main()
