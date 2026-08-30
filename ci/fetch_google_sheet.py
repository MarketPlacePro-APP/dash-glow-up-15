#!/usr/bin/env python3
"""Authenticated Google Sheet -> XLSX export for CI.

Used for privately-shared sheets (e.g. Lindsey's "Market Comparisons") that the
anonymous export endpoint returns 401 for. Public sheets use the anonymous
fallback in the driver instead.

Credentials (first one present wins):
  - GOOGLE_SERVICE_ACCOUNT_JSON : a service account shared as Viewer on the sheet
    (recommended for unattended CI; needs drive.readonly).
  - GOOGLE_OAUTH_TOKEN_JSON     : an authorized-user token JSON (e.g. the Studio's
    sw@ token) with a refresh_token; used as-is with its granted scopes.

Export strategy mirrors the Studio: try a native Drive export first, then fall
back to reconstructing an XLSX from the Sheets API values (works when the token
only carries spreadsheets scope, not drive.readonly).

Requires: google-api-python-client, google-auth.
"""
from __future__ import annotations

import argparse
import json
import os
from io import BytesIO
from pathlib import Path

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SA_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def load_credentials():
    sa = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa:
        from google.oauth2.service_account import Credentials
        return Credentials.from_service_account_info(json.loads(sa), scopes=SA_SCOPES)

    user = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if user:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials as UserCredentials
        creds = UserCredentials.from_authorized_user_info(json.loads(user))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    raise SystemExit("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_OAUTH_TOKEN_JSON")


def export_via_drive(creds, sheet_id: str) -> bytes:
    from googleapiclient.discovery import build
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    payload = drive.files().export(fileId=sheet_id, mimeType=XLSX_MIME).execute()
    return payload.getvalue() if isinstance(payload, BytesIO) else payload


def export_via_sheets_api(creds, sheet_id: str) -> bytes:
    from googleapiclient.discovery import build
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter

    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    meta = service.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields="sheets(properties(title,gridProperties(rowCount,columnCount)))",
    ).execute()

    wb = Workbook()
    wb.remove(wb.active)
    quote = chr(39)
    specs, used = [], set()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        title = props.get("title") or "Sheet"
        grid = props.get("gridProperties", {})
        rows = int(grid.get("rowCount") or 1)
        cols = int(grid.get("columnCount") or 1)
        safe = title.translate(str.maketrans({ch: "_" for ch in ":\\/?*[]"}))[:31] or "Sheet"
        while safe in used:
            safe = (safe[:28] + f"_{len(used) + 1}")[:31]
        used.add(safe)
        escaped = title.replace(quote, quote + quote)
        specs.append((safe, f"{quote}{escaped}{quote}!A1:{get_column_letter(max(1, cols))}{rows}"))

    for start in range(0, len(specs), 40):
        chunk = specs[start:start + 40]
        response = service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=[spec[1] for spec in chunk],
            valueRenderOption="UNFORMATTED_VALUE",
            dateTimeRenderOption="SERIAL_NUMBER",
        ).execute()
        for (safe, _range), value_range in zip(chunk, response.get("valueRanges", [])):
            ws = wb.create_sheet(safe)
            for r, row in enumerate(value_range.get("values", []), start=1):
                for c, value in enumerate(row, start=1):
                    ws.cell(row=r, column=c, value=value)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Google Sheet file id")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    creds = load_credentials()
    try:
        body = export_via_drive(creds, args.id)
        how = "drive export"
    except Exception as exc:
        print(f"WARN: Drive export failed ({type(exc).__name__}); using Sheets API values", flush=True)
        body = export_via_sheets_api(creds, args.id)
        how = "sheets api"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(body)
    print(f"OK {how} {args.out.name} bytes={len(body)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
