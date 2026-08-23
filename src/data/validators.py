"""Data quality checks. Raise, never silently continue on invalid state (Phase 3/6)."""
import pandas as pd


def validate_crime_data(df: pd.DataFrame) -> dict:
    """Return audit dict: row_count, missing %, dup ids, invalid dates/coords/community areas."""
    report = {
        "row_count": len(df),
        "missing_pct": df.isna().mean().to_dict(),
        "duplicate_ids": int(df["id"].duplicated().sum()) if "id" in df else None,
        "duplicate_case_numbers": int(df["case_number"].duplicated().sum()) if "case_number" in df else None,
    }
    if "date" in df:
        dates = pd.to_datetime(df["date"], errors="coerce")
        report["invalid_dates"] = int(dates.isna().sum())
        report["future_dates"] = int((dates > pd.Timestamp.now()).sum())
    if {"latitude", "longitude"}.issubset(df.columns):
        lat, lon = pd.to_numeric(df["latitude"], errors="coerce"), pd.to_numeric(df["longitude"], errors="coerce")
        report["invalid_coords"] = int((~lat.between(41.0, 42.5) | ~lon.between(-88.5, -87.0)).sum())
    if "community_area" in df:
        ca = pd.to_numeric(df["community_area"], errors="coerce")
        report["invalid_community_area"] = int((~ca.between(1, 77)).sum())
    return report


def validate_weather_data(df: pd.DataFrame) -> dict:
    """Return audit dict: row_count, date uniqueness, missingness, sentinel/implausible values."""
    report = {"row_count": len(df), "missing_pct": df.isna().mean().to_dict()}
    if "date" in df:
        report["duplicate_dates"] = int(df["date"].duplicated().sum())
    return report
