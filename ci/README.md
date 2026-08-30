# TLWB KPI durable refresh (CI migration)

This directory moves the TLWB KPI dashboard refresh off the single Mac Studio and
onto GitHub Actions, so the dashboard stays current even when the Studio is
offline. It reuses the existing committed Python generators unchanged by
reproducing the `workspace-main/dash-glow-up-15` layout they expect.

## Components

- `.github/workflows/tlwb-kpi-refresh.yml` — Phase 1 scheduled/on-demand refresh,
  **no deploy**. Fetches sources, regenerates data, runs gates + build.
- `.github/workflows/tlwb-kpi-freshness-monitor.yml` — polls `/api/status` every
  30 min and fails if the last publish is older than `MAX_AGE_HOURS` (default 6).
- `ci/tlwb_kpi_ci_refresh.sh` — portable driver mirroring
  `tlwb_kpi_daily_refresh.sh` without Studio paths/Keychain.
- `ci/fetch_google_sheet.py` — authenticated (service-account) sheet export;
  anonymous export is the default fallback.
- `ci/slack_channel_history.py` — headless Slack collector (bot token) replacing
  the Studio-only `recent_slack.py`.

## Required GitHub Actions secrets

| Secret | Used for |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` or `GOOGLE_OAUTH_TOKEN_JSON` | Authenticated export of the privately-shared "Market Comparisons" sheet (the 5 public sheets export anonymously). Use a service account shared as Viewer on the sheet, or the Studio's `sw@` authorized-user token JSON. |
| `SLACK_BOT_TOKEN` | Slack channel history (`channels:history`, bot invited to channels) |
| `TLWB_KPI_AUTH_USERNAME` / `TLWB_KPI_AUTH_PASSWORD` | Freshness monitor + Phase 2 route verification |
| `VERCEL_TOKEN` | Phase 2 deploy only (`org team_eHUDYQiAtTZN5FZP7mhL6AJu`, `project prj_bYcixEpEvztrj98MPbM0elNf7uU1`) |
| `TLWB_REFRESH_GIST_TOKEN` | Phase 2 refresh-queue gist (`id 9417e6feadd30ef20d8a8c609377e05c`) |
| `TLWB_WORKER_TOKEN` | Status callback to `/api/internal/refresh-work` (button loop + Phase 2) |

## "Refresh now" button -> GitHub Actions

`api/refresh` fires `repository_dispatch: tlwb-kpi-refresh` (in addition to queuing
the gist state) so a button click triggers this workflow directly — no dependency
on the Studio worker polling. This is guarded by a **Vercel** environment variable:

| Vercel env var | Used for |
| --- | --- |
| `TLWB_DISPATCH_TOKEN` | GitHub token (fine-grained: Actions read/write on this repo) that lets `api/refresh` trigger the workflow. Optional `TLWB_DISPATCH_REPO` overrides the default `MarketPlacePro-APP/dash-glow-up-15`. |

Until `TLWB_DISPATCH_TOKEN` is set on Vercel the dispatch is skipped, and until
`TLWB_WORKER_TOKEN` is a GitHub secret the workflow's status callbacks are skipped
— so the whole button loop stays dormant through Phase 1 and activates at cutover.

## Still needed from the Studio (reproducibility gaps)

These are read by the pipeline but are **not yet in the repo**, so a fully green
headless run is blocked until they are committed or otherwise provided:

1. `src/lib/sourceHealthStatus.ts` — reconstructed here from the test contract;
   replace with the canonical Studio version if it differs.
2. Market Comparisons — RESOLVED here: the driver now fetches Lindsey's live sheet
   (`1fCb7-1_TT2w4lzM6mQj38rsnieUdoruk_Eg6_psjB0Y`, owned by
   lindsey@taxlienwealthbuilders.com, updated regularly) fresh each run, replacing
   the frozen 2026-04-25 export. It is privately shared (anon export returns 401),
   so it needs a Google credential: either a service account shared as Viewer on
   the sheet, or the Studio's `sw@` token as `GOOGLE_OAUTH_TOKEN_JSON`. Optional
   cleanup for Harlow: rename the misleading `lindsey_shared_2026-04-25` path to a
   `_latest` export in `generate-live-data-review.py`.
3. A coherent test/data baseline. RESOLVED here: the `teammillar` required-channel
   mismatch (test now matches `data/source_health.json`), and the Slack snapshot
   format (`slack_channel_history.py` output now round-trips through
   `scripts/update_tlwb_slack_operational_sections.py::parse_messages`). STILL
   data-driven and needing Harlow's canonical data: an optional-coverage row in
   `data/source_health.json` renders `green` where the test expects `yellow`, and
   the preview adapters lack the `sourceState` the test asserts. Commit matching
   data so `npm test` is green.

The Studio's working tree is internally consistent at deploy time; the git
snapshot is not, which is why these committed data reconciliations are required.

## Phases

- **Phase 1 (this PR):** `TLWB_KPI_DEPLOY=0`. Prove the pipeline runs headlessly.
- **Phase 2 (cutover):** set `TLWB_KPI_DEPLOY=1`, add the deploy secrets, wire
  `api/refresh` to fire `repository_dispatch: tlwb-kpi-refresh` so the "Refresh
  now" button triggers this workflow, and disable the Studio crons.
