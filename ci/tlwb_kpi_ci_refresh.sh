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
# Required for a full data refresh (fail-soft skips are logged, not silent):
#   - Google sheets: anonymous export works today; set GOOGLE_SERVICE_ACCOUNT_JSON
#     for reliable authenticated export.
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

if [[ "$(basename "$SRC")" != "dash-glow-up-15" ]]; then
  log "WARNING: repo dir is '$(basename "$SRC")', but the committed generators expect it to be named 'dash-glow-up-15' (they resolve data via parents[2]). Check out the repo into <workspace-main>/dash-glow-up-15."
fi

# --- Source fetch: Google Sheets (anon export, authenticated fallback) ---------
declare -A SHEETS=(
  [numbers_per_session_1dfke_latest]="1dfke_KCSGHNfnG_FUjAwo1TPAXFtgLEh9tE_XqQB0TU"
  [upcoming_schedule_1F05mJ_latest]="1F05mJPz4m8Kzxc8ROTQc4puRBky263ghSUMTg4kxKqY"
  [workshop_schedule_sheet_1psHz1_latest]="1psHz1be5AdbpjLu4vWEIvecf6CLeuRWodBoHu20Dotw"
  [ws_sales_tracker_1CmJ_latest]="1CmJYo4jIiweNArfZvvKdb0q_WlLtLsNH1UqHaad5gxQ"
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
  if [[ -n "${GOOGLE_SERVICE_ACCOUNT_JSON:-}" ]]; then
    if python3 "$SRC/ci/fetch_google_sheet.py" --id "$id" --out "$out"; then
      validate_xlsx "$out"; return 0
    fi
    log "WARN: authenticated export failed for $name; falling back to anonymous export"
  fi
  curl -sSL --retry 4 --retry-all-errors --retry-delay 2 --connect-timeout 20 --max-time 120 \
    -A "Mozilla/5.0 (TLWB KPI CI Refresh)" \
    "https://docs.google.com/spreadsheets/d/${id}/export?format=xlsx" -o "$out"
  validate_xlsx "$out"
}

log "Fetching structured Google Sheet exports"
for name in "${!SHEETS[@]}"; do fetch_sheet "$name" "${SHEETS[$name]}"; done

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

# --- Data regeneration (requires the remaining Studio-only inputs) --------------
MARKET_COMPARISONS="$DATA_DIR/lindsey_shared_2026-04-25/Market_Comparisons.xlsx"
if [[ "$FULL_REFRESH" == "1" && -f "$MARKET_COMPARISONS" ]]; then
  log "Regenerating dashboard data from fetched sources"
  ( cd "$SRC" && python3 scripts/generate-live-data-review.py )

  if [[ -n "${SLACK_BOT_TOKEN:-}" ]]; then
    SLACK_SNAPSHOT="$DATA_DIR/slack-source-$(date +%Y%m%d-%H%M%S).txt"
    python3 "$SRC/ci/slack_channel_history.py" --out "$SLACK_SNAPSHOT" \
      eventstats expo teamtony teamshaw teamdrecksel teamnick teamwayne teamdent teamwyman teamvogel teammillar
    ( cd "$WORKSPACE_MAIN" && python3 "$SRC/scripts/update_tlwb_slack_operational_sections.py" --slack "$SLACK_SNAPSHOT" --src "$SRC" )
  else
    log "SKIP: SLACK_BOT_TOKEN not set; leaving committed Slack adapters in place"
  fi
else
  log "SKIP full regenerate: set TLWB_CI_FULL_REFRESH=1 and provide $MARKET_COMPARISONS (Studio-only input, see ci/README.md)"
fi

# --- Gates: tests, build, lint --------------------------------------------------
cd "$SRC"
log "Installing dependencies"
npm ci
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
