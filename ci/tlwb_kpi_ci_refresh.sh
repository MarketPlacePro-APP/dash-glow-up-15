#!/usr/bin/env bash
# Portable TLWB KPI refresh driver for headless CI runners (GitHub Actions).
#
# This mirrors the Studio-owned scripts/../tlwb_kpi_daily_refresh.sh but removes
# every hard-coded /Users/seanwilliams path and Keychain dependency so the same
# source->generate->gate->build (->deploy) pipeline can run off the Mac Studio.
#
# It reproduces the directory layout the committed Python generators expect
# (generate-live-data-review.py resolves ROOT via parents[2], i.e. the parent of
# the checked-out repo), so the generators run unmodified.
#
# Phases:
#   TLWB_KPI_DEPLOY=0 (default here) -> fetch + generate + gates + build, NO deploy.
#   TLWB_KPI_DEPLOY=1                -> also pull/build/deploy to Vercel (Phase 2).
#
# Required for a full data refresh (missing required inputs fail closed):
#   - Google sheets: set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_OAUTH_TOKEN_JSON
#     for the privately shared Market Comparisons source.
#   - Slack: SLACK_BOT_TOKEN (bot invited to the required channels).
#   - Market_Comparisons.xlsx: a Studio-only static input (see ci/README.md).
set -euo pipefail

log() { printf '[ci-refresh] %s\n' "$*" >&2; }

# --- Resolve the workspace-main/dash-glow-up-15 layout the generators expect ---
SRC="${TLWB_KPI_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
WORKSPACE_MAIN="${TLWB_WORKSPACE_MAIN:-$(dirname "$SRC")}"
DATA_DIR="$WORKSPACE_MAIN/data"
EXPORTS_DIR="$DATA_DIR/google_exports"
DEPLOY_ENABLED="${TLWB_KPI_DEPLOY:-0}"
FULL_REFRESH="${TLWB_CI_FULL_REFRESH:-1}"
mkdir -p "$EXPORTS_DIR"

if [[ "$FULL_REFRESH" == "1" ]]; then
  [[ -n "${SLACK_BOT_TOKEN:-}" ]] || { log "ERROR: SLACK_BOT_TOKEN is required for a full refresh"; exit 40; }
  if [[ -z "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" && -z "${GOOGLE_OAUTH_TOKEN_JSON:-}" ]]; then
    log "ERROR: GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_OAUTH_TOKEN_JSON is required for a full refresh"
    exit 41
  fi
fi

if [[ "$(basename "$SRC")" != "dash-glow-up-15" ]]; then
  log "WARNING: repo dir is '$(basename "$SRC")', but the committed generators expect it to be named 'dash-glow-up-15' (they resolve data via parents[2]). Check out the repo into <workspace-main>/dash-glow-up-15."
fi

# --- Source fetch: Google Sheets (anon export, authenticated fallback) ---------
SHEET_NAMES=(
  numbers_per_session_1dfke_latest
  upcoming_schedule_1F05mJ_latest
  workshop_schedule_sheet_1psHz1_latest
  ws_sales_tracker_1CmJ_latest
)
SHEET_IDS=(
  1dfke_KCSGHNfnG_FUjAwo1TPAXFtgLEh9tE_XqQB0TU
  1F05mJPz4m8Kzxc8ROTQc4puRBky263ghSUMTg4kxKqY
  1psHz1be5AdbpjLu4vWEIvecf6CLeuRWodBoHu20Dotw
  1CmJYo4jIiweNArfZvvKdb0q_WlLtLsNH1UqHaad5gxQ
)

validate_xlsx() {
  python3 - "$1" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
b = p.read_bytes()
if len(b) < 1000 or b[:4] != b"PK\x03\x04":
    raise SystemExit(f"Invalid XLSX export: {p} bytes={len(b)} head={b[:16]!r}")
print(f"OK XLSX {p.name} bytes={len(b)}")
PY
}

fetch_sheet() {
  local name="$1" id="$2" out="$EXPORTS_DIR/$1.xlsx"
  # Preserve native workbook formatting/date metadata whenever the public export
  # is available. The Sheets-API values fallback intentionally reconstructs only
  # cell values and is therefore unsuitable as the first choice for schedule
  # workbooks whose date parsing depends on native XLSX metadata.
  if curl -sSL --retry 4 --retry-all-errors --retry-delay 2 --connect-timeout 20 --max-time 120 \
    -A "Mozilla/5.0 (TLWB KPI CI Refresh)" \
    "https://docs.google.com/spreadsheets/d/${id}/export?format=xlsx" -o "$out" \
    && validate_xlsx "$out"; then
    return 0
  fi
  log "WARN: anonymous export failed for $name; trying authenticated export"
  if [[ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" || -n "${GOOGLE_OAUTH_TOKEN_JSON:-}" ]]; then
    python3 "$SRC/ci/fetch_google_sheet.py" --id "$id" --out "$out"
    validate_xlsx "$out"
    return 0
  fi
  log "ERROR: no authenticated fallback is configured for $name"
  return 1
}

log "Fetching structured Google Sheet exports"
for index in "${!SHEET_NAMES[@]}"; do
  fetch_sheet "${SHEET_NAMES[$index]}" "${SHEET_IDS[$index]}"
done

# --- Source fetch: Replit JSON feeds (public) ----------------------------------
fetch_json() {
  local url="$1" out="$2"
  curl -sSL --retry 4 --retry-all-errors --retry-delay 2 --connect-timeout 20 --max-time 120 \
    -A "Mozilla/5.0 (TLWB KPI CI Refresh)" "$url" -o "$out"
  python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
if not data:
    raise SystemExit(f"Empty JSON payload: {sys.argv[1]}")
print(f"OK JSON {Path(sys.argv[1]).name}")
PY
}
log "Fetching Replit inside-sales and collections feeds"
fetch_json "https://utltlwb-stats.replit.app/api/tlwb/inside-sales-dpl" "$DATA_DIR/inside_replit_latest.json"
fetch_json "https://utltlwb-stats.replit.app/api/tlwb/collections-performance" "$DATA_DIR/collections_replit_latest.json"

# --- Source fetch: Lindsey's "Market Comparisons" (privately shared, auth req) --
# Native Google Sheet owned by lindsey@taxlienwealthbuilders.com, shared with sw@.
# Anonymous export returns 401, so this needs GOOGLE_SERVICE_ACCOUNT_JSON (SA
# shared as Viewer) or GOOGLE_OAUTH_TOKEN_JSON (the sw@ token). Fetched fresh each
# run to the path generate-live-data-review.py expects, replacing the frozen
# 2026-04-25 export.
MARKET_COMPARISONS="$DATA_DIR/lindsey_shared_2026-04-25/Market_Comparisons.xlsx"
MC_SHEET_ID="1fCb7-1_TT2w4lzM6mQj38rsnieUdoruk_Eg6_psjB0Y"
if [[ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" || -n "${GOOGLE_OAUTH_TOKEN_JSON:-}" ]]; then
  log "Fetching Market Comparisons sheet (authenticated)"
  mkdir -p "$(dirname "$MARKET_COMPARISONS")"
  python3 "$SRC/ci/fetch_google_sheet.py" --id "$MC_SHEET_ID" --out "$MARKET_COMPARISONS"
  validate_xlsx "$MARKET_COMPARISONS"
else
  log "SKIP Market Comparisons fetch: no Google credential (sheet is privately shared; anon export 401)"
  [[ "$FULL_REFRESH" != "1" ]] || exit 41
fi

# --- Data regeneration ----------------------------------------------------------
if [[ "$FULL_REFRESH" == "1" && -f "$MARKET_COMPARISONS" ]]; then
  log "Regenerating dashboard data from fetched sources"
  ( cd "$SRC" && python3 scripts/generate-live-data-review.py )

  if [[ -n "${SLACK_BOT_TOKEN:-}" ]]; then
    SLACK_SNAPSHOT="$DATA_DIR/slack-source-$(date +%Y%m%d-%H%M%S).txt"
    SLACK_STATUS="$DATA_DIR/slack-source-status.json"
    python3 "$SRC/ci/slack_channel_history.py" --out "$SLACK_SNAPSHOT" --status-out "$SLACK_STATUS" \
      eventstats expo teamtony teamshaw teamdrecksel teamnick teamwayne teamdent teamwyman teamvogel teammillar \
      --optional front-end-team ticketsales collections-allteams refunds-allteams fe-confirmations-team
    ( cd "$WORKSPACE_MAIN" && python3 "$SRC/scripts/update_tlwb_slack_operational_sections.py" --slack "$SLACK_SNAPSHOT" --src "$SRC" )
    ( cd "$SRC" && python3 ci/phase1_freshness_ci.py --status "$SLACK_STATUS" )
  else
    log "SKIP: SLACK_BOT_TOKEN not set; leaving committed Slack adapters in place"
    [[ "$FULL_REFRESH" != "1" ]] || exit 40
  fi
else
  log "SKIP full regenerate: TLWB_CI_FULL_REFRESH must be 1 and Market Comparisons must be fetched (needs a Google credential; see ci/README.md)"
fi

# --- Gates: tests, build, lint --------------------------------------------------
cd "$SRC"
log "Installing dependencies"
npm ci
log "Running parser and business-truth gates"
python3 scripts/validate_tlwb_market_roster.py --src "$SRC" --slack "$SLACK_SNAPSHOT"
python3 ci/test_slack_channel_history.py
python3 scripts/test_marketing_history_coverage.py
python3 scripts/test_marketing_preview_no_drop.py
python3 scripts/test_workshop_schedule_parser.py
python3 scripts/test_upcoming_me_pipeline.py
python3 scripts/test_preview_final_selection.py
python3 scripts/test_workshop_abc_parser.py
python3 scripts/test_tlwb_preview_history.py
python3 scripts/test_phase1_predeploy_gate.py
python3 scripts/phase1_predeploy_gate.py
if [[ -n "${TLWB_ANALYTICS_BRAIN_EXPORT_ROOT:-}" && -d "${TLWB_ANALYTICS_BRAIN_EXPORT_ROOT}" ]]; then
  python3 scripts/generate_analytics_brain_data.py
else
  log "Analytics Brain live exports are not mounted in Phase 1; verifying the committed authenticated snapshot"
  python3 - "$SRC/src/data/analyticsBrain.generated.json" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
rows = data.get("rows") or {}
required = ("eventSummary", "channels", "campaigns", "adSets", "ads")
missing = [name for name in required if not isinstance(rows.get(name), list) or not rows[name]]
source = data.get("source") or {}
qa = data.get("qa") or {}
if data.get("version") != 1 or missing:
    raise SystemExit(f"Invalid committed Analytics Brain artifact; missing rows: {missing}")
if not source.get("authenticatedExport") or not source.get("batchBound") or not qa.get("sameBatch"):
    raise SystemExit("Committed Analytics Brain artifact lacks authenticated same-batch provenance")
print(
    "OK: committed Analytics Brain snapshot "
    f"batch={data.get('batchToken')} exported_at={source.get('exportedAt')} "
    + " ".join(f"{name}={len(rows[name])}" for name in required)
)
PY
fi
log "Running tests (NODE_ENV=test)"
NODE_ENV=test npm test -- --run
log "Building production bundle (NODE_ENV=production)"
NODE_ENV=production npm run build
log "Linting"
npm run lint

FINGERPRINT="$(python3 "$SRC/scripts/tlwb_semantic_fingerprint.py" --src "$SRC")"
[[ "$FINGERPRINT" =~ ^[0-9a-f]{64}$ ]] || { log "Could not compute semantic fingerprint"; exit 44; }
echo "TLWB_KPI_FINGERPRINT fingerprint=$FINGERPRINT"

if [[ "$DEPLOY_ENABLED" != "1" ]]; then
  log "OK: refresh + gates + build passed; deploy skipped (Phase 1, TLWB_KPI_DEPLOY=0)"
  exit 0
fi

# --- Phase 2 deploy (guarded; requires VERCEL_TOKEN + refresh secrets) ----------
: "${VERCEL_TOKEN:?VERCEL_TOKEN required for deploy}"
log "Deploying prebuilt production output to Vercel"
npx vercel pull --yes --environment=production --token "$VERCEL_TOKEN"
npx vercel build --prod --token "$VERCEL_TOKEN"
npx vercel deploy --prebuilt --prod --yes --token "$VERCEL_TOKEN"
log "TLWB_KPI_DEPLOYED fingerprint=$FINGERPRINT"
