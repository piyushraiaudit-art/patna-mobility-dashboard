# Public deployment — Streamlit Community Cloud

The GCP VM keeps collecting data — that side needs no changes. You download
the CSVs to this laptop, then push to GitHub. Streamlit Cloud auto-rebuilds
on every push and shows the latest data publicly.

## One-time setup (≈10 minutes)

### 1. Create a public GitHub repo

In the GitHub web UI, create a new **public** repository, e.g.
`patna-mobility-dashboard`. Do **not** add a README, license, or `.gitignore`
— this folder already has one.

### 2. Initialise git here and push

```bash
cd "/Users/apple/Documents/Traffic Data"
git init
git add .
git commit -m "Initial: collector + dashboard"
git branch -M main
git remote add origin git@github.com:<your-username>/patna-mobility-dashboard.git
git push -u origin main
```

`.gitignore` already excludes `venv/`, `.env`, log files, `__pycache__`, and
`.DS_Store`. The `travel_log_*.csv` files **are** committed — the dashboard
reads them at runtime, and they contain no PII.

### 3. Connect Streamlit Community Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io) and sign in with the same GitHub account.
2. Click **New app** → pick the repo → branch `main` → main file path `dashboard/app.py`.
3. Click **Deploy**. The build takes ~3 minutes.
4. The app URL appears at the top of the page — share it with auditees and seniors.

Free tier is sufficient: one app, public, unlimited views, auto-redeploys on every push.

## Daily routine (≈30 seconds per day, after first download of the day)

1. Download the latest `travel_log_<date>.csv` from the GCP VM (you already
   do this — your usual `scp` / cloud-console download / GCS bucket pull).
2. Place it in this folder, overwriting / sitting alongside existing snapshots.
3. From this folder, run:

   ```bash
   git add travel_log_*.csv
   git commit -m "Daily data sync $(date +%F)"
   git push
   ```

   Streamlit Cloud detects the push, rebuilds in ~30 seconds, and the public
   dashboard now reflects the new day.

That's it. No VM changes, no cron changes, no SSH keys.

## Optional — make it one command

Create `sync.sh` (gitignored if you want):

```bash
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
git add travel_log_*.csv
git commit -m "Daily data sync $(date +%F)" || echo "No new data to commit."
git push
```

`chmod +x sync.sh`. Then your daily routine is just `./sync.sh` after the download.
