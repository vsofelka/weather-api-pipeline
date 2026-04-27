# GitHub Actions Weather Pipeline — Design Spec

**Date:** 2026-04-27
**Status:** Approved

## Overview

Schedule `weather.py` to run daily via GitHub Actions, appending fresh forecast rows to `weather_data.csv` and committing the result back to `main`.

## Repository Setup

### `requirements.txt`
Add a `requirements.txt` containing `requests`. GitHub Actions uses this to install dependencies in a clean environment.

### API Key Secret
Remove the hardcoded `API_KEY` from `weather.py`. The script will read the key from `os.environ["WEATHERAPI_KEY"]`. The secret is registered once in the repo under **Settings → Secrets and variables → Actions → New repository secret** with the name `WEATHERAPI_KEY`.

### `weather.py` output
The script appends rows to `weather_data.csv` (open mode `a`) on every run so the workflow has a file to commit. If the file does not exist it is created with a header row.

## Workflow File

**Path:** `.github/workflows/weather-pipeline.yml`

**Trigger:** `schedule` cron `0 6 * * *` (daily at 06:00 UTC). A manual `workflow_dispatch` trigger is also included for ad-hoc runs.

**Job:** `fetch-weather`
- Runner: `ubuntu-latest`
- `retry.max-attempts: 2` — 1 original attempt + 1 retry before the job is marked failed

**Steps:**
1. `actions/checkout@v4` — full checkout so git push works
2. `actions/setup-python@v5` with Python 3.11
3. `pip install -r requirements.txt`
4. `python weather.py` — `WEATHERAPI_KEY` injected from the repo secret
5. Commit and push:
   - `git config user.name` / `user.email` set to `github-actions[bot]`
   - `git add weather_data.csv`
   - Commit with message `chore: update weather data $(date +%Y-%m-%d)`
   - `git push` — if the push fails due to a concurrent update, `git pull --rebase` and retry

The commit step is guarded with `git diff --quiet && git diff --staged --quiet || <commit+push>` so it is a no-op when there are no changes.

## Error Handling

| Failure | Behavior |
|---|---|
| API returns non-200 | Script raises an exception; job fails and retries once |
| `WEATHERAPI_KEY` missing | `KeyError` at startup; job fails immediately with a clear message |
| Push conflict | `git pull --rebase` before retry |
| Second attempt fails | Job marked failed; GitHub shows red run in Actions tab |

## Files Changed

| File | Change |
|---|---|
| `weather.py` | Remove hardcoded key; read from env; write/append to CSV |
| `requirements.txt` | New file: `requests` |
| `.github/workflows/weather-pipeline.yml` | New workflow file |
