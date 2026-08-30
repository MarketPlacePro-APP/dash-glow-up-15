#!/usr/bin/env python3
"""Generate current static freshness artifacts from the headless CI Slack probe.

The canonical Studio freshness spine also archives into the local SQLite warehouse.
GitHub's Phase 1 runner has no durable warehouse yet, so this adapter reuses the
canonical health/audit builders while writing only the static artifacts that the
predeploy gate and dashboard consume. Warehouse cutover remains a separate gate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
SPINE_PATH = APP_ROOT / "scripts" / "phase1_freshness_spine.py"


def load_spine():
    spec = importlib.util.spec_from_file_location("phase1_freshness_spine_ci", SPINE_PATH)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load canonical freshness spine: {SPINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.status.read_text(encoding="utf-8"))
    outcomes = payload.get("channels") or {}
    spine = load_spine()

    for channel in spine.REQUIRED_CHANNELS:
        outcomes.setdefault(channel, {
            "channel": channel,
            "required": True,
            "status": "failed",
            "rows_seen": 0,
            "new_rows_since_last_check": 0,
            "latest_source_post_date": None,
            "notes": "Required channel missing from CI probe output.",
        })
    for channel in spine.OPTIONAL_CHANNELS:
        outcomes.setdefault(channel, {
            "channel": channel,
            "required": False,
            "status": "not_in_channel",
            "rows_seen": 0,
            "new_rows_since_last_check": 0,
            "latest_source_post_date": None,
            "notes": "Optional channel is not visible to the CI bot; non-blocking.",
        })

    schedule = json.loads(spine.SCHEDULE_JSON.read_text(encoding="utf-8"))
    if schedule.get("source", {}).get("source_id") != "upcoming_schedule":
        raise RuntimeError("Schedule artifact does not name upcoming_schedule as source")
    if not schedule.get("records") or not schedule.get("route_blocks"):
        raise RuntimeError("Schedule artifact is empty")

    health = spine.build_source_health(schedule, outcomes)
    spine.write_source_health(health)
    audit = spine.build_phase2a_audit(schedule, health)
    spine.PHASE2A_AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    spine.PHASE2A_AUDIT_JSON.write_text(
        json.dumps(audit, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    red = [row for row in health["rows"] if row.get("status") == "red"]
    print(json.dumps({
        "generated_at": health.get("generated_at"),
        "health_rows": len(health.get("rows") or []),
        "red_rows": len(red),
        "phase2a_event_roster": audit["counts"]["event_roster"],
        "phase2a_metric_rows": audit["counts"]["metric_rows"],
        "warehouse_write": "deferred_phase_2",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())