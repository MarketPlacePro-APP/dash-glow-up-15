#!/usr/bin/env python3
"""Generate a sanitized, same-batch Analytics Brain artifact for the TLWB dashboard.

This script never opens the authenticated browser profile or Keychain. It reads only
CSV exports and the secret-safe overnight audit record, then writes a client-safe
JSON snapshot into the dashboard source tree.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

EXPORT_ROOT = Path(os.environ.get(
    "TLWB_ANALYTICS_BRAIN_EXPORT_ROOT",
    "/Users/seanwilliams/.hermes/profiles/harlow/data/analytics_brain/exports",
))
AUDIT_ROOT = Path(os.environ.get(
    "TLWB_ANALYTICS_BRAIN_AUDIT_ROOT",
    "/Users/seanwilliams/.hermes/profiles/harlow/data/analytics_brain/overnight_runs",
))
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "src/data/analyticsBrain.generated.json"
REQUIRED_REPORTS = {"event-summary": 8, "ad-channel": 6, "campaign-ads": 3}
EXCLUDED_REPORTS = [
    "TU Reporting",
    "TU Scoring by Channel",
    "TU Scoring by Campaign, Ad Set, Ad Name",
]
EXPECTED_HEADERS = {
    "eventSummary": [
        "Market Name", "Market Date", "Market Group", "Spend", "Registrations", "Guests",
        "Cost per Registration", "Attendance", "Show Rate", "Cost per Attendee", "Buyers",
        "Cost per Buyer", "Net FE Revenue", "FE ROM", "Gross ME Revenue", "Net ME Revenue",
        "FE+ME ROM", "::auto_unique_id::",
    ],
    "channels": [
        "Channel", "Total Cost", "% of Cost", "Registrations", "% of Regs",
        "Cost per Registration", "Attended", "Show Rate", "Cost per Attendee", "Buyers",
        "Cost per Buyer", "Buy Rate", "Net FE Revenue", "FE Sales per Head", "FE ROM",
        "Gross ME Revenue", "Net ME Revenue", "FE+ME ROM", "::auto_unique_id::",
    ],
    "campaigns": [
        "Channel", "Campaign", "Total Cost", "% of Cost", "Registrations", "% of Regs",
        "Cost per Registration", "Attended", "Show Rate", "Cost per Attendee", "Buyers",
        "Cost per Buyer", "Buy Rate", "Net FE Revenue", "FE Sales per Head", "FE ROM",
        "Gross ME Revenue", "Net ME Revenue", "FE+ME ROM", "::auto_unique_id::",
    ],
    "adSets": [
        "Channel", "Ad Set", "Total Cost", "% of Cost", "Registrations", "% of Regs",
        "Cost per Registration", "Attended", "Show Rate", "Cost per Attendee", "Buyers",
        "Cost per Buyer", "Buy Rate", "Net FE Revenue", "FE Sales per Head", "FE ROM",
        "Gross ME Revenue", "Net ME Revenue", "FE+ME ROM", "::auto_unique_id::",
    ],
    "ads": [
        "Channel", "Ad Name", "Total Cost", "% of Cost", "Registrations", "% of Regs",
        "Cost per Registration", "Attended", "Show Rate", "Cost per Attendee", "Buyers",
        "Cost per Buyer", "Buy Rate", "Net FE Revenue", "FE Sales per Head", "FE ROM",
        "Gross ME Revenue", "Net ME Revenue", "FE+ME ROM", "::auto_unique_id::",
    ],
}
KEY_FIELDS = {
    "eventSummary": ["Market Group"],
    "channels": ["Channel"],
    "campaigns": ["Channel", "Campaign"],
    "adSets": ["Channel", "Ad Set"],
    "ads": ["Channel", "Ad Name"],
}
NUMERIC_FIELDS = {
    "eventSummary": [
        "Spend", "Registrations", "Guests", "Cost per Registration", "Attendance", "Show Rate",
        "Cost per Attendee", "Buyers", "Cost per Buyer", "Net FE Revenue", "FE ROM",
        "Gross ME Revenue", "Net ME Revenue", "FE+ME ROM",
    ],
    "performance": [
        "Total Cost", "% of Cost", "Registrations", "% of Regs", "Cost per Registration",
        "Attended", "Show Rate", "Cost per Attendee", "Buyers", "Cost per Buyer", "Buy Rate",
        "Net FE Revenue", "FE Sales per Head", "FE ROM", "Gross ME Revenue", "Net ME Revenue",
        "FE+ME ROM",
    ],
}
RATIO_FIELDS = {"Show Rate", "Buy Rate", "% of Cost", "% of Regs"}
SENSITIVE_HEADER = re.compile(r"(?:password|passwd|cookie|authorization|secret|keychain|_dl_token|access[_ -]?token)", re.I)


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"-", "—", "n/a", "na", "null", "none"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.replace("$", "").replace(",", "").replace("%", "").strip("() ")
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return -number if negative else number


def parse_market_date(value: str) -> str | None:
    try:
        return datetime.strptime(value.strip(), "%b %d, %Y").date().isoformat()
    except (TypeError, ValueError):
        return None


def latest_complete_audit() -> tuple[Path, dict[str, Any]]:
    for path in sorted(AUDIT_ROOT.glob("*.json"), reverse=True):
        payload = json.loads(path.read_text())
        reports = {row.get("report"): row for row in payload.get("reports", [])}
        complete = (
            not payload.get("error")
            and all(reports.get(name, {}).get("status") == "ok" for name in REQUIRED_REPORTS)
            and all(reports.get(name, {}).get("csv_count") == count for name, count in REQUIRED_REPORTS.items())
        )
        if complete:
            return path, payload
    raise RuntimeError("No complete authenticated Analytics Brain audit batch is available")


def select_batch_files(audit: dict[str, Any]) -> list[Path]:
    started = datetime.fromisoformat(audit["started_at"]).timestamp() - 1
    finished = datetime.fromisoformat(audit["finished_at"]).timestamp() + 1
    output_dirs = {Path(row["output_dir"]) for row in audit["reports"]}
    if len(output_dirs) != 1:
        raise RuntimeError("Complete audit references inconsistent export directories")
    output_dir = output_dirs.pop()
    selected = [path for path in output_dir.glob("*.csv") if started <= path.stat().st_mtime <= finished]
    counts = {name: sum(path.name.startswith(f"{name}-") for path in selected) for name in REQUIRED_REPORTS}
    if counts != REQUIRED_REPORTS:
        raise RuntimeError(f"Same-batch file counts do not match the audit: {counts}")
    return sorted(selected, key=lambda path: (path.stat().st_mtime, path.name))


def locate(selected: list[Path], prefix: str) -> Path:
    matches = [path for path in selected if path.name.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one same-batch file for {prefix}; found {len(matches)}")
    return matches[0]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader if any(str(value or "").strip() for value in row.values())]
    if any(SENSITIVE_HEADER.search(header) for header in headers):
        raise RuntimeError(f"Sensitive-looking header detected in sanitized input: {path.name}")
    return headers, rows


def qa_dimension(name: str, headers: list[str], rows: list[dict[str, str]]) -> dict[str, Any]:
    key_fields = KEY_FIELDS[name]
    numeric_fields = NUMERIC_FIELDS["eventSummary" if name == "eventSummary" else "performance"]
    seen: set[tuple[str, ...]] = set()
    duplicate_keys: list[str] = []
    empty_keys: list[int] = []
    numeric_errors: list[dict[str, Any]] = []
    impossible_ratios: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=2):
        key = tuple((row.get(field) or "").strip() for field in key_fields)
        if any(not part for part in key):
            empty_keys.append(index)
        key_label = " · ".join(key)
        if key in seen:
            duplicate_keys.append(key_label)
        seen.add(key)
        for field in numeric_fields:
            raw = (row.get(field) or "").strip()
            parsed = parse_number(raw)
            if raw and raw.lower() not in {"-", "—", "n/a", "na", "null", "none"} and parsed is None:
                numeric_errors.append({"row": index, "key": key_label, "field": field, "value": raw})
            if field in RATIO_FIELDS and parsed is not None and parsed > 100:
                impossible_ratios.append({"row": index, "key": key_label, "field": field, "sourceValue": raw})
    return {
        "headerValid": headers == EXPECTED_HEADERS[name],
        "headers": headers,
        "rowCount": len(rows),
        "duplicateKeys": duplicate_keys,
        "emptyKeyRows": empty_keys,
        "numericParseErrors": numeric_errors,
        "impossibleRatios": impossible_ratios,
    }


def sum_field(rows: list[dict[str, str]], field: str) -> float:
    return sum(parse_number(row.get(field)) or 0 for row in rows)


def aggregates(name: str, rows: list[dict[str, str]]) -> dict[str, float]:
    event = name == "eventSummary"
    return {
        "spend": sum_field(rows, "Spend" if event else "Total Cost"),
        "registrations": sum_field(rows, "Registrations"),
        "attended": sum_field(rows, "Attendance" if event else "Attended"),
        "buyers": sum_field(rows, "Buyers"),
        "netFeRevenue": sum_field(rows, "Net FE Revenue"),
        "grossMeRevenue": sum_field(rows, "Gross ME Revenue"),
        "netMeRevenue": sum_field(rows, "Net ME Revenue"),
    }


def main(output: Path = DEFAULT_OUTPUT) -> None:
    audit_path, audit = latest_complete_audit()
    selected = select_batch_files(audit)
    files = {
        "eventSummary": locate(selected, "event-summary-1-"),
        "channels": locate(selected, "ad-channel-1-"),
        "campaigns": locate(selected, "campaign-ads-1-"),
        "adSets": locate(selected, "campaign-ads-2-"),
        "ads": locate(selected, "campaign-ads-3-"),
    }
    headers: dict[str, list[str]] = {}
    rows: dict[str, list[dict[str, str]]] = {}
    dimension_qa: dict[str, dict[str, Any]] = {}
    for name, path in files.items():
        headers[name], rows[name] = read_csv(path)
        dimension_qa[name] = qa_dimension(name, headers[name], rows[name])

    event_dates = [parse_market_date(row.get("Market Date", "")) for row in rows["eventSummary"]]
    valid_event_dates = sorted(value for value in event_dates if value)
    totals = {name: aggregates(name, dimension_rows) for name, dimension_rows in rows.items()}
    compared = [totals[name] for name in ("eventSummary", "channels", "campaigns", "adSets", "ads")]
    reconciliation: dict[str, dict[str, Any]] = {}
    for metric in compared[0]:
        values = [row[metric] for row in compared]
        spread = max(values) - min(values)
        tolerance = max(5.0 if metric == "spend" else 0.0, max(values) * 0.00001)
        reconciliation[metric] = {
            "values": dict(zip(("eventSummary", "channels", "campaigns", "adSets", "ads"), values)),
            "spread": spread,
            "tolerance": tolerance,
            "withinTolerance": spread <= tolerance,
        }

    all_impossible = [
        {"dimension": name, **issue}
        for name, result in dimension_qa.items()
        for issue in result["impossibleRatios"]
    ]
    all_numeric_errors = [
        {"dimension": name, **issue}
        for name, result in dimension_qa.items()
        for issue in result["numericParseErrors"]
    ]
    required_ok = all(
        dimension_qa[name]["headerValid"]
        and not dimension_qa[name]["duplicateKeys"]
        and not dimension_qa[name]["emptyKeyRows"]
        for name in ("eventSummary", "channels", "campaigns", "adSets")
    )
    reconciliation_ok = all(row["withinTolerance"] for row in reconciliation.values())
    decision_status = "source-refreshed / discrepancy open" if all_impossible or not reconciliation_ok else "decision-ready"

    payload = {
        "version": 1,
        "batchToken": audit_path.stem,
        "decisionStatus": decision_status,
        "source": {
            "name": "Analytics Brain",
            "portal": "TLWB portal",
            "reportUrl": "https://lite.analyticsbrain.ai/?portal=tlwb",
            "accountLabel": "TLWB single-user portal account (operator-held)",
            "producer": "Harlow/Hermes export pipeline",
            "operator": "Owner of the live Analytics Brain account",
            "sourceAsOf": None,
            "sourceAsOfLabel": "Not supplied by export",
            "reportingWindowStart": valid_event_dates[0] if valid_event_dates else None,
            "reportingWindowEnd": valid_event_dates[-1] if valid_event_dates else None,
            "exportedAt": audit["finished_at"],
            "auditStartedAt": audit["started_at"],
            "auditMode": audit.get("mode"),
            "authenticatedExport": True,
            "batchBound": True,
        },
        "reports": {
            "eventSummary": "TLWB | Event Summary Report",
            "channels": "TLWB | Report by Ad Channel",
            "campaigns": "TLWB | Report by Campaign and Ads — Campaign",
            "adSets": "TLWB | Report by Campaign and Ads — Ad Set",
            "ads": "TLWB | Report by Campaign and Ads — Ad Name",
            "excluded": EXCLUDED_REPORTS,
        },
        "files": {name: path.name for name, path in files.items()},
        "batchFiles": [path.name for path in selected],
        "rows": rows,
        "qa": {
            "requiredDimensionsPresent": required_ok,
            "optionalAdNamePresent": bool(rows["ads"]) and dimension_qa["ads"]["headerValid"],
            "sameBatch": True,
            "sourceSnapshotProvided": False,
            "dimensions": dimension_qa,
            "aggregates": totals,
            "reconciliation": reconciliation,
            "reconciliationPassed": reconciliation_ok,
            "numericParseErrors": all_numeric_errors,
            "impossibleRatios": all_impossible,
            "zeroBlankRule": "Zero is preserved; blank/invalid values normalize to null.",
            "smallSampleThreshold": 100,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({
        "output": str(output),
        "batchToken": payload["batchToken"],
        "decisionStatus": decision_status,
        "rows": {name: len(value) for name, value in rows.items()},
        "impossibleRatios": len(all_impossible),
        "reconciliationPassed": reconciliation_ok,
    }, indent=2))


if __name__ == "__main__":
    main()
