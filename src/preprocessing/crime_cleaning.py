"""Crime data cleaning.

Public API:
    clean_crime_data(df)             -- main entrypoint, full pipeline, returns (df, audit)
    normalize_dtypes(df)              -- dtype coercion only, no rows dropped
    drop_full_row_duplicates(df)      -- byte-identical row removal
    filter_valid_community_areas(df)  -- community_area range enforcement

normalize_dtypes, drop_full_row_duplicates, and filter_valid_community_areas
are exported standalone (not just called internally by clean_crime_data) so
other notebooks and ML code can reuse individual steps -- e.g. notebook 03
calling normalize_dtypes() on a frame that's already been deduplicated
upstream, or an inference pipeline normalizing one new record's dtypes
without running the full drop/dedup sequence meant for bulk historical data.

Decisions encoded here (driven by the notebook 01 audit against the live
2021-2025 Chicago crime pull -- see PROJECT_BLUEPRINT.md):
- Numeric-looking fields (community_area, beat, district, ward, coordinates)
  arrive as strings from the Socrata API -> coerced to numeric.
- community_area outside VALID_COMMUNITY_AREA_RANGE is unrecoverable for the
  community_area x date modeling unit -> dropped.
- Missing lat/long/x/y (privacy-masked by the source, not corrupted) is NOT
  dropped -> community_area is the modeling key, not coordinates; kept as
  null so spatial plots can filter explicitly where needed.
- Duplicate case_number with distinct id/full-row content are legitimate
  multi-offense records under one police case -> kept, logged only.
- Exact full-row duplicates (byte-identical copies) ARE dropped.
No other rows are dropped or imputed here. Every removal is counted and
returned in the audit dict (raw -> transform -> removed/flagged -> final) so
downstream notebooks and reports can trace exactly what changed and why.
"""
from typing import TypedDict

import pandas as pd

VALID_COMMUNITY_AREA_RANGE: tuple[int, int] = (1, 77)
NUMERIC_COLS = ["beat", "district", "ward", "community_area", "x_coordinate", "y_coordinate", "latitude", "longitude"]
BOOLEAN_COLS = ["arrest", "domestic"]
CATEGORY_COLS = ["primary_type", "location_description", "iucr", "fbi_code", "block"]
CATEGORY_NULL_TOKENS = {"NONE", "NAN"}


class CleaningAudit(TypedDict):
    raw_rows: int
    full_row_duplicates_dropped: int
    invalid_community_area_dropped: int
    duplicate_case_numbers_kept: int
    missing_coordinates_kept: int
    final_rows: int


def normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce Socrata's string-typed fields to their real types. No rows dropped.

    date -> datetime64; NUMERIC_COLS -> float (unparseable -> NaN); BOOLEAN_COLS
    -> bool; CATEGORY_COLS -> stripped/uppercased string, with null-token
    literals ("NONE"/"NAN") normalized to true nulls.
    """
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    for col in NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in BOOLEAN_COLS:
        if col in out.columns:
            out[col] = out[col].astype(bool)
    for col in CATEGORY_COLS:
        if col in out.columns:
            normalized = out[col].astype(str).str.strip().str.upper()
            out[col] = normalized.mask(normalized.isin(CATEGORY_NULL_TOKENS))
    return out


def drop_full_row_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop byte-identical duplicate rows. Returns (frame, dropped_count)."""
    dropped = int(df.duplicated().sum())
    return df.drop_duplicates(), dropped


def filter_valid_community_areas(
    df: pd.DataFrame, valid_range: tuple[int, int] = VALID_COMMUNITY_AREA_RANGE
) -> tuple[pd.DataFrame, int]:
    """Drop rows whose community_area falls outside `valid_range` (default 1-77).

    Unrecoverable for the community_area x date modeling unit. Returns
    (frame, dropped_count); community_area is cast to int on the returned frame.
    Requires normalize_dtypes() to have run first (community_area must be numeric).
    """
    lo, hi = valid_range
    invalid = ~df["community_area"].between(lo, hi)
    out = df.loc[~invalid].copy()
    out["community_area"] = out["community_area"].astype(int)
    return out, int(invalid.sum())


def clean_crime_data(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningAudit]:
    """Full cleaning pipeline: normalize dtypes, drop full-row duplicates, drop
    invalid community areas, log (not drop) duplicate case numbers and missing
    coordinates. Returns the cleaned frame and a CleaningAudit trail.
    """
    audit: CleaningAudit = {  # type: ignore[typeddict-item]
        "raw_rows": len(df),
    }

    out = normalize_dtypes(df)

    out, full_dupes = drop_full_row_duplicates(out)
    audit["full_row_duplicates_dropped"] = full_dupes

    out, invalid_ca = filter_valid_community_areas(out)
    audit["invalid_community_area_dropped"] = invalid_ca

    audit["duplicate_case_numbers_kept"] = int(out["case_number"].duplicated().sum())
    audit["missing_coordinates_kept"] = int(out["latitude"].isna().sum())
    audit["final_rows"] = len(out)

    return out, audit
