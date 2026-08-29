# Harlow production snapshot

This branch is a **read-only snapshot** of the production-critical KPI files as they existed on Mac Studio.

It does **not** change how production is published.

## Live deploy path (unchanged)

Production still deploys from the Studio working tree via CLI:

1. Hermes cron `e34e868b43e6` runs `/Users/seanwilliams/.hermes/profiles/harlow/scripts/tlwb_kpi_refresh_owner.py`
2. That wrapper runs `/Users/seanwilliams/.openclaw/workspace-main/scripts/tlwb_kpi_daily_refresh.sh`
3. Publish command remains `npx vercel deploy --prebuilt --prod --yes` from `/Users/seanwilliams/.openclaw/workspace-main/dash-glow-up-15`
4. Canonical alias: `https://tlwb-kpi.vercel.app`
5. GitHub `main` is not the production publisher

`harlow-ops/` in this branch is a **copy** of those live scripts. The owner/worker still execute the original absolute paths above, not these copies.

On-demand refresh: dashboard `/api/refresh` queues work; Studio cron `3070e3be3408` runs `tlwb_kpi_refresh_queue_worker.py` every 5 minutes.

## Secrets

Passwords and tokens are not in this branch. See `.env.example` for names only.
