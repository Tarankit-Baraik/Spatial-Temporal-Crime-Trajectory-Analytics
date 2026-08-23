"""Pull NOAA GHCN-Daily weather for NOAA_STATION_ID (2021-2025). Save untouched to data/raw/weather/."""
import requests
import pandas as pd

from src.config import NOAA_STATION_ID, START_DATE, END_DATE, DATA_RAW

# NOAA GHCN-Daily .dly / CDO API access. CDO Web Services requires a free token
# (https://www.ncdc.noaa.gov/cdo-web/token) — set NOAA_TOKEN env var before running.
GHCND_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
VARS = ["TMAX", "TMIN", "TAVG", "PRCP", "SNOW", "AWND"]


def load_weather_data() -> pd.DataFrame:
    params = {
        "dataset": "daily-summaries",
        "stations": NOAA_STATION_ID,
        "startDate": START_DATE,
        "endDate": END_DATE,
        "dataTypes": ",".join(VARS),
        "format": "json",
        "units": "standard",
    }
    resp = requests.get(GHCND_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"NOAA request failed: {resp.status_code} {resp.text[:300]}")
    rows = resp.json()
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No weather rows returned for configured station/date range — check API/dates before proceeding.")
    # NOAA returns DATE/STATION in uppercase; normalize to match the crime dataset's
    # lowercase 'date' merge key (Phase 8 merges crime+weather on `date`). Measurement
    # columns (TMAX/TMIN/...) keep NOAA's own naming — left untouched.
    df = df.rename(columns={"DATE": "date", "STATION": "station"})
    return df


def save_raw_weather(df: pd.DataFrame) -> None:
    DATA_RAW.joinpath("weather").mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / "weather" / "weather_raw_2021_2025.parquet"
    df.to_parquet(out, index=False)


if __name__ == "__main__":
    save_raw_weather(load_weather_data())
