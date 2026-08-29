#!/usr/bin/env python3
"""Download and inspect the live TLWB Master Tracker Google Sheet.

Source: https://docs.google.com/spreadsheets/d/1miRUadPo0WsB9tAZ2XgJ3xgyV3CY0Z4xGUNd8eRY4EU/edit
No third-party deps; reads XLSX zip/XML directly.
"""
from __future__ import annotations

import json
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SHEET_ID = "1miRUadPo0WsB9tAZ2XgJ3xgyV3CY0Z4xGUNd8eRY4EU"
SOURCE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=0#gid=0"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data/google_exports/master_tracker_1miRU_latest.xlsx"
REPORT = ROOT / "reports/tlwb_master_tracker_live_extract_2026-05-06.md"
JSON_OUT = ROOT / "data/google_exports/master_tracker_1miRU_latest_summary.json"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

ACTIVE_COMPARABLES = ["Raleigh", "Tampa", "West Palm", "Minneapolis"]
ME_PIPELINE = ["Fort Lauderdale", "Long Island"]
PREVIEW_CHECKS = ["Atlanta", "Norfolk"]


def download() -> None:
    XLSX.parent.mkdir(parents=True, exist_ok=True)
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(key, None)
    os.environ.setdefault("NO_PROXY", "docs.google.com,*.google.com")
    req = Request(EXPORT_URL, headers={"User-Agent": "Mozilla/5.0 (OpenClaw TLWB KPI Refresh)"})
    try:
        with urlopen(req, timeout=45) as resp:
            XLSX.write_bytes(resp.read())
    except Exception as exc:
        if XLSX.exists():
            age_hours = (datetime.now(timezone.utc) - datetime.fromtimestamp(XLSX.stat().st_mtime, timezone.utc)).total_seconds() / 3600
            if age_hours <= 8:
                print(f"WARN: Master Tracker download failed; using cached XLSX age_hours={age_hours:.1f}: {type(exc).__name__}: {str(exc)[:180]}", file=sys.stderr)
                return
        raise


def colnum(ref: str) -> int:
    letters = "".join(c for c in ref if c.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def clean(v) -> str:
    return "" if v is None else str(v).strip()


def num(v, default=0.0):
    s = clean(v)
    if not s or s.startswith("#") or s in {"-", "—"}:
        return default
    try:
        return float(s.replace(",", "").replace("$", ""))
    except Exception:
        return default


def excel_date(v: str) -> str:
    try:
        n = float(v)
    except Exception:
        return clean(v)
    if n <= 30000 or n > 80000:
        return clean(v)
    return (datetime(1899, 12, 30) + timedelta(days=n)).date().isoformat()


class Workbook:
    def __init__(self, path: Path):
        self.z = zipfile.ZipFile(path)
        self.shared = []
        if "xl/sharedStrings.xml" in self.z.namelist():
            root = ET.fromstring(self.z.read("xl/sharedStrings.xml"))
            for si in root.findall(NS + "si"):
                self.shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
        wb = ET.fromstring(self.z.read("xl/workbook.xml"))
        rels = ET.fromstring(self.z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        self.sheets = {}
        for s in wb.find(NS + "sheets"):
            target = relmap[s.attrib[RNS + "id"]]
            target = "xl/" + target if target.startswith("worksheets/") else target.lstrip("/")
            self.sheets[s.attrib["name"]] = target

    def rows(self, sheet: str):
        root = ET.fromstring(self.z.read(self.sheets[sheet]))
        for row in root.iter(NS + "row"):
            vals = []
            last = -1
            for c in row.findall(NS + "c"):
                idx = colnum(c.attrib.get("r", "A1"))
                while last + 1 < idx:
                    vals.append("")
                    last += 1
                v = c.find(NS + "v")
                val = ""
                if v is not None:
                    val = v.text or ""
                    if c.attrib.get("t") == "s":
                        try:
                            val = self.shared[int(val)]
                        except Exception:
                            pass
                vals.append(val)
                last = idx
            yield vals


def row_matches(row, terms) -> bool:
    joined = " ".join(clean(x).lower() for x in row[:5])
    return any(t.lower() in joined for t in terms)


def all_rows(wb: Workbook):
    headers = next(wb.rows("ALL"))
    records = []
    for idx, row in enumerate(wb.rows("ALL"), 1):
        if idx == 1 or not row or clean(row[0]).lower() == "market":
            continue
        row = row + [""] * 45
        market = clean(row[0])
        if not market:
            continue
        records.append({
            "sourceRow": idx,
            "market": market,
            "date": excel_date(row[1]),
            "fbRegistered": int(num(row[2])),
            "radioRegistered": int(num(row[3])),
            "youtubeRegistered": int(num(row[4])),
            "tiktokRegistered": int(num(row[5])),
            "tvRegistered": int(num(row[6])),
            "remarketingRegistered": int(num(row[7])),
            "atEventRegistered": int(num(row[8])),
            "totalRegistered": int(num(row[9])),
            "fbAttended": int(num(row[10])),
            "radioAttended": int(num(row[11])),
            "youtubeAttended": int(num(row[12])),
            "tiktokAttended": int(num(row[13])),
            "tvAttended": int(num(row[14])),
            "remarketingAttended": int(num(row[15])),
            "atEventAttended": int(num(row[16])),
            "totalAttended": int(num(row[17])),
            "totalShowRateRaw": clean(row[24]),
            "totalBuyers": int(num(row[32] if len(row) > 32 else 0)),
        })
    return records


def channel_rows(wb: Workbook, sheet: str):
    out = []
    for idx, row in enumerate(wb.rows(sheet), 1):
        if idx <= 3 or not row:
            continue
        row = row + [""] * 18
        market = clean(row[0])
        if not market or market.lower() in {"market", "totals"}:
            continue
        out.append({
            "sourceRow": idx,
            "market": market,
            "date": excel_date(row[1]),
            "registered": int(num(row[2])),
            "attended": int(num(row[3])),
            "showRate": num(row[4]),
            "buyers": int(num(row[5])),
            "spend": num(row[6]),
            "written": num(row[7]),
            "collected": num(row[8]),
            "collected90Day": num(row[9]),
            "cpr": num(row[10]),
            "cpa": num(row[12]),
        })
    return out


def latest_matches(records, terms, limit=8, require_completed=False):
    hits = [r for r in records if row_matches([r.get("market", "")], terms)]
    if require_completed:
        hits = [r for r in hits if r.get("totalRegistered", 0) > 0 or r.get("totalAttended", 0) > 0 or r.get("totalBuyers", 0) > 0]
    return sorted(hits, key=lambda r: r.get("date", ""), reverse=True)[:limit]


def main():
    download()
    wb = Workbook(XLSX)
    all_recs = all_rows(wb)
    channels = {name: channel_rows(wb, name) for name in ["FB YTD", "YouTube YTD", "TikTok YTD", "Radio YTD", "TV YTD"]}
    summary = {
        "sourceUrl": SOURCE_URL,
        "fetchedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "xlsx": str(XLSX),
        "sheets": list(wb.sheets.keys()),
        "allRowCount": len(all_recs),
        "channelRowCounts": {k: len(v) for k, v in channels.items()},
        "activeComparableLatest": {term: latest_matches(all_recs, [term], 6, require_completed=True) for term in ACTIVE_COMPARABLES},
        "mePipelineChecks": {term: latest_matches(all_recs, [term], 6) for term in ME_PIPELINE},
        "previewChecks": {term: latest_matches(all_recs, [term], 6) for term in PREVIEW_CHECKS},
    }
    JSON_OUT.write_text(json.dumps(summary, indent=2))

    lines = [
        "# TLWB Master Tracker Live Extract — 2026-05-06",
        "",
        f"Source: {SOURCE_URL}",
        f"Fetched: {summary['fetchedAt']}",
        f"Local XLSX: `{XLSX}`",
        "",
        "## Sheets detected",
        "",
        *[f"- {s}" for s in summary["sheets"]],
        "",
        "## Row counts",
        "",
        f"- ALL rows parsed: {summary['allRowCount']}",
        *[f"- {k}: {v}" for k, v in summary["channelRowCounts"].items()],
        "",
        "## Dashboard wiring notes",
        "",
        "- `ALL` carries market/date plus channel registration/attendance rollups and total registrations/attendees.",
        "- Channel tabs carry channel spend, CPR, buyers, written, collected, and 90-day collected by market/date.",
        "- This is enough to replace static Marketing comparable-market rows with live Master Tracker rows for Raleigh, Tampa, West Palm Beach, and Minneapolis.",
        "- ME/preview buyer and close-rate history can be sourced from channel tabs via `WS Buyer`, `ME Written`, `ME Collected`, and calculated buyer/close rates, but final same-day sessions still need Numbers Per Session/Slack for live active session rows.",
        "",
    ]
    for title, block in [("Active comparable latest rows", summary["activeComparableLatest"]), ("ME pipeline checks", summary["mePipelineChecks"]), ("Preview checks", summary["previewChecks"] )]:
        lines += [f"## {title}", ""]
        for term, rows in block.items():
            lines.append(f"### {term}")
            if not rows:
                lines.append("- No rows found")
            for r in rows[:4]:
                lines.append(f"- {r['date']} — {r['market']}: regs {r['totalRegistered']}, attended {r['totalAttended']}, buyers {r.get('totalBuyers', 0)}")
            lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {REPORT}")
    print(f"wrote {JSON_OUT}")


if __name__ == "__main__":
    main()
