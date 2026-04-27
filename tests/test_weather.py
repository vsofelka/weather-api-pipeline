import os
import csv
import pytest
from unittest.mock import patch, MagicMock


def make_mock_response(city, region, date, max_f, min_f, condition):
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

    mock_resp = make_mock_response("Los Angeles", "California", "2026-04-27", 72.0, 58.0, "Sunny")
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

    mock_resp = make_mock_response("Los Angeles", "California", "2026-04-27", 72.0, 58.0, "Sunny")
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
