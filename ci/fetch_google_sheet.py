#!/usr/bin/env python3
"""Authenticated Google Sheet -> XLSX export for CI.

Used only when GOOGLE_SERVICE_ACCOUNT_JSON is set; the driver falls back to the
anonymous export endpoint otherwise. Reliability path for when a sheet's link
sharing is tightened. Requires: google-api-python-client, google-auth.
"""
from __future__ import annotations

import argparse
import json
import os
from io import BytesIO
from pathlib import Path

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Google Sheet file id")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise SystemExit("GOOGLE_SERVICE_ACCOUNT_JSON not set")

    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    payload = drive.files().export(fileId=args.id, mimeType=XLSX_MIME).execute()
    body = payload.getvalue() if isinstance(payload, BytesIO) else payload
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(body)
    print(f"OK authenticated export {args.out.name} bytes={len(body)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
