#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/seanwilliams/.openclaw/workspace-main"
SRC="$ROOT/dash-glow-up-15"
OUT="$ROOT/outputs/kpi-dashboard-v3loveable-options"
MEM="$ROOT/memory/$(date +%F).md"
URL="https://kpi-dashboard-v3loveable-options.vercel.app"

cd "$SRC"

PROJECT_NAME="$(python3 - <<'PY'
import json
from pathlib import Path
p=Path('/Users/seanwilliams/.openclaw/workspace-main/outputs/kpi-dashboard-v3loveable-options/.vercel/project.json')
print(json.loads(p.read_text()).get('projectName',''))
PY
)"
if [[ "$PROJECT_NAME" != "kpi-dashboard-v3loveable-options" ]]; then
  echo "Refusing deploy: output Vercel project is '$PROJECT_NAME', expected kpi-dashboard-v3loveable-options" >&2
  exit 20
fi

python3 scripts/generate-live-data-review.py
npm run build

mkdir -p "$OUT"
rsync -a --delete --exclude='.vercel' --exclude='vercel.json' "$SRC/dist/" "$OUT/"

if [[ ! -f "$OUT/vercel.json" ]]; then
  cat > "$OUT/vercel.json" <<'JSON'
{"rewrites":[{"source":"/(.*)","destination":"/index.html"}]}
JSON
fi

cd "$OUT"
npx vercel deploy --prod --yes >/tmp/tlwb_kpi_review_vercel.log

for route in / /data-qa /marketing /preview /workshop /inside-sales /schedule; do
  code="$(curl -L -s -o /dev/null -w '%{http_code}' "$URL$route")"
  if [[ "$code" != "200" ]]; then
    echo "Route check failed: $route returned $code" >&2
    exit 30
  fi
done

JS_FILE="$(ls -t "$OUT"/assets/index-*.js | head -1)"
for forbidden in '2 min ago' '5 min ago' 'source of truth mode' 'source-adapter' 'Attendance breakdown' 'button seats'; do
  if grep -q "$forbidden" "$JS_FILE"; then
    echo "Forbidden deployed bundle string found: $forbidden" >&2
    exit 40
  fi
done

cd "$SRC"
if ! git diff --quiet -- src/data/generatedData.ts; then
  git add src/data/generatedData.ts scripts/generate-live-data-review.py
  git commit -m "Refresh TLWB KPI review data snapshot" >/tmp/tlwb_kpi_review_git.log || true
fi

mkdir -p "$(dirname "$MEM")"
cat >> "$MEM" <<EOF

## TLWB KPI review refresh cron — $(date '+%H:%M %Z')
- Refreshed source-hardened review-only KPI data, rebuilt, synced to review output, deployed to ${URL}, and verified Executive/Data QA/Marketing/Preview/Workshop/Inside Sales/Schedule routes returned 200.
- Vercel project guard passed: kpi-dashboard-v3loveable-options. Production KPI untouched.
EOF

echo "OK: TLWB KPI review-only refresh deployed and verified."
