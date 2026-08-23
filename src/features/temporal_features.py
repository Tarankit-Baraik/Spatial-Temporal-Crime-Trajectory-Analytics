"""Temporal feature engineering (Phase 4), reused across two contexts:

- incident-level rows -> `create_temporal_features()` -- adds hour/time_of_day,
  used in 03_spatiotemporal_feature_engineering before daily aggregation.
- date-only, daily-grain frames -> `create_date_features()` -- calendar fields
  only, no hour/time_of_day (a community_area x date row has no single hour).
  Reusable wherever a date-indexed frame needs weekend/season labels: the
  cleaned weather series (05_weather_analysis), the crime-weather merge
  (06_crime_weather_analysis), and Phase 18's weather x temporal interaction
  terms (temp x weekend, temp x season) all build directly on this output.

Both share one calendar-field implementation (`_calendar_fields`) so
weekday/season logic is defined exactly once, not duplicated per notebook.
`date_col` is a parameter, not a hardcoded literal, so either function works
on any date-indexed frame (crime, weather, or a future third source) without
a rename step first.
"""
import pandas as pd

SEASON_BY_MONTH = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}
# [start_hour, end_hour) -> label. Documented bins, not arbitrary.
TIME_OF_DAY_BINS = [(0, 6, "Night"), (6, 12, "Morning"), (12, 18, "Afternoon"), (18, 24, "Evening")]


def _time_of_day(hour: int) -> str:
    for lo, hi, label in TIME_OF_DAY_BINS:
        if lo <= hour < hi:
            return label
    raise ValueError(f"hour {hour} outside 0-23")


def _assert_datetime(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        raise KeyError(f"'{col}' not found -- pass the correct date_col for this frame.")
    if not pd.api.types.is_datetime64_any_dtype(df[col]):
        raise TypeError(
            f"'{col}' must be datetime64, got {df[col].dtype}. Run "
            f"preprocessing.crime_cleaning.normalize_dtypes() (or pd.to_datetime) first."
        )


def _calendar_fields(dt: pd.Series) -> dict[str, pd.Series]:
    return {
        "year": dt.dt.year,
        "month": dt.dt.month,
        "day": dt.dt.day,
        "day_of_week": dt.dt.dayofweek,  # 0 = Monday
        "week_of_year": dt.dt.isocalendar().week.astype(int),
        "quarter": dt.dt.quarter,
        "season": dt.dt.month.map(SEASON_BY_MONTH),
        "is_weekend": dt.dt.dayofweek.isin([5, 6]),
    }


def create_temporal_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Incident-level: calendar fields + hour + time_of_day. Requires a real
    timestamp (not date-only) for hour/time_of_day to be meaningful."""
    _assert_datetime(df, date_col)
    out = df.copy()
    dt = out[date_col]
    for name, series in _calendar_fields(dt).items():
        out[name] = series
    out["hour"] = dt.dt.hour
    out["time_of_day"] = out["hour"].apply(_time_of_day)
    return out


def create_date_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Daily-grain: calendar fields only -- no hour/time_of_day, since a
    single date row (one community_area x date, or one weather station-day)
    has no single hour to derive them from."""
    _assert_datetime(df, date_col)
    out = df.copy()
    for name, series in _calendar_fields(out[date_col]).items():
        out[name] = series
    return out
