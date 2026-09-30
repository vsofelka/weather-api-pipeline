"""
backfill_history.py — rebuild the full forecast history from git.

Why this exists: from May to September 2026, weather.py replaced
weather_data.csv on every run instead of adding to it, so the file only ever
held the latest forecast. Every daily version was still committed by the
GitHub Action, though, so the full history lives in git. This script walks
those versions from oldest to newest, works out which rows each run fetched,
stamps them with the run's date (fetched_on), and writes one combined CSV.

How it decides which rows a run fetched:
  - If a version starts with all of the previous version's rows and adds more
    (the append period, April to May), only the added rows are new.
  - Otherwise (the overwrite period), the whole file is that run's fetch.

Run once from the repo root:
  python scripts/backfill_history.py
"""
import csv
import io
import subprocess

CSV_PATH = "weather_data.csv"


def rows_fetched_in_run(prev_rows, cur_rows):
    appended = len(cur_rows) > len(prev_rows) and cur_rows[:len(prev_rows)] == prev_rows
    if prev_rows and appended:
        return cur_rows[len(prev_rows):]
    return cur_rows


def _git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def main():
    # Every commit that changed the CSV, oldest first, with its date
    log = _git("log", "--reverse", "--format=%H %ad", "--date=short", "--", CSV_PATH)
    versions = [line.split() for line in log.splitlines()]

    history, prev_rows = [], []
    for commit, day in versions:
        text = _git("show", f"{commit}:{CSV_PATH}")
        rows = [r for r in csv.DictReader(io.StringIO(text))]
        # Compare rows as tuples so "same row" means same values in every column
        cur = [tuple(r.values()) for r in rows]
        prev = [tuple(r.values()) for r in prev_rows]
        new_count = len(rows_fetched_in_run(prev, cur))
        for r in rows[len(rows) - new_count:]:
            history.append({"fetched_on": day, **r})
        prev_rows = rows

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(history[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(history)
    print(f"Rebuilt {CSV_PATH}: {len(history)} rows from {len(versions)} versions")


if __name__ == "__main__":
    main()
