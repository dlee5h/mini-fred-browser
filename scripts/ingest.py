import requests
import duckdb
import pandas as pd
import os

API_KEY = "58c10a452221776d176a817ef8443f12"

SERIES = [
    "GDP",
    "CPIAUCSL",
    "FEDFUNDS",
    "PAYEMS"
]

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

def fetch_series(series_id):
    url = f"{BASE_URL}?series_id={series_id}&api_key={API_KEY}&file_type=json"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    rows = data["observations"]
    df = pd.DataFrame(rows)
    df["series_id"] = series_id
    return df

def main():
    os.makedirs("../raw", exist_ok=True)
    os.makedirs("../data", exist_ok=True)

    con = duckdb.connect("../data/fred.duckdb")

    for s in SERIES:
        print(f"Fetching {s}...")
        df = fetch_series(s)

        # optional: save raw file for debugging
        df.to_csv(f"../raw/{s}.csv", index=False)

        # load into DuckDB
        con.execute(f"CREATE TABLE IF NOT EXISTS raw_{s} AS SELECT * FROM df")
        con.execute(f"DELETE FROM raw_{s}")
        con.execute(f"INSERT INTO raw_{s} SELECT * FROM df")

    con.close()
    print("Done.")

if __name__ == "__main__":
    main()
