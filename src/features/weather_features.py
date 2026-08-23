"""Derived weather features (Phase 7 feature step). Run after
preprocessing.weather_cleaning has produced clean, numeric TMAX/TMIN/PRCP/
SNOW[/TAVG] -- this module assumes numeric dtype and raises if it isn't.

Adds average temperature, temperature range, and rain/snow/temperature
threshold flags. These flags are consumed directly as model features (08)
and as the weather side of Phase 18's weather x temporal interaction terms
(temp x weekend, rain x weekend, snow x night, temp x season, precip x
time-of-day) -- the interaction terms themselves are built in notebook 09
from these flags x features.temporal_features output, not duplicated here.

Threshold sources (documented per blueprint rule: no undocumented composite
score or unexplained flag):
- HEAVY_RAIN_THRESHOLD_IN  = 1.0  -- common "heavy rain day" convention (>=1 in/24h)
- HEAVY_SNOW_THRESHOLD_IN  = 4.0  -- regional heavy-snow-advisory floor (>=4 in/24h)
- EXTREME_HEAT_THRESHOLD_F = 90.0 -- standard "hot day" cutoff for the Midwest
- EXTREME_COLD_THRESHOLD_F = 20.0 -- well below freezing, distinct from a
                                     plain "below freezing" (32F) flag
These are named, reviewable constants, not inline magic numbers -- revisit
against 04_crime_eda / 06_crime_weather_analysis distributions before Phase 18
if Chicago's actual 2021-2025 data suggests different cutoffs.
"""
import pandas as pd

REQUIRED_NUMERIC_COLS = ["TMAX", "TMIN", "PRCP", "SNOW"]

HEAVY_RAIN_THRESHOLD_IN = 1.0
HEAVY_SNOW_THRESHOLD_IN = 4.0
EXTREME_HEAT_THRESHOLD_F = 90.0
EXTREME_COLD_THRESHOLD_F = 20.0


def _assert_numeric(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required weather columns: {missing}")
    non_numeric = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        raise TypeError(
            f"Expected numeric dtype for {non_numeric}, got "
            f"{[str(df[c].dtype) for c in non_numeric]}. Run "
            f"preprocessing.weather_cleaning (numeric coercion) first."
        )


def derive_avg_temp(df: pd.DataFrame) -> pd.Series:
    """TAVG where present and non-null, else (TMAX + TMIN) / 2 per row.
    Handles both whole-column absence -- this station does not return TAVG,
    confirmed in 01_data_ingestion_and_quality -- and row-level nulls within
    an otherwise-present TAVG column."""
    computed = (df["TMAX"] + df["TMIN"]) / 2
    if "TAVG" in df.columns:
        return df["TAVG"].fillna(computed)
    return computed


def create_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds avg_temp, temp_range, is_rain, is_snow, is_heavy_rain,
    is_heavy_snow, is_extreme_heat, is_extreme_cold. No composite/weighted
    score is created -- each flag is independent and documented above."""
    numeric_check_cols = REQUIRED_NUMERIC_COLS + (["TAVG"] if "TAVG" in df.columns else [])
    _assert_numeric(df, numeric_check_cols)

    out = df.copy()
    out["avg_temp"] = derive_avg_temp(out)
    out["temp_range"] = out["TMAX"] - out["TMIN"]

    out["is_rain"] = out["PRCP"] > 0
    out["is_snow"] = out["SNOW"] > 0
    out["is_heavy_rain"] = out["PRCP"] >= HEAVY_RAIN_THRESHOLD_IN
    out["is_heavy_snow"] = out["SNOW"] >= HEAVY_SNOW_THRESHOLD_IN
    out["is_extreme_heat"] = out["TMAX"] >= EXTREME_HEAT_THRESHOLD_F
    out["is_extreme_cold"] = out["TMIN"] <= EXTREME_COLD_THRESHOLD_F

    return out
