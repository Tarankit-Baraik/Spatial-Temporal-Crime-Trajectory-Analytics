"""Spatial feature flags, documented crime-category mapping, and daily
aggregation to the community_area x date modeling unit (Phases 4-5). Category
mapping and daily aggregation live here (not temporal_features.py) because
both are keyed by community_area, the blueprint's primary spatial unit.
"""
import pandas as pd

from src.config import START_DATE, END_DATE

# Documented crime-category mapping (blueprint Phase 4: "no undocumented
# mappings, store mapping explicitly"). Keyed by `primary_type` as returned
# by the Socrata API. Anything not listed here falls into "OTHER" -- expand
# this map, don't special-case elsewhere, if 03's coverage check flags a
# high-volume type landing in OTHER.
CRIME_CATEGORY_MAP: dict[str, set[str]] = {
    "VIOLENT": {"HOMICIDE", "CRIMINAL SEXUAL ASSAULT", "CRIM SEXUAL ASSAULT", "ASSAULT", "BATTERY", "ROBBERY", "KIDNAPPING"},
    "PROPERTY": {"BURGLARY", "THEFT", "MOTOR VEHICLE THEFT", "CRIMINAL DAMAGE", "ARSON", "CRIMINAL TRESPASS"},
    "DRUG": {"NARCOTICS", "OTHER NARCOTIC VIOLATION"},
    "FRAUD": {"DECEPTIVE PRACTICE", "FORGERY"},
}
_TYPE_TO_CATEGORY = {t: cat for cat, types in CRIME_CATEGORY_MAP.items() for t in types}


def add_crime_category(df: pd.DataFrame) -> pd.DataFrame:
    """Maps `primary_type` to the broad category via CRIME_CATEGORY_MAP;
    unmapped types -> "OTHER". Requires `primary_type` already uppercased
    (see preprocessing.crime_cleaning.normalize_dtypes)."""
    out = df.copy()
    out["crime_category"] = out["primary_type"].map(_TYPE_TO_CATEGORY).fillna("OTHER")
    return out


def create_spatial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Spatial fields (community_area, district, beat, lat/long) already exist
    post-cleaning; this only flags coordinate availability. No new geometry is
    derived -- the source is block-level, not exact-coordinate (blueprint rule
    11: no exact-coordinate claims)."""
    out = df.copy()
    out["has_coordinates"] = out["latitude"].notna()
    return out


def aggregate_daily_crime(df: pd.DataFrame, start_date: str = START_DATE, end_date: str = END_DATE) -> pd.DataFrame:
    """Aggregates incident-level rows to community_area x date. Reindexes to
    the full date range x every community area present in the data, filling
    non-occurring combinations with 0 -- required so the lag/rolling features
    built next (features.crime_lags) see a continuous daily series per
    community area rather than one with gaps on zero-crime days.

    Requires `date`, `crime_category`, `arrest`, `domestic` already present
    (create_temporal_features, add_crime_category, cleaning, respectively).
    """
    work = df.copy()
    work["date_only"] = work["date"].dt.normalize()

    daily = (
        work.groupby(["community_area", "date_only"])
        .agg(
            crime_count=("id", "count"),
            violent_crime_count=("crime_category", lambda s: (s == "VIOLENT").sum()),
            property_crime_count=("crime_category", lambda s: (s == "PROPERTY").sum()),
            drug_crime_count=("crime_category", lambda s: (s == "DRUG").sum()),
            unique_crime_types=("primary_type", "nunique"),
            arrest_rate=("arrest", "mean"),
            domestic_rate=("domestic", "mean"),
        )
        .reset_index()
        .rename(columns={"date_only": "date"})
    )

    all_dates = pd.date_range(start_date, end_date, freq="D")
    all_areas = sorted(work["community_area"].unique())
    full_index = pd.MultiIndex.from_product([all_areas, all_dates], names=["community_area", "date"])

    daily = daily.set_index(["community_area", "date"]).reindex(full_index).reset_index()
    count_cols = ["crime_count", "violent_crime_count", "property_crime_count", "drug_crime_count", "unique_crime_types"]
    daily[count_cols] = daily[count_cols].fillna(0).astype(int)
    daily[["arrest_rate", "domestic_rate"]] = daily[["arrest_rate", "domestic_rate"]].fillna(0.0)

    return daily.sort_values(["community_area", "date"]).reset_index(drop=True)
