import csv
import os
import time
from datetime import date

import requests
import pandas as pd
from dotenv import load_dotenv

API_URL = "https://api.weatherapi.com/v1/forecast.json"
CSV_PATH = "weather_data.csv"

# WeatherAPI's free plan returns at most 3 forecast days per request
FORECAST_DAYS = 3

ZIP_CODES = [
    "90045", "10001", "60601", "98101", "33101", "77001", "85001",
    "19101", "78201", "92101", "75201", "95101", "78701", "30301",
    "28201", "80201", "37201", "97201", "89101", "02101",
]


def fetch_weather(zip_codes, api_key):
    results = []
    for zip_code in zip_codes:
        params = {"key": api_key, "q": zip_code, "days": FORECAST_DAYS}
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        for day in data["forecast"]["forecastday"]:
            results.append({
                "zip_code": zip_code,
                "city": data["location"]["name"],
                "region": data["location"]["region"],
                "date": day["date"],
                "max_temp_f": day["day"]["maxtemp_f"],
                "min_temp_f": day["day"]["mintemp_f"],
                "condition": day["day"]["condition"]["text"],
            })
        time.sleep(1)
    return results


def append_to_csv(rows, filepath):
    # Add rows to the end of the CSV. The header is written only when the file
    # is new or empty, so running this every day builds up one long history.
    write_header = not os.path.exists(filepath) or os.path.getsize(filepath) == 0
    with open(filepath, "a", newline="") as f:
        # "\n" line endings everywhere, so rows added on GitHub's Linux runners
        # match rows written on Windows
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def main():
    load_dotenv()
    api_key = os.environ["WEATHERAPI_KEY"]
    results = fetch_weather(ZIP_CODES, api_key)

    # Stamp every row with the day it was fetched, so the same forecast date
    # can be compared across runs (e.g. how a forecast changed as the day got closer)
    fetched_on = date.today().isoformat()
    rows = [{"fetched_on": fetched_on, **row} for row in results]

    df = pd.DataFrame(rows)
    print(df.to_string())
    print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")

    append_to_csv(rows, CSV_PATH)
    print(f"Added {len(rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
