#!/usr/bin/env python3
"""Harlow-owned deterministic refresh runner for the canonical TLWB KPI dashboard.

The wrapped source/build/deploy pipeline remains in the existing dashboard workspace so
Vercel linkage and source history are preserved. Hermes owns scheduling, exit status,
run logs, verification state, and failure delivery. Successful scheduled runs are silent.
"""
from __future__ import annotations

import argparse
import base64
import fcntl
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Denver")
REFRESH = Path("/Users/seanwilliams/.openclaw/workspace-main/scripts/tlwb_kpi_daily_refresh.sh")
ROOT = Path("/Users/seanwilliams/.hermes/profiles/harlow/projects/tlwb-kpi-refresh-owner")
LOGS = ROOT / "logs"
STATE = ROOT / "state.json"
LOCK = ROOT / "refresh.lock"
DASH_ROOT = Path("/Users/seanwilliams/.openclaw/workspace-main/dash-glow-up-15")
CANON_URL = "https://tlwb-kpi.vercel.app"
LEGACY_URL = "https://tlwb-utl-kpi-dashboard.vercel.app"
MISSION_CONTROL_STATE_URL = "https://tlwb-mission-control.vercel.app/mc2_state.json"
PUBLIC_ROUTES = ("/", "/marketing", "/preview", "/workshop", "/inside-sales", "/schedule", "/analytics-brain", "/data-qa")
TEAM_USERNAME = "tlwb-team"
TEAM_PASSWORD_SERVICE = "harlow.tlwb-kpi.team-password"
WORKER_TOKEN_SERVICE = "harlow.tlwb-kpi.worker-token"


def keychain_secret(service: str, account: str) -> str:
    proc = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-s", service, "-a", account, "-w"],
        text=True, capture_output=True, timeout=15, check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"Required Keychain item is unavailable: {service}/{account}")
    return proc.stdout.strip()


def dashboard_authorization() -> str:
    password = keychain_secret(TEAM_PASSWORD_SERVICE, TEAM_USERNAME)
    token = base64.b64encode(f"{TEAM_USERNAME}:{password}".encode()).decode()
    return f"Basic {token}"


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def report_remote_result(state: dict) -> None:
    """Best-effort status publication; it never overrides the deterministic owner result."""
    try:
        token = keychain_secret(WORKER_TOKEN_SERVICE, "worker")
        body = json.dumps({
            "action": "scheduled_result",
            "completed_at": state.get("ended_at"),
            "result": state.get("result", "failed"),
            "published_at": state.get("published_at"),
            "deployed_fingerprint": state.get("deployed_fingerprint"),
        }).encode()
        request = urllib.request.Request(
            f"{CANON_URL}/api/internal/refresh-work", data=body, method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "User-Agent": "Harlow-TLWB-KPI-owner/2.0"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"status endpoint returned HTTP {response.status}")
    except Exception:
        # Deployment/source correctness must never depend on the observability side channel.
        return


def write_state(payload: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temp.replace(STATE)


def fetch(url: str, *, authenticated: bool = False) -> bytes:
    headers = {"User-Agent": "Harlow-TLWB-KPI-owner/2.0"}
    if authenticated:
        headers["Authorization"] = dashboard_authorization()
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read()


def verify_production() -> dict:
    """Verify the already-built local artifact is what both public aliases serve."""
    try:
        fetch(CANON_URL)
        raise RuntimeError("Anonymous dashboard request unexpectedly succeeded")
    except urllib.error.HTTPError as exc:
        if exc.code != 401 or "Basic" not in (exc.headers.get("WWW-Authenticate") or ""):
            raise RuntimeError(f"Anonymous dashboard denial was not the expected Basic 401: HTTP {exc.code}") from exc

    for base in (CANON_URL, LEGACY_URL):
        for route in PUBLIC_ROUTES:
            fetch(f"{base}{route}", authenticated=True)

    canon_index = fetch(CANON_URL, authenticated=True).decode("utf-8", errors="replace")
    legacy_index = fetch(LEGACY_URL, authenticated=True).decode("utf-8", errors="replace")
    asset_pattern = r"/assets/index-[^\"']+\.js"
    canon_match = re.search(asset_pattern, canon_index)
    legacy_match = re.search(asset_pattern, legacy_index)
    if not canon_match or not legacy_match:
        raise RuntimeError("Could not resolve the public JavaScript bundle asset")
    if canon_match.group(0) != legacy_match.group(0):
        raise RuntimeError(f"Canonical/legacy asset mismatch: {canon_match.group(0)} != {legacy_match.group(0)}")

    local_bundles = sorted((DASH_ROOT / "dist" / "assets").glob("index-*.js"))
    if len(local_bundles) != 1:
        raise RuntimeError(f"Expected one local production bundle, found {len(local_bundles)}")
    local_bundle = local_bundles[0].read_bytes()
    public_bundle = fetch(urljoin(CANON_URL, canon_match.group(0)), authenticated=True)
    legacy_bundle = fetch(urljoin(LEGACY_URL, legacy_match.group(0)), authenticated=True)
    if public_bundle != local_bundle or legacy_bundle != local_bundle:
        raise RuntimeError("Public canonical/legacy bundle does not match the local verified dist artifact")

    text = public_bundle.decode("utf-8", errors="replace")
    required = (
        "Latest finals:",
        "Phoenix, AZ",
        "Birmingham, AL",
        "Jacksonville, FL",
        "Long Island",
        "Tulsa, OK",
        "Memphis",
        "lindsey_dashboard_adapter",
        "workshop_schedule_sheet_1psHz1_latest.xlsx",
        "TLWB – Analytics Brain",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(f"Production bundle missing current/source markers: {missing}")
    if "Chicago + Richmond completed; Long Island + Fort Lauderdale completed" in text:
        raise RuntimeError("Production bundle still contains the stale hard-coded workshop heading")

    mission = json.loads(fetch(MISSION_CONTROL_STATE_URL))
    links: list[str | None] = []
    for dashboard in mission.get("dashboards", []):
        if "KPI" in dashboard.get("name", ""):
            links.append(dashboard.get("url"))
    for project in mission.get("projects", []):
        if project.get("id") == "tlwb-utl-kpi-dashboard":
            links.extend(link.get("url") for link in project.get("source_links", []))
    if not links or any(link != CANON_URL for link in links):
        raise RuntimeError(f"Mission Control KPI links are missing or stale: {links}")
    return {"asset": canon_match.group(0), "routes_checked": len(PUBLIC_ROUTES) * 2, "mission_control_links": links}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-deploy", action="store_true", help="Exercise refresh/tests/build without publishing")
    parser.add_argument("--verify-only", action="store_true", help="Verify the existing local dist against production and record recovered success")
    parser.add_argument("--queue-request", action="store_true", help="Return 75 instead of silent success when the owner lock is busy")
    args = parser.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    started = datetime.now(TZ)
    stamp = started.strftime("%Y%m%d-%H%M%S")
    log_path = LOGS / f"refresh-{stamp}.log"

    prior_state = load_state()

    if args.verify_only:
        try:
            details = verify_production()
        except Exception as exc:
            ended = datetime.now(TZ)
            write_state({"started_at": started.isoformat(), "ended_at": ended.isoformat(), "status": "failed", "returncode": 1, "deploy": True, "verification_only": True, "error": str(exc)})
            print(f"TLWB KPI PRODUCTION VERIFICATION FAILED — {exc}")
            return 1
        ended = datetime.now(TZ)
        write_state({"started_at": started.isoformat(), "ended_at": ended.isoformat(), "status": "ok", "returncode": 0, "deploy": True, "verification_only": True, "details": details})
        print(f"OK: TLWB KPI production verified ({details['routes_checked']} routes, {details['asset']})")
        return 0

    if not REFRESH.exists():
        message = f"TLWB KPI REFRESH FAILED — Harlow owner script could not find {REFRESH}"
        write_state({"started_at": started.isoformat(), "ended_at": started.isoformat(), "status": "failed", "returncode": 127, "log": str(log_path), "error": message})
        print(message)
        return 127

    with LOCK.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Scheduled duplicates stay silent; queue requests must retry rather than
            # incorrectly reporting completion.
            return 75 if args.queue_request else 0

        env = os.environ.copy()
        env.update(
            {
                "HOME": "/Users/seanwilliams",
                "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
                "TLWB_KPI_DEPLOY": "0" if args.no_deploy else "1",
                "TLWB_KPI_CHANGE_AWARE": "1",
                "TLWB_KPI_PREVIOUS_FINGERPRINT": str(prior_state.get("deployed_fingerprint") or ""),
                "TLWB_KPI_AUTH_USERNAME": TEAM_USERNAME,
                "TLWB_KPI_AUTH_PASSWORD": keychain_secret(TEAM_PASSWORD_SERVICE, TEAM_USERNAME),
            }
        )
        with log_path.open("w", encoding="utf-8") as log_file:
            proc = subprocess.run(
                [str(REFRESH)],
                cwd="/Users/seanwilliams/.openclaw/workspace-main",
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=1800,
                check=False,
            )

    ended = datetime.now(TZ)
    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        log_text = ""
    fingerprint_match = re.findall(r"TLWB_KPI_(?:FINGERPRINT|NO_CHANGE|DEPLOYED) fingerprint=([0-9a-f]{64})", log_text)
    fingerprint = fingerprint_match[-1] if fingerprint_match else prior_state.get("deployed_fingerprint")
    deployed = "TLWB_KPI_DEPLOYED fingerprint=" in log_text
    no_change = "TLWB_KPI_NO_CHANGE fingerprint=" in log_text
    result = "deployed" if deployed else "no_change" if no_change else "failed" if proc.returncode else "no_change"
    state = {
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "deploy": not args.no_deploy,
        "result": result,
        "deployed_fingerprint": fingerprint if deployed or no_change else prior_state.get("deployed_fingerprint"),
        "published_at": ended.isoformat() if deployed else prior_state.get("published_at"),
        "log": str(log_path),
    }
    write_state(state)
    report_remote_result(state)

    if proc.returncode == 0:
        return 0

    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        excerpt = "\n".join(lines[-16:])
    except OSError:
        excerpt = "(run log unavailable)"
    print(
        "TLWB KPI REFRESH FAILED — Harlow owns follow-through; no action needed from Troy yet.\n"
        f"- Exit code: {proc.returncode}\n"
        f"- Log: {log_path}\n"
        f"- Last output:\n{excerpt}"
    )
    return proc.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.TimeoutExpired as exc:
        now = datetime.now(TZ)
        message = "TLWB KPI REFRESH FAILED — Harlow owner run exceeded 30 minutes."
        write_state({"ended_at": now.isoformat(), "status": "failed", "returncode": 124, "error": str(exc), "message": message})
        print(message)
        raise SystemExit(124)
