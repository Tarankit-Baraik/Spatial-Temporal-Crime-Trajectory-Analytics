"""Generic missing-value diagnostics and explicit-imputation helpers, reused
by preprocessing.crime_cleaning, preprocessing.weather_cleaning, and any
future cleaning module. Deliberately does NOT auto-impute anything -- each
function either reports or performs one clearly-named transformation the
caller opts into explicitly. Blind imputation is out of scope by design
(blueprint: don't blind-drop/blind-fill, every transform documented).
"""
import pandas as pd


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column missing count/pct/dtype, sorted worst-first. The one place
    every cleaning notebook checks before deciding what to do about
    missingness -- a measurement, not a decision."""
    report = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_pct": df.isna().mean(),
        "dtype": df.dtypes.astype(str),
    })
    return report.sort_values("missing_pct", ascending=False)


def assert_no_missing(df: pd.DataFrame, cols: list[str]) -> None:
    """Fail fast if any of `cols` has missing values. Use at the end of a
    cleaning pipeline for columns the rest of the pipeline assumes are
    complete (e.g. `date`, `community_area`) -- not for columns where NaN is
    expected and meaningful (e.g. lag-feature warm-up rows)."""
    missing = {c: int(df[c].isna().sum()) for c in cols if df[c].isna().any()}
    if missing:
        raise ValueError(f"Unexpected missing values in required column(s): {missing}")


def add_missing_indicators(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Adds a `<col>_was_missing` boolean flag for each of `cols`, before any
    imputation, so missingness itself stays available as a modeling signal
    even after the original column is filled. Does not modify `cols`."""
    out = df.copy()
    for c in cols:
        out[f"{c}_was_missing"] = out[c].isna()
    return out


def impute_constant(df: pd.DataFrame, col: str, value) -> tuple[pd.DataFrame, int]:
    """Fills `col`'s missing values with `value`. Returns (frame, n_filled) so
    the caller logs how many values were touched, rather than imputing
    silently."""
    out = df.copy()
    n_filled = int(out[col].isna().sum())
    out[col] = out[col].fillna(value)
    return out, n_filled
