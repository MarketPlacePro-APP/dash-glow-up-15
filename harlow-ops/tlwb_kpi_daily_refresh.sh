#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/seanwilliams/.openclaw/workspace-main"
SRC="$ROOT/dash-glow-up-15"
PYTHON_BIN="${TLWB_KPI_PYTHON_BIN:-/usr/bin/python3}"
[[ -x "$PYTHON_BIN" ]] || { echo "Python interpreter missing: $PYTHON_BIN" >&2; exit 43; }
"$PYTHON_BIN" -c 'import openpyxl' 2>/dev/null || {
  echo "Python interpreter lacks required openpyxl module: $PYTHON_BIN" >&2
  exit 43
}
CANON_OUT="$ROOT/outputs/tlwb-kpi"
CANON_URL="https://tlwb-kpi.vercel.app"
LEGACY_URL="https://tlwb-utl-kpi-dashboard.vercel.app"
MISSION_CONTROL_STATE_URL="https://tlwb-mission-control.vercel.app/mc2_state.json"
MEM="$ROOT/memory/$(date +%F).md"
LOG_DIR="$ROOT/logs/tlwb-kpi-refresh"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEPLOY_ENABLED="${TLWB_KPI_DEPLOY:-1}"
mkdir -p "$LOG_DIR" "$ROOT/data/google_exports" "$ROOT/data"

curl_fetch() {
  local url="$1"
  local out="$2"
  curl --http1.1 -L -fsS \
    -A "Mozilla/5.0 (OpenClaw TLWB KPI Refresh)" \
    --retry 4 \
    --retry-all-errors \
    --retry-delay 2 \
    --connect-timeout 20 \
    --max-time 120 \
    "$url" -o "$out"
}

fetch_xlsx() {
  local sheet_id="$1"
  local out="$2"
  local url="https://docs.google.com/spreadsheets/d/${sheet_id}/export?format=xlsx"

  if curl_fetch "$url" "$out" && "$PYTHON_BIN" - "$out" <<PY
import sys
from pathlib import Path
p = Path(sys.argv[1])
b = p.read_bytes()
if len(b) < 1000 or b[:4] != b"PK\x03\x04":
    raise SystemExit(f"Invalid XLSX export: {p} bytes={len(b)} head={b[:16]!r}")
print(f"OK XLSX {p} bytes={len(b)}")
PY
  then
    return 0
  fi

  echo "WARN: anonymous XLSX export failed for ${sheet_id}; trying authenticated SW Google Drive export" >&2
  "$PYTHON_BIN" - "$sheet_id" "$out" <<PY
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

sheet_id = sys.argv[1]
out = Path(sys.argv[2])
token_path = Path("~/.openclaw/credentials/sw-tlwb-google-drive-sheets-token.json").expanduser()
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(key, None)
os.environ.setdefault("NO_PROXY", "oauth2.googleapis.com,www.googleapis.com,*.googleapis.com")
if not token_path.exists():
    raise SystemExit("SW Google token missing")
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(str(token_path), scopes)
if creds.expired and creds.refresh_token:
    creds.refresh(GoogleRequest())
    existing = json.loads(token_path.read_text())
    data = json.loads(creds.to_json())
    data["account"] = existing.get("account")
    data["scopes"] = existing.get("scopes") or scopes
    token_path.write_text(json.dumps(data, indent=2) + "\n")
    token_path.chmod(0o600)
if not creds.valid:
    raise SystemExit("SW Google token invalid")
out.parent.mkdir(parents=True, exist_ok=True)
try:
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    payload = drive.files().export(
        fileId=sheet_id,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ).execute()
    body = payload.getvalue() if isinstance(payload, BytesIO) else payload
    out.write_bytes(body)
    print(f"OK authenticated Drive XLSX {out} bytes={len(body)}")
except Exception as exc:
    print(f"WARN: Drive XLSX export failed for {sheet_id}; trying Sheets API values: {type(exc).__name__}: {str(exc)[:220]}", file=sys.stderr)
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter

    sheets_service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    meta = sheets_service.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields="properties(title),sheets(properties(title,gridProperties(rowCount,columnCount)))",
    ).execute()
    wb = Workbook()
    default = wb.active
    wb.remove(default)
    quote = chr(39)
    sheet_specs = []
    used_titles = set()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        title = props.get("title") or "Sheet"
        grid = props.get("gridProperties", {})
        row_count = int(grid.get("rowCount") or 1)
        col_count = int(grid.get("columnCount") or 1)
        safe_title = title.translate(str.maketrans({ch: "_" for ch in ":\/?*[]"}))[:31] or "Sheet"
        while safe_title in used_titles:
            safe_title = (safe_title[:28] + f"_{len(used_titles) + 1}")[:31]
        used_titles.add(safe_title)
        escaped = title.replace(quote, quote + quote)
        last_col = get_column_letter(max(1, col_count))
        sheet_specs.append((safe_title, f"{quote}{escaped}{quote}!A1:{last_col}{row_count}"))

    values_by_title = []
    chunk_size = 40
    for start in range(0, len(sheet_specs), chunk_size):
        chunk = sheet_specs[start:start + chunk_size]
        response = sheets_service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=[spec[1] for spec in chunk],
            valueRenderOption="UNFORMATTED_VALUE",
            dateTimeRenderOption="SERIAL_NUMBER",
        ).execute()
        for (safe_title, _range), value_range in zip(chunk, response.get("valueRanges", [])):
            values_by_title.append((safe_title, value_range.get("values", [])))

    for safe_title, values in values_by_title:
        ws = wb.create_sheet(safe_title)
        for r_idx, row in enumerate(values, start=1):
            for c_idx, value in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=value)
    wb.save(out)
    print(f"OK authenticated Sheets API XLSX {out} sheets={len(wb.sheetnames)} bytes={out.stat().st_size}")
PY
  "$PYTHON_BIN" - "$out" <<PY
import sys
from pathlib import Path
p = Path(sys.argv[1])
b = p.read_bytes()
if len(b) < 1000 or b[:4] != b"PK\x03\x04":
    raise SystemExit(f"Invalid XLSX export: {p} bytes={len(b)} head={b[:16]!r}")
print(f"OK XLSX {p} bytes={len(b)}")
PY
}

fetch_json() {
  local url="$1"
  local out="$2"
  if ! curl_fetch "$url" "$out"; then
    echo "WARN: JSON fetch failed for ${url}; checking cached ${out}" >&2
  fi
  "$PYTHON_BIN" - "$out" <<PY
import json
import sys
import time
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    raise SystemExit(f"JSON payload missing and fetch failed: {p}")
age_seconds = time.time() - p.stat().st_mtime
data = json.loads(p.read_text())
if not data:
    raise SystemExit(f"Empty JSON payload: {p}")
if age_seconds > 8 * 3600:
    raise SystemExit(f"Cached JSON stale after fetch failure: {p} age_hours={age_seconds / 3600:.1f}")
print(f"OK JSON {p} age_minutes={age_seconds / 60:.1f}")
PY
}

# Structured source refreshes.
fetch_xlsx "1dfke_KCSGHNfnG_FUjAwo1TPAXFtgLEh9tE_XqQB0TU" "$ROOT/data/google_exports/numbers_per_session_1dfke_latest.xlsx"
fetch_xlsx "1F05mJPz4m8Kzxc8ROTQc4puRBky263ghSUMTg4kxKqY" "$ROOT/data/google_exports/upcoming_schedule_1F05mJ_latest.xlsx"
fetch_xlsx "1psHz1be5AdbpjLu4vWEIvecf6CLeuRWodBoHu20Dotw" "$ROOT/data/google_exports/workshop_schedule_sheet_1psHz1_latest.xlsx"
fetch_xlsx "1CmJYo4jIiweNArfZvvKdb0q_WlLtLsNH1UqHaad5gxQ" "$ROOT/data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx"
fetch_json "https://utltlwb-stats.replit.app/api/tlwb/inside-sales-dpl" "$ROOT/data/inside_replit_latest.json"
fetch_json "https://utltlwb-stats.replit.app/api/tlwb/collections-performance" "$ROOT/data/collections_replit_latest.json"
cp "$ROOT/data/inside_replit_latest.json" "$ROOT/data/inside_replit_$(date +%F).json"
cp "$ROOT/data/collections_replit_latest.json" "$ROOT/data/collections_replit_$(date +%F).json"

# Archive every fetched structured source into SQLite before dashboard parsing.
# Parser/build failures must not prevent source truth from remaining queryable.
"$PYTHON_BIN" "$ROOT/scripts/archive_tlwb_structured_sources.py" \
  | tee "$LOG_DIR/structured-archive-$STAMP.log"

cd "$ROOT"
"$PYTHON_BIN" scripts/tlwb_master_tracker_extract.py | tee "$LOG_DIR/master-tracker-$STAMP.log"
# Generate the schedule artifact before Slack reconciliation so a newly fetched
# route plan controls the session denominator in the same refresh run.
cd "$SRC"
"$PYTHON_BIN" scripts/generate-live-data-review.py | tee "$LOG_DIR/generated-data-$STAMP.log"
cd "$ROOT"
if [[ -z "${TLWB_SLACK_SNAPSHOT:-}" ]]; then
  TLWB_SLACK_SNAPSHOT="$LOG_DIR/slack-source-$STAMP.txt"
  HOME=/Users/seanwilliams "$PYTHON_BIN" scripts/tlwb_recent_slack_bundle.py \
    --limit 120 \
    --out "$TLWB_SLACK_SNAPSHOT" \
    eventstats expo teamtony teamshaw teamdrecksel teamnick teamwayne teamdent teamwyman teamvogel teammillar \
    | tee "$LOG_DIR/slack-collect-$STAMP.log"
fi
[[ -f "$TLWB_SLACK_SNAPSHOT" ]] || { echo "Slack source bundle missing: $TLWB_SLACK_SNAPSHOT" >&2; exit 42; }
HOME=/Users/seanwilliams "$PYTHON_BIN" scripts/update_tlwb_slack_operational_sections.py \
  --slack "$TLWB_SLACK_SNAPSHOT" \
  --src "$SRC" \
  | tee "$LOG_DIR/slack-adapters-$STAMP.log"
# The comparable-history generator must run after the Slack adapter so its key
# roster matches every current Marketing card instead of a stale fixed list.
"$PYTHON_BIN" scripts/generate_master_tracker_marketing_ts.py | tee "$LOG_DIR/master-marketing-$STAMP.log"

cd "$SRC"
"$PYTHON_BIN" scripts/validate_tlwb_market_roster.py --src "$SRC" --slack "$TLWB_SLACK_SNAPSHOT" | tee "$LOG_DIR/market-roster-gate-$STAMP.log"
"$PYTHON_BIN" scripts/test_marketing_history_coverage.py | tee "$LOG_DIR/marketing-history-coverage-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_marketing_preview_no_drop.py | tee "$LOG_DIR/marketing-preview-no-drop-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_workshop_schedule_parser.py | tee "$LOG_DIR/workshop-schedule-parser-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_upcoming_me_pipeline.py | tee "$LOG_DIR/upcoming-me-pipeline-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_preview_final_selection.py | tee "$LOG_DIR/preview-final-selection-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_workshop_abc_parser.py | tee "$LOG_DIR/workshop-abc-parser-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_tlwb_preview_history.py | tee "$LOG_DIR/preview-history-test-$STAMP.log"
"$PYTHON_BIN" scripts/test_phase1_predeploy_gate.py | tee "$LOG_DIR/phase1-predeploy-gate-test-$STAMP.log"
"$PYTHON_BIN" scripts/phase1_freshness_spine.py | tee "$LOG_DIR/freshness-spine-$STAMP.log"
"$PYTHON_BIN" scripts/tlwb_preview_history.py \
  --src "$SRC" \
  --db "${TLWB_SOURCE_ARCHIVE_DB:-/Users/seanwilliams/.openclaw/workspace/outputs/tlwb_source_archive.db}" \
  | tee "$LOG_DIR/preview-history-$STAMP.log"
"$PYTHON_BIN" scripts/phase1_predeploy_gate.py 2>&1 | tee "$LOG_DIR/predeploy-gate-$STAMP.log"
# Analytics Brain uses a sanitized build-time artifact from the latest verified
# same-batch export. This never opens the authenticated browser profile or reads
# Keychain/browser credentials; a missing or inconsistent export fails closed.
"$PYTHON_BIN" scripts/generate_analytics_brain_data.py | tee "$LOG_DIR/analytics-brain-$STAMP.log"
# Be explicit: the host may export NODE_ENV=production, where React's
# jsx-dev-runtime intentionally leaves jsxDEV undefined and component tests
# fail before the build. Tests use test mode; the artifact uses production.
NODE_ENV=test npm test -- --run | tee "$LOG_DIR/test-$STAMP.log"
NODE_ENV=production npm run build | tee "$LOG_DIR/build-$STAMP.log"
npm run lint | tee "$LOG_DIR/lint-$STAMP.log"
FINGERPRINT="$("$PYTHON_BIN" "$SRC/scripts/tlwb_semantic_fingerprint.py" --src "$SRC")"
[[ "$FINGERPRINT" =~ ^[0-9a-f]{64}$ ]] || { echo "Could not compute TLWB semantic fingerprint" >&2; exit 44; }
echo "TLWB_KPI_FINGERPRINT fingerprint=$FINGERPRINT"

if [[ "$DEPLOY_ENABLED" != "1" ]]; then
  echo "OK: TLWB KPI refresh, Slack adapter update, tests, gates, and build passed; deploy skipped (TLWB_KPI_DEPLOY=$DEPLOY_ENABLED)"
  exit 0
fi
if [[ "${TLWB_KPI_CHANGE_AWARE:-1}" == "1" && -n "${TLWB_KPI_PREVIOUS_FINGERPRINT:-}" && "$FINGERPRINT" == "$TLWB_KPI_PREVIOUS_FINGERPRINT" ]]; then
  echo "TLWB_KPI_NO_CHANGE fingerprint=$FINGERPRINT"
  echo "OK: TLWB KPI sources checked and verified; no material change, production deploy skipped."
  exit 0
fi

sync_output() {
  local out="$1" project_id="$2" project_name="$3"
  rm -rf "$out"
  mkdir -p "$out/.vercel"
  cp -R "$SRC/dist/." "$out/"
  cp "$SRC/vercel.json" "$out/vercel.json"
  cp "$SRC/middleware.ts" "$out/middleware.ts"
  rm -rf "$out/api"
  cp -R "$SRC/api" "$out/api"
  cat > "$out/package.json" <<'JSON'
{"private":true,"type":"module","dependencies":{"@vercel/blob":"2.8.0","@vercel/functions":"3.9.3"}}
JSON
  cat > "$out/.vercel/project.json" <<JSON
{"projectId":"${project_id}","orgId":"team_eHUDYQiAtTZN5FZP7mhL6AJu","projectName":"${project_name}"}
JSON
  "$PYTHON_BIN" - "$out/.vercel/project.json" "$project_name" <<'PY'
import json, sys
p, expected = sys.argv[1], sys.argv[2]
actual = json.load(open(p)).get('projectName')
if actual != expected:
    raise SystemExit(f"Refusing deploy: projectName={actual!r}, expected={expected!r}")
print(f"Deploy guard ok: {expected}")
PY
}

sync_output "$CANON_OUT" "prj_bYcixEpEvztrj98MPbM0elNf7uU1" "tlwb-kpi"
echo "[tlwb-kpi] Pulling linked production environment" >&2
(cd "$SRC" && npx vercel pull --yes --environment=production) | tee "$LOG_DIR/vercel-pull-tlwb-kpi-$STAMP.log"
echo "[tlwb-kpi] Building native Vercel production output" >&2
(cd "$SRC" && npx vercel build --prod) | tee "$LOG_DIR/vercel-build-tlwb-kpi-$STAMP.log"
echo "[tlwb-kpi] Deploying verified prebuilt production output" >&2
GIST_ID="${TLWB_REFRESH_GIST_ID:-9417e6feadd30ef20d8a8c609377e05c}"
GIST_TOKEN="$(/usr/bin/security find-generic-password -s harlow.tlwb-kpi.refresh-gist-token -a gist -w 2>/dev/null || true)"
if [[ -n "$GIST_TOKEN" ]]; then
  "$PYTHON_BIN" - "$SRC/.vercel/output/functions" "$GIST_ID" "$GIST_TOKEN" <<'PY'
import json, sys
from pathlib import Path
root, gist_id, token = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
targets = {
    "api/refresh.func/.vc-config.json",
    "api/status.func/.vc-config.json",
    "api/internal/refresh-work.func/.vc-config.json",
    "api/v1/status.func/.vc-config.json",
}
patched = 0
for rel in targets:
    path = root / rel
    if not path.exists():
        continue
    data = json.loads(path.read_text())
    env = data.setdefault("environment", {})
    env["TLWB_REFRESH_GIST_ID"] = gist_id
    env["TLWB_REFRESH_GIST_TOKEN"] = token
    path.write_text(json.dumps(data, indent=2) + "\n")
    patched += 1
if patched != len(targets):
    raise SystemExit(f"Refresh-queue function env inject patched {patched}/{len(targets)}")
print(f"Injected gist refresh-queue env into {patched} function configs")
PY
  echo "[tlwb-kpi] Injecting GitHub gist refresh-queue credentials into this deployment" >&2
else
  echo "[tlwb-kpi] Refresh-queue gist token missing from Keychain; Refresh now will stay unavailable" >&2
fi
(cd "$SRC" && npx vercel deploy --prebuilt --prod --yes) | tee "$LOG_DIR/deploy-tlwb-kpi-$STAMP.log"

CANON_DEPLOY_URL="$("$PYTHON_BIN" - "$LOG_DIR/deploy-tlwb-kpi-$STAMP.log" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(errors="ignore")
matches = re.findall(r"https://tlwb-[a-z0-9-]+-market-place-pro\.vercel\.app", text)
print(matches[-1] if matches else "")
PY
)"
[[ -n "$CANON_DEPLOY_URL" ]] || { echo "Could not determine canonical deployment URL for alias repair" >&2; exit 32; }
(cd "$SRC" && npx vercel alias set "$CANON_DEPLOY_URL" "${LEGACY_URL#https://}") | tee "$LOG_DIR/alias-legacy-kpi-$STAMP.log"

DASH_AUTH_CONFIG="$(mktemp /tmp/tlwb-kpi-curl.XXXXXX)"
chmod 600 "$DASH_AUTH_CONFIG"
"$PYTHON_BIN" - "$DASH_AUTH_CONFIG" <<'PY'
import os, sys
from pathlib import Path
user = os.environ.get("TLWB_KPI_AUTH_USERNAME")
password = os.environ.get("TLWB_KPI_AUTH_PASSWORD")
if not user or not password:
    raise SystemExit("Protected dashboard verification credentials are missing")
if any(ch.isspace() for ch in user + password):
    raise SystemExit("Protected dashboard credentials contain unsupported whitespace")
Path(sys.argv[1]).write_text(f"default login {user} password {password}\n", encoding="utf-8")
PY
trap 'rm -f "$DASH_AUTH_CONFIG"' EXIT
dashboard_curl() {
  curl --netrc-file "$DASH_AUTH_CONFIG" "$@"
}

check_url() {
  local base="$1"
  for route in / /marketing /preview /workshop /inside-sales /schedule /analytics-brain /data-qa; do
    code="$(dashboard_curl -L -s -o /tmp/tlwb_kpi_route.html -w '%{http_code}' "${base}${route}")"
    echo "$base$route $code"
    [[ "$code" == "200" ]] || { echo "Route check failed: ${base}${route} -> $code" >&2; exit 30; }
  done
}
check_url "$CANON_URL"
check_url "$LEGACY_URL"

bundle_asset_for() {
  local base="$1" out="$2"
  dashboard_curl -L -s "$base" -o "$out.index.html"
  local asset
  asset="$("$PYTHON_BIN" - "$out.index.html" <<'PY'
import re, sys
html=open(sys.argv[1]).read()
m=re.search(r"/assets/index-[^\"]+\.js", html)
print(m.group(0) if m else "")
PY
)"
  [[ -n "$asset" ]] || { echo "Could not find production bundle asset for $base" >&2; exit 31; }
  dashboard_curl -L -s "${base}${asset}" -o "$out.bundle.js"
  echo "$asset"
}

CANON_ASSET="$(bundle_asset_for "$CANON_URL" /tmp/tlwb_kpi_canon)"
LEGACY_ASSET="$(bundle_asset_for "$LEGACY_URL" /tmp/tlwb_kpi_legacy)"
[[ "$CANON_ASSET" == "$LEGACY_ASSET" ]] || { echo "KPI alias asset mismatch: canonical=$CANON_ASSET legacy=$LEGACY_ASSET" >&2; exit 41; }
for bundle in /tmp/tlwb_kpi_canon.bundle.js /tmp/tlwb_kpi_legacy.bundle.js; do
  for required in 'lindsey_dashboard_adapter' 'ws_sales_tracker_1CmJ_latest.xlsx' 'numbers_per_session_1dfke_latest.xlsx' 'TLWB/MO Schedule' 'workshop_schedule_sheet_1psHz1_latest.xlsx' 'TLWB – Analytics Brain'; do
    grep -q "$required" "$bundle" || { echo "Missing bundle marker in $bundle: $required" >&2; exit 40; }
  done
done
if [[ -n "${TLWB_SLACK_SNAPSHOT:-}" && -f "$TLWB_SLACK_SNAPSHOT" ]]; then
  "$PYTHON_BIN" - /tmp/tlwb_kpi_canon.bundle.js "$SRC/src/data/executiveAdapters.ts" <<'PY' | tee "$LOG_DIR/slack-operational-production-qa-$STAMP.log"
import re, sys
from pathlib import Path

bundle = Path(sys.argv[1]).read_text(errors="ignore")
adapter = Path(sys.argv[2]).read_text(errors="ignore")
required = [
    "slack_expo_current_",
    "slack_active_preview_",
    "slack_eventstats_active_marketing_",
    "slack_me_finals_",
    "August Investor Expo",
    "Tulsa, OK",
    "Memphis",
    "Hartford",
]
required.extend(sorted(set(re.findall(r"team:\s*'([^']+· Speaker [^']+ / #[^']+)'", adapter))))
missing = [marker for marker in required if marker not in bundle]
if missing:
    raise SystemExit(f"Slack operational production QA failed; missing bundle markers: {missing}")
stale_patterns = [
    r'market:"Long Island".{0,600}?sourceState:"active_session"',
    r'market:"Nashville".{0,600}?sourceState:"active_session"',
]
stale = [pattern for pattern in stale_patterns if re.search(pattern, bundle)]
if stale:
    raise SystemExit(f"Slack operational production QA failed; stale LIVE market patterns present: {stale}")
print("OK: Slack operational source markers present in production bundle")
PY
fi

TLWB_QA_BASES="$CANON_URL,$LEGACY_URL" \
TLWB_KPI_SRC="$SRC" \
TLWB_KPI_AUTH_USERNAME="$TLWB_KPI_AUTH_USERNAME" \
TLWB_KPI_AUTH_PASSWORD="$TLWB_KPI_AUTH_PASSWORD" \
node scripts/qa_tlwb_market_roster.mjs | tee "$LOG_DIR/market-roster-production-qa-$STAMP.log"

curl -L -fsS "$MISSION_CONTROL_STATE_URL" -o /tmp/tlwb_mission_control_state.json
"$PYTHON_BIN" - /tmp/tlwb_mission_control_state.json "$CANON_URL" <<'PY'
import json, sys
state = json.load(open(sys.argv[1]))
expected = sys.argv[2]
links = []
for dash in state.get("dashboards", []):
    if "KPI" in dash.get("name", ""):
        links.append(dash.get("url"))
for project in state.get("projects", []):
    if project.get("id") == "tlwb-utl-kpi-dashboard":
        links.extend(link.get("url") for link in project.get("source_links", []))
bad = [url for url in links if url != expected]
if not links:
    raise SystemExit("Mission Control KPI link missing")
if bad:
    raise SystemExit(f"Mission Control KPI link stale: {bad}")
print(f"OK Mission Control KPI links -> {expected}")
PY

cat >> "$MEM" <<EOF

## TLWB KPI daily refresh — $(date '+%H:%M %Z')
- Structured exports refreshed, dashboard rebuilt, canonical Vercel project deployed, legacy KPI alias repaired, Mission Control KPI link checked, and route/bundle checks passed.
- Canonical: ${CANON_URL}
- Legacy alias: ${LEGACY_URL}
EOF

echo "TLWB_KPI_DEPLOYED fingerprint=$FINGERPRINT"
echo "OK: TLWB KPI daily structured refresh deployed and verified: $CANON_URL"
