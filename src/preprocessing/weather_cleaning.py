"""Weather cleaning (Phase 7). Mirrors preprocessing.crime_cleaning's
audit-trail pattern: every transform is counted and returned in the audit
dict (raw -> transform -> removed/flagged -> final); nothing is dropped or
imputed silently.
"""
from typing import TypedDict

import pandas as pd

from src.preprocessing.missing_values import assert_no_missing

NUMERIC_COLS = ["TMAX", "TMIN", "TAVG", "PRCP", "SNOW", "AWND"]
# NOAA GHCN-Daily / Access Data Service sentinel values seen for missing
# readings -- never real measurements (blueprint rule: handle NOAA sentinels
# correctly, never treat as real).
SENTINEL_VALUES = {-9999, -9999.0, -9999.9}


class WeatherCleaningAudit(TypedDict):
    raw_rows: int
    duplicate_rows_dropped: int
    sentinel_values_replaced: dict
    implausible_temp_rows: int
    final_rows: int


def normalize_weather_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renames NOAA's DATE/STATION (uppercase) to date/station, matching the
    crime dataset's merge-key convention (Phase 8). Case-insensitive; safe to
    call on an already-normalized frame."""
    rename = {c: c.lower() for c in df.columns if c.upper() in ("DATE", "STATION")}
    return df.rename(columns=rename)


def replace_sentinels(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Replaces SENTINEL_VALUES with NaN in each numeric weather column
    present. Returns (frame, {col: n_replaced})."""
    out = df.copy()
    replaced = {}
    for col in NUMERIC_COLS:
        if col in out.columns:
            mask = out[col].isin(SENTINEL_VALUES)
            n = int(mask.sum())
            if n:
                out.loc[mask, col] = pd.NA
            replaced[col] = n
    return out, replaced


def clean_weather_data(df: pd.DataFrame) -> tuple[pd.DataFrame, WeatherCleaningAudit]:
    """Full cleaning pipeline: normalize columns, coerce numeric dtype,
    replace sentinels, drop exact-duplicate rows, enforce one row per date
    (raises if two distinct rows still share a date -- ambiguous readings
    need manual review, not a silent pick). Implausible TMAX<TMIN rows are
    counted, not altered here -- 05_weather_analysis decides how to handle
    them, per the same reasoning crime_cleaning uses for coordinate nulls.
    """
    audit: WeatherCleaningAudit = {"raw_rows": len(df)}  # type: ignore[typeddict-item]

    out = normalize_weather_columns(df)
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out, sentinel_counts = replace_sentinels(out)
    audit["sentinel_values_replaced"] = sentinel_counts

    dupes = int(out.duplicated().sum())
    out = out.drop_duplicates()
    audit["duplicate_rows_dropped"] = dupes

    assert_no_missing(out, ["date"])
    if out["date"].duplicated().any():
        n_ambiguous = int(out["date"].duplicated().sum())
        raise ValueError(
            f"{n_ambiguous} row(s) share a date after exact-duplicate removal -- "
            f"distinct, conflicting readings for the same station-day. Needs manual "
            f"review; clean_weather_data() will not silently pick one."
        )

    audit["implausible_temp_rows"] = (
        int((out["TMAX"] < out["TMIN"]).sum()) if {"TMAX", "TMIN"}.issubset(out.columns) else 0
    )
    audit["final_rows"] = len(out)

    return out, audit
