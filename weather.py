import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

API_URL = "https://api.weatherapi.com/v1/forecast.json"

ZIP_CODES = [
    "90045", "10001", "60601", "98101", "33101", "77001", "85001",
    "19101", "78201", "92101", "75201", "95101", "78701", "30301",
    "28201", "80201", "37201", "97201", "89101", "02101",
]


def fetch_weather(zip_codes, api_key):
    results = []
    for zip_code in zip_codes:
        params = {"key": api_key, "q": zip_code, "days": 7}
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


def main():
    load_dotenv()
    api_key = os.environ["WEATHERAPI_KEY"]
    results = fetch_weather(ZIP_CODES, api_key)

    df = pd.DataFrame(results)
    print(df.to_string())
    print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")

    df.to_csv("weather_data.csv", index=False)
    print(f"Saved {len(df)} rows to weather_data.csv")


if __name__ == "__main__":
    main()
