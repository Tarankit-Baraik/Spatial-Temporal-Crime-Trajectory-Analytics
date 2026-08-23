"""Historical crime lag/rolling features (Phase 11). Operates on the daily
community_area x date frame from features.spatial_features.aggregate_daily_crime().

Leakage safety (blueprint rule 6): every value is computed from strictly
prior days. All rolling windows are built on a series shifted by 1 first, so
the current day's own crime_count never enters its own feature row.
"""
import pandas as pd

LAG_DAYS = [1, 3, 7, 14, 28]
ROLLING_WINDOWS = [7, 14, 28]


def _add_lags_for_group(g: pd.DataFrame) -> pd.DataFrame:
    community_area = g.name  # groupby.apply drops the grouping column from the sub-frame; capture before any copy
    g = g.sort_values("date").copy()
    g["community_area"] = community_area
    cc = g["crime_count"]

    for lag in LAG_DAYS:
        g[f"crime_count_lag_{lag}"] = cc.shift(lag)

    shifted_cc = cc.shift(1)  # exclude current day from every rolling window below
    for window in ROLLING_WINDOWS:
        g[f"crime_rolling_{window}"] = shifted_cc.rolling(window).sum()

    g["recent_7d_avg"] = g["crime_rolling_7"] / 7
    previous_7d_sum = shifted_cc.shift(7).rolling(7).sum()  # the 7 days before the recent window
    g["previous_7d_avg"] = previous_7d_sum / 7
    g["trend_ratio"] = g["recent_7d_avg"] / g["previous_7d_avg"].replace(0, pd.NA)

    violent_roll7 = g["violent_crime_count"].shift(1).rolling(7).sum()
    property_roll7 = g["property_crime_count"].shift(1).rolling(7).sum()
    g["violent_ratio"] = violent_roll7 / g["crime_rolling_7"].replace(0, pd.NA)
    g["property_ratio"] = property_roll7 / g["crime_rolling_7"].replace(0, pd.NA)

    return g


def create_crime_lag_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Adds crime_count_lag_{1,3,7,14,28}, crime_rolling_{7,14,28},
    recent_7d_avg, previous_7d_avg, trend_ratio, violent_ratio, property_ratio.
    `violent_ratio`/`property_ratio` are historical (prior-7-day) shares, not
    same-day shares -- consistent with every other feature in this module and
    required for leakage safety, since a same-day ratio would be derived from
    the same crime_count the target (`high_crime_day`) is thresholded on.

    NaNs at the start of each community_area's series (up to 28 rows, from the
    longest lag/window) are expected -- there is no prior history to compute
    from yet. Do not fill these; downstream steps handle them explicitly.
    """
    out = daily_df.groupby("community_area", group_keys=False).apply(_add_lags_for_group)
    return out.reset_index(drop=True)
