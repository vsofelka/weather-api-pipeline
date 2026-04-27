# GitHub Actions Weather Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schedule `weather.py` to run daily via GitHub Actions, appending forecast rows to `weather_data.csv` and committing the result back to `main`.

**Architecture:** Refactor `weather.py` into three testable functions (`fetch_weather`, `append_to_csv`, `main`), guarded by `if __name__ == "__main__"`. Add a `requirements.txt` for dependency pinning. Add a `.github/workflows/weather-pipeline.yml` that checks out the repo, runs the script with the API key from a GitHub Secret, and commits the updated CSV.

**Tech Stack:** Python 3.11, `requests`, `pytest`, GitHub Actions (`ubuntu-latest`)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Create | Declare `requests` runtime dependency |
| `weather.py` | Modify | Refactored script: fetch forecast, append CSV, read key from env |
| `tests/test_weather.py` | Create | Unit tests for `fetch_weather` and `append_to_csv` |
| `.github/workflows/weather-pipeline.yml` | Create | Scheduled workflow: checkout → install → run → commit |

---

## Task 1: Create `requirements.txt`

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create the file**

```
requests
```

Save as `requirements.txt` in the project root.

- [ ] **Step 2: Verify it installs cleanly**

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed requests-...` (or "already satisfied")

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements.txt"
```

---

## Task 2: Refactor `weather.py`

**Files:**
- Modify: `weather.py`
- Create: `tests/test_weather.py`

The current script has three issues to fix:
1. API key is hardcoded (line 4: `API_KEY = "..."`)
2. Variable name bug: `API_KEY` defined but `api_key` used in params — causes `NameError`
3. Output goes to stdout instead of CSV

The refactor extracts `fetch_weather` and `append_to_csv` functions and switches to the forecast endpoint (`forecast.json?days=1`) so the CSV columns (`max_temp_f`, `min_temp_f`) match the existing `weather_data.csv` schema.

- [ ] **Step 1: Install pytest**

```bash
pip install pytest
```

- [ ] **Step 2: Create `tests/test_weather.py` with failing tests**

```python
import os
import csv
import pytest
from unittest.mock import patch, MagicMock


def make_mock_response(zip_code, city, region, date, max_f, min_f, condition):
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "location": {"name": city, "region": region},
        "forecast": {
            "forecastday": [{
                "date": date,
                "day": {
                    "maxtemp_f": max_f,
                    "mintemp_f": min_f,
                    "condition": {"text": condition},
                },
            }]
        },
    }
    return mock


def test_fetch_weather_returns_correct_row():
    from weather import fetch_weather

    mock_resp = make_mock_response("90045", "Los Angeles", "California", "2026-04-27", 72.0, 58.0, "Sunny")
    with patch("weather.requests.get", return_value=mock_resp):
        rows = fetch_weather(["90045"], "fake-key")

    assert len(rows) == 1
    assert rows[0] == {
        "zip_code": "90045",
        "city": "Los Angeles",
        "region": "California",
        "date": "2026-04-27",
        "max_temp_f": 72.0,
        "min_temp_f": 58.0,
        "condition": "Sunny",
    }


def test_fetch_weather_calls_raise_for_status():
    from weather import fetch_weather

    mock_resp = make_mock_response("90045", "Los Angeles", "California", "2026-04-27", 72.0, 58.0, "Sunny")
    with patch("weather.requests.get", return_value=mock_resp):
        fetch_weather(["90045"], "fake-key")

    mock_resp.raise_for_status.assert_called_once()


def test_append_to_csv_creates_file_with_header(tmp_path):
    from weather import append_to_csv

    filepath = str(tmp_path / "data.csv")
    rows = [{"zip_code": "90045", "city": "Los Angeles", "region": "California",
              "date": "2026-04-27", "max_temp_f": 72.0, "min_temp_f": 58.0, "condition": "Sunny"}]
    append_to_csv(rows, filepath)

    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        result = list(reader)

    assert len(result) == 1
    assert result[0]["city"] == "Los Angeles"
    assert result[0]["max_temp_f"] == "72.0"


def test_append_to_csv_does_not_duplicate_header(tmp_path):
    from weather import append_to_csv

    filepath = str(tmp_path / "data.csv")
    rows = [{"zip_code": "90045", "city": "Los Angeles", "region": "California",
              "date": "2026-04-27", "max_temp_f": 72.0, "min_temp_f": 58.0, "condition": "Sunny"}]
    append_to_csv(rows, filepath)
    append_to_csv(rows, filepath)

    with open(filepath, newline="") as f:
        lines = f.readlines()

    assert len(lines) == 3  # 1 header + 2 data rows


def test_main_raises_on_missing_api_key():
    from weather import main

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("WEATHERAPI_KEY", None)
        with pytest.raises(KeyError):
            main()
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_weather.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `fetch_weather` and `append_to_csv` don't exist yet.

- [ ] **Step 4: Rewrite `weather.py`**

```python
import csv
import os
import requests

API_URL = "https://api.weatherapi.com/v1/forecast.json"

ZIP_CODES = [
    "90045", "10001", "60601", "98101", "33101", "77001", "85001",
    "19101", "78201", "92101", "75201", "95101", "78701", "30301",
    "28201", "80201", "37201", "97201", "89101", "02101",
]

CSV_PATH = "weather_data.csv"
FIELDNAMES = ["zip_code", "city", "region", "date", "max_temp_f", "min_temp_f", "condition"]


def fetch_weather(zip_codes, api_key):
    rows = []
    for zip_code in zip_codes:
        params = {"key": api_key, "q": zip_code, "days": 1}
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        day = data["forecast"]["forecastday"][0]
        rows.append({
            "zip_code": zip_code,
            "city": data["location"]["name"],
            "region": data["location"]["region"],
            "date": day["date"],
            "max_temp_f": day["day"]["maxtemp_f"],
            "min_temp_f": day["day"]["mintemp_f"],
            "condition": day["day"]["condition"]["text"],
        })
    return rows


def append_to_csv(rows, filepath=CSV_PATH):
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    api_key = os.environ["WEATHERAPI_KEY"]
    rows = fetch_weather(ZIP_CODES, api_key)
    append_to_csv(rows)
    print(f"Appended {len(rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_weather.py -v
```

Expected output:
```
tests/test_weather.py::test_fetch_weather_returns_correct_row PASSED
tests/test_weather.py::test_fetch_weather_calls_raise_for_status PASSED
tests/test_weather.py::test_append_to_csv_creates_file_with_header PASSED
tests/test_weather.py::test_append_to_csv_does_not_duplicate_header PASSED
tests/test_weather.py::test_main_raises_on_missing_api_key PASSED

5 passed
```

- [ ] **Step 6: Commit**

```bash
git add weather.py tests/test_weather.py
git commit -m "feat: refactor weather.py — env key, forecast API, CSV append"
```

---

## Task 3: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weather-pipeline.yml`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/weather-pipeline.yml`**

```yaml
name: Weather Pipeline

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  fetch-weather:
    runs-on: ubuntu-latest
    retry:
      max-attempts: 2

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run weather pipeline
        env:
          WEATHERAPI_KEY: ${{ secrets.WEATHERAPI_KEY }}
        run: python weather.py

      - name: Commit and push updated CSV
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          if ! git diff --staged --quiet; then
            git commit -m "chore: update weather data $(date +%Y-%m-%d)"
            git pull --rebase
            git push
          fi
```

- [ ] **Step 3: Validate the YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/weather-pipeline.yml'))" && echo "YAML valid"
```

Expected: `YAML valid`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/weather-pipeline.yml
git commit -m "ci: add daily weather pipeline workflow"
```

---

## Task 4: Add GitHub Secret (manual step)

This step is performed in the GitHub UI — it cannot be scripted.

- [ ] **Step 1: Navigate to your repo on GitHub**

Go to **Settings → Secrets and variables → Actions → New repository secret**

- [ ] **Step 2: Add the secret**

- Name: `WEATHERAPI_KEY`
- Value: your WeatherAPI key (the one previously hardcoded in `weather.py`)

Click **Add secret**.

- [ ] **Step 3: Verify by triggering a manual run**

Go to **Actions → Weather Pipeline → Run workflow**. Confirm the run succeeds and a new commit appears on `main` updating `weather_data.csv`.
