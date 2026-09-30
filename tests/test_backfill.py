# Tests for scripts/backfill_history.py, which rebuilds the full forecast
# history from the past versions of weather_data.csv saved in git.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from backfill_history import rows_fetched_in_run  # noqa: E402


def test_appended_version_keeps_only_the_new_rows():
    # Early on, each run added rows to the end of the file
    prev = ["a", "b"]
    cur = ["a", "b", "c", "d"]
    assert rows_fetched_in_run(prev, cur) == ["c", "d"]


def test_overwritten_version_keeps_every_row():
    # Later, each run replaced the file with that day's forecast
    prev = ["a", "b", "c"]
    cur = ["x", "y", "z"]
    assert rows_fetched_in_run(prev, cur) == ["x", "y", "z"]


def test_same_rows_after_overwrite_are_still_that_days_fetch():
    # An unchanged forecast is still a real fetch for that day
    prev = ["a", "b"]
    cur = ["a", "b"]
    assert rows_fetched_in_run(prev, cur) == ["a", "b"]


def test_first_version_keeps_every_row():
    assert rows_fetched_in_run([], ["a", "b"]) == ["a", "b"]
