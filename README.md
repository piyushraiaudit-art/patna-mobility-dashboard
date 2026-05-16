# Patna Urban Mobility Audit — Congestion Index Collector

A small Python tool that calls Google's Routes API v2 every 30 minutes for 56
origin–destination (OD) pairs across Patna and appends each result to a CSV.
The CSV is later analysed to produce a Congestion Index for the audit report.

> **Auto-stop:** the script refuses to make any API calls after
> **2026-05-20 23:59 IST**. This is intentional — the audit collection window
> ends then. Running the script after that simply logs a message and exits.

---

## What's in this folder

| File                       | Purpose                                                      |
| -------------------------- | ------------------------------------------------------------ |
| `collect_travel_times.py`  | The collector. Reads `corridors.csv`, writes `travel_log.csv`. |
| `corridors.csv`            | The 56 OD pairs (28 corridors × 2 directions). Pre-populated. |
| `requirements.txt`         | Pinned Python dependencies.                                  |
| `.env.example`             | Template for the API key. Copy to `.env` and edit.           |
| `setup.sh`                 | One-shot installer for Ubuntu 22.04 (system pkgs + cron).    |
| `stop_collection.sh`       | Removes the cron entry cleanly.                              |
| `README.md`                | This file.                                                   |

After it runs you will also see:

- `travel_log.csv` — every API result, one row per OD pair per run.
- `collector.log` — rotating log file (10 MB × 5 backups) from the script itself.
- `cron.log` — stdout/stderr captured by cron each run.
- `venv/` — the Python virtual environment created by `setup.sh`.

---

## Setup (one-time, on the Ubuntu VM)

1. **Place the project folder** at `~/patna-mobility` (or anywhere — `setup.sh`
   uses its own location).

2. **Create your `.env` file** with the Google Maps API key:

   ```bash
   cp .env.example .env
   nano .env       # paste your key after GOOGLE_MAPS_API_KEY=
   ```

   The key must have **Routes API** enabled in Google Cloud Console.

3. **Run the installer:**

   ```bash
   chmod +x setup.sh stop_collection.sh
   ./setup.sh
   ```

   This installs `python3`, `python3-pip`, `python3-venv`, creates a `venv/`
   in the project folder, installs the Python deps, and adds a cron entry:

   ```
   */30 * * * * cd <project-dir> && ./venv/bin/python collect_travel_times.py >> cron.log 2>&1
   ```

   The cron entry is idempotent — running `setup.sh` again will **not**
   duplicate it.

---

## Testing it works

Run the collector once, manually:

```bash
./venv/bin/python collect_travel_times.py
```

You should see a single summary line like:

```
[2026-05-12 16:00 IST] 56/56 success, 0 failed
```

Then inspect the CSV:

```bash
head -n 3 travel_log.csv
tail -n 60 travel_log.csv
wc -l travel_log.csv
```

Each successful run appends 56 rows.

---

## Verifying cron is running

```bash
crontab -l              # confirm the */30 entry is present
tail -f cron.log        # watch live as each half-hour batch runs
tail -f collector.log   # detailed script log (warnings, errors)
```

Cron fires on the wall clock — :00 and :30 of every hour. The first run will
happen at the next :00 / :30 boundary after `setup.sh` finishes.

---

## Viewing live data

```bash
tail -n 60 travel_log.csv     # last 60 rows (≈ last batch)
wc -l travel_log.csv          # total rows collected so far
```

CSV columns:

```
timestamp_ist, date, time, day_of_week, hour, is_weekend,
corridor_id, corridor_name, direction,
distance_m, duration_traffic_s, duration_freeflow_s,
congestion_ratio, api_status, error_msg
```

`congestion_ratio` = `duration_traffic_s / duration_freeflow_s`, rounded to
3 decimals. Values near 1.0 mean free-flowing; values above 2.0 indicate
heavy congestion.

---

## Stopping collection

```bash
./stop_collection.sh
```

This removes only the cron entry that references `collect_travel_times.py`,
leaves the data files and the venv intact. Run `setup.sh` again later to
re-enable collection.

After the auto-stop date (2026-05-20 23:59 IST), cron will keep firing but
the script will exit immediately without calling the API. You can leave it
running or run `stop_collection.sh` to clean up.

---

## Dashboard

A Streamlit dashboard turns the raw `travel_log_*.csv` into the six analytical
outputs called for by the audit brief, plus a Methodology & Data Quality page
for senior review.

```bash
./run_dashboard.sh        # opens at http://localhost:8501
```

If `setup.sh` was run, the launcher uses `venv/bin/streamlit`. Otherwise it
falls back to the system `streamlit` on `$PATH`. Install dependencies with
`pip install -r requirements.txt`.

Pages:

| # | Page | Audience |
|---|---|---|
| 0 | Overview — headline stats + feature-gating status strip | Both |
| 1 | Congestion Index Ranking — 28 corridors, most-congested first | Auditees |
| 2 | Hourly Heatmap — corridor × hour median CR, weekday + weekend | Auditees |
| 3 | Direction Asymmetry — inbound vs outbound at AM/PM peak | Auditees |
| 4 | Reliability Index — BTI (FHWA) + CV cross-check | Both |
| 5 | Corridor Map — colour-coded Patna map, report-ready | Audit team |
| 6 | Methodology & Data Quality — formulas, coverage, FAIL log, MD5 | Senior reviewers |
| 7 | Downloads — 10-sheet Excel annexure + 300 DPI PNG bundle | Both |

Every chart self-gates by sample size: **Locked** (insufficient), **Preliminary**
(usable with `n` quoted), **Stable** (audit-defensible). Features unlock
automatically as cron adds new batches; no code changes are needed past day 1.

Public hosted version: see `dashboard/app.py` for the Streamlit Community Cloud
URL once deployed.

---

## Troubleshooting

### "GOOGLE_MAPS_API_KEY is not set"
- Confirm `.env` exists in the same folder as `collect_travel_times.py`.
- Confirm the line reads exactly: `GOOGLE_MAPS_API_KEY=AIza...` (no quotes,
  no spaces around `=`).
- Run `cat .env` to verify.

### Lots of `api_status=FAIL` rows
Open `collector.log` and look at the `error_msg` column in `travel_log.csv`.
Common patterns:

- **`HTTP 403`** — API key invalid, restricted to wrong domain, or Routes API
  not enabled in Google Cloud Console.
- **`HTTP 429`** — quota exceeded. Check your project's quota page in Google
  Cloud Console and raise the per-minute limit or wait for the next window.
- **`HTTP 400`** — usually a malformed coordinate in `corridors.csv`.
  Open the row referenced in the log and check the lat/lng values.
- **`Connection error`** / **`Request timed out`** — temporary network
  problem on the VM. A handful per day is normal; persistent failures mean
  the VM has lost internet access.

### Cron entry isn't firing
- `systemctl status cron` — make sure the cron service is running.
- `grep CRON /var/log/syslog | tail` — see whether cron tried to execute it.
- `crontab -l` — confirm the entry is there.
- Check that `./venv/bin/python` is executable: `ls -l venv/bin/python`.

### "Collection window closed — exiting"
This is the hard auto-stop kicking in (after 2026-05-20 23:59 IST). It is
intentional and **not** a bug. Run `./stop_collection.sh` to remove the cron
entry if you want to silence the daily empty runs.

---

## Quick reference — common commands

```bash
# manual run
./venv/bin/python collect_travel_times.py

# tail the data
tail -n 60 travel_log.csv

# tail the cron output
tail -f cron.log

# tail the script's own log
tail -f collector.log

# remove the cron entry
./stop_collection.sh

# re-add the cron entry
./setup.sh
```
