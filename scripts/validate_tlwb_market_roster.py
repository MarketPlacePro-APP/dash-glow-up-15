#!/usr/bin/env python3
"""Fail closed when a current market drops between source and dashboard surfaces."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def load_updater(src: Path):
    path = src / "scripts/update_tlwb_slack_operational_sections.py"
    spec = importlib.util.spec_from_file_location("tlwb_slack_market_gate", path)
    if not spec or not spec.loader:
        raise SystemExit(f"Could not load Slack updater: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ts_markets(text: str, marker: str) -> list[str]:
    try:
        block = text.split(marker, 1)[1].split("];", 1)[0]
    except IndexError as exc:
        raise SystemExit(f"Could not locate adapter block: {marker}") from exc
    return list(dict.fromkeys(re.findall(r"market:\s*'([^']+)'", block)))


def history_keys(text: str) -> set[str]:
    try:
        payload = text.split("= ", 1)[1].split(" as Record<", 1)[0].strip()
        parsed = json.loads(payload)
    except (IndexError, json.JSONDecodeError) as exc:
        raise SystemExit("Could not parse Marketing comparable-history artifact") from exc
    return set(parsed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--slack", type=Path, required=True)
    args = parser.parse_args()

    updater = load_updater(args.src)
    messages = updater.parse_messages(args.slack.read_text(encoding="utf-8", errors="replace"))
    facts = updater.current_marketing_facts(messages)
    if not facts:
        raise SystemExit("No current #eventstats market facts parsed")

    source_markets = [str(row["market"]) for row in facts]
    adapter_text = (args.src / "src/data/executiveAdapters.ts").read_text(encoding="utf-8")
    marketing_markets = ts_markets(adapter_text, "export const activeMarketingMarkets: ActiveMarketingMarket[] = [")
    preview_markets = ts_markets(adapter_text, "export const activePreviewMarkets: ActivePreviewMarket[] = [")
    history = history_keys((args.src / "src/data/masterTrackerMarketing.ts").read_text(encoding="utf-8"))

    source_keys = {updater.normalize_market_name(value): value for value in source_markets}
    marketing_keys = {updater.normalize_market_name(value): value for value in marketing_markets}
    preview_keys = {updater.normalize_market_name(value): value for value in preview_markets}
    history_keys_normalized = {updater.normalize_market_name(value): value for value in history}

    missing_marketing = sorted(source_keys[key] for key in source_keys.keys() - marketing_keys.keys())
    missing_preview = sorted(source_keys[key] for key in source_keys.keys() - preview_keys.keys())
    missing_history = sorted(source_keys[key] for key in source_keys.keys() - history_keys_normalized.keys())
    extra_marketing = sorted(marketing_keys[key] for key in marketing_keys.keys() - source_keys.keys())

    issues = []
    if missing_marketing:
        issues.append(f"Marketing dropped current source markets: {missing_marketing}")
    if missing_preview:
        issues.append(f"Preview dropped current source markets: {missing_preview}")
    if missing_history:
        issues.append(f"Marketing history omitted current market keys: {missing_history}")
    if extra_marketing:
        issues.append(f"Marketing contains markets outside the current source roster: {extra_marketing}")
    if len(source_keys) != len(source_markets):
        issues.append("Current #eventstats roster contains duplicate normalized markets")

    artifact = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source": str(args.slack),
        "source_market_count": len(source_markets),
        "source_markets": source_markets,
        "marketing_market_count": len(marketing_markets),
        "preview_market_count": len(preview_markets),
        "missing_marketing": missing_marketing,
        "missing_preview": missing_preview,
        "missing_history": missing_history,
        "extra_marketing": extra_marketing,
        "status": "failed" if issues else "ok",
        "issues": issues,
    }
    output = args.src / "data/market_roster_gate.json"
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    if issues:
        raise SystemExit("; ".join(issues))
    print(f"OK: market roster no-drop gate passed for {len(source_markets)} current markets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
