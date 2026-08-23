"""Pull Chicago crime data (2021-2025) from Socrata API. Save untouched to data/raw/crime/."""
import requests
import pandas as pd

from src.config import CHICAGO_SOCRATA_DOMAIN, CHICAGO_CRIME_DATASET_ID, START_DATE, END_DATE, DATA_RAW

FIELDS = [
    "id", "case_number", "date", "block", "iucr", "primary_type", "description",
    "location_description", "arrest", "domestic", "beat", "district", "ward",
    "community_area", "fbi_code", "x_coordinate", "y_coordinate", "latitude", "longitude",
]


def load_crime_data(limit: int = 50_000) -> pd.DataFrame:
    """Page through Socrata SoQL API for START_DATE..END_DATE. Raises on non-200."""
    url = f"https://{CHICAGO_SOCRATA_DOMAIN}/resource/{CHICAGO_CRIME_DATASET_ID}.json"
    where = f"date >= '{START_DATE}T00:00:00' AND date <= '{END_DATE}T23:59:59'"
    rows, offset = [], 0
    while True:
        params = {
            "$select": ",".join(FIELDS),
            "$where": where,
            "$limit": limit,
            "$offset": offset,
            "$order": "date",
        }
        resp = requests.get(url, params=params, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Socrata request failed: {resp.status_code} {resp.text[:300]}")
        batch = resp.json()
        if not batch:
            break
        rows.extend(batch)
        offset += limit
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No crime rows returned for configured date range — check API/dates before proceeding.")
    return df


def save_raw_crime(df: pd.DataFrame) -> None:
    DATA_RAW.joinpath("crime").mkdir(parents=True, exist_ok=True)
    out = DATA_RAW / "crime" / "crime_raw_2021_2025.parquet"
    df.to_parquet(out, index=False)


if __name__ == "__main__":
    save_raw_crime(load_crime_data())
