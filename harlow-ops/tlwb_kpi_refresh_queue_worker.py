#!/usr/bin/env python3
"""Poll the protected TLWB refresh queue and run the deterministic owner pipeline.

Healthy idle polls are silent. A queued request is transitioned through running to
succeeded/no_change/failed with request-id checks on every mutation.
"""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
BASE_URL = "https://tlwb-kpi.vercel.app"
ENDPOINT = f"{BASE_URL}/api/internal/refresh-work"
OWNER = Path("/Users/seanwilliams/.hermes/profiles/harlow/scripts/tlwb_kpi_refresh_owner.py")
OWNER_STATE = Path("/Users/seanwilliams/.hermes/profiles/harlow/projects/tlwb-kpi-refresh-owner/state.json")
TOKEN_SERVICE = "harlow.tlwb-kpi.worker-token"


def keychain_token() -> str:
    proc = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-s", TOKEN_SERVICE, "-a", "worker", "-w"],
        text=True, capture_output=True, timeout=15, check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("TLWB refresh worker credential is unavailable in Keychain")
    return proc.stdout.strip()


def api(method: str, token: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Harlow-TLWB-KPI-queue-worker/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read())


def load_owner_state() -> dict:
    try:
        return json.loads(OWNER_STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def main() -> int:
    try:
        token = keychain_token()
        queued = api("GET", token).get("refresh") or {}
    except Exception as exc:
        print(f"TLWB KPI QUEUE CHECK FAILED — Harlow is handling it; no Troy action requested. {type(exc).__name__}: {exc}")
        return 1

    if queued.get("status") != "queued" or not queued.get("request_id"):
        return 0

    request_id = str(queued["request_id"])
    try:
        api("POST", token, {"action": "start", "request_id": request_id, "message": "Studio is collecting sources and running all validation gates."})
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            return 0
        print(f"TLWB KPI QUEUE START FAILED — HTTP {exc.code}; Harlow will retry.")
        return 1

    before = load_owner_state().get("ended_at")
    try:
        proc = subprocess.run(
            [str(OWNER), "--queue-request"],
            text=True,
            capture_output=True,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired:
        api("POST", token, {"action": "fail", "request_id": request_id, "message": "Refresh exceeded 30 minutes and failed closed; the prior verified build remains live."})
        print("TLWB KPI REQUESTED REFRESH FAILED — owner run exceeded 30 minutes; prior verified build remains live.")
        return 124

    if proc.returncode == 75:
        api("POST", token, {"action": "requeue", "request_id": request_id, "message": "A scheduled owner run is already active; this request will retry within five minutes."})
        return 0

    state = load_owner_state()
    if proc.returncode != 0 or state.get("status") != "ok":
        api("POST", token, {"action": "fail", "request_id": request_id, "message": "Refresh failed a validation or deployment gate; the prior verified build remains live."})
        print(f"TLWB KPI REQUESTED REFRESH FAILED — exit {proc.returncode}; log: {state.get('log', 'unavailable')}")
        return proc.returncode or 1

    if state.get("ended_at") == before:
        api("POST", token, {"action": "requeue", "request_id": request_id, "message": "The owner pipeline is busy; this request will retry within five minutes."})
        return 0

    result = state.get("result")
    action = "complete" if result == "deployed" else "no_change"
    message = "New source data was published and verified." if action == "complete" else "Checked all sources and validation gates; no material data changed."
    api("POST", token, {
        "action": action,
        "request_id": request_id,
        "message": message,
        "completed_at": state.get("ended_at") or datetime.now(TZ).isoformat(),
        "published_at": state.get("published_at"),
        "deployed_fingerprint": state.get("deployed_fingerprint"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
