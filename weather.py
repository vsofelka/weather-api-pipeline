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
    file_exists = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
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
