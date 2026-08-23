# Data Dictionary

Unit of analysis throughout: **community area x date**. Community area is Chicago's official 77-area designation; date spans 2021-01-01 to 2025-12-31 (1,826 days).

## `data/interim/crime_daily.parquet` — 140,602 rows x 22 columns

Full 77-area x 1,826-day grid, zero-filled on days with no recorded crime. Produced by notebook 03.

| Column | Type | Description |
|---|---|---|
| `community_area` | int | Chicago community area code, 1-77 |
| `date` | date | Calendar date |
| `crime_count` | int | Total recorded incidents that day, that area |
| `violent_crime_count` | int | Incidents mapped to the violent category |
| `property_crime_count` | int | Incidents mapped to the property category |
| `drug_crime_count` | int | Incidents mapped to the drug category |
| `unique_crime_types` | int | Distinct offense types recorded that day |
| `arrest_rate` | float | Share of that day's incidents resulting in arrest |
| `domestic_rate` | float | Share of that day's incidents flagged domestic |
| `crime_count_lag_1/3/7/14/28` | float | `crime_count` from 1, 3, 7, 14, 28 days prior, same area |
| `crime_rolling_7/14/28` | float | Rolling mean of `crime_count` over the prior 7, 14, 28 days (excludes current day) |
| `recent_7d_avg` | float | Mean `crime_count` over the prior 7 days |
| `previous_7d_avg` | float | Mean `crime_count` over the 7 days before that (days 8-14 prior) |
| `trend_ratio` | float | `recent_7d_avg` / `previous_7d_avg`. **Excluded from modeling** — see below. |
| `violent_ratio` | float | `violent_crime_count` / `crime_count`. **Excluded from modeling.** |
| `property_ratio` | float | `property_crime_count` / `crime_count`. **Excluded from modeling.** |

**Why the three ratio columns are excluded downstream**: the computation replaces a zero denominator with `NaN` before dividing, and zero-crime weeks occur for lower-crime areas outside the training warm-up period too — keeping these columns would drop validation/test rows non-randomly. They remain in this interim file for transparency but are not part of `modeling_dataset.parquet`.

## `data/interim/weather_cleaned.parquet` — 1,826 rows x 15 columns

One row per date, single station (`USW00094846`, O'Hare). Zero NOAA sentinel values, zero duplicate dates, zero `TMAX < TMIN` rows, full 2021-2025 coverage. `TAVG` is absent from this station's extract.

Confirmed columns feeding the model (11 of the 15; the remaining columns are raw NOAA fields retained for traceability, e.g. `date`, `TMAX`, `TMIN`):

| Column | Type | Description |
|---|---|---|
| `avg_temp` | float, degF | `(TMAX + TMIN) / 2` — computed, not measured, since this station has no `TAVG` |
| `temp_range` | float, degF | `TMAX - TMIN` |
| `PRCP` | float, inches | Daily precipitation |
| `SNOW` | float, inches | Daily snowfall |
| `AWND` | float, mph | Average daily wind speed |
| `is_rain` | bool | `PRCP` above a documented threshold |
| `is_snow` | bool | `SNOW` above a documented threshold |
| `is_heavy_rain` | bool | `PRCP` above a higher, documented threshold |
| `is_heavy_snow` | bool | `SNOW` above a higher, documented threshold |
| `is_extreme_heat` | bool | `avg_temp` above a documented high-temperature threshold |
| `is_extreme_cold` | bool | `avg_temp` below a documented low-temperature threshold |

## `data/interim/crime_weather_daily.parquet` — 140,602 rows x 35 columns

`crime_daily.parquet` (22 columns) left-joined to `weather_cleaned.parquet`'s 13 non-key columns, on `date`. 100% date match, row count unchanged from `crime_daily.parquet`, zero nulls introduced by the join. **Every community area on a given day shares the same weather reading** — the single-station approximation (see `limitations.md`).

## `data/processed/modeling_dataset.parquet` — 138,446 rows x 32 columns

`crime_weather_daily.parquet` plus calendar features, minus 2,156 warm-up rows (2021-only rows where lag/rolling features aren't yet defined), minus the leakage/collinearity-excluded columns. Produced by notebook 07. This is the file the models are trained and evaluated on.

**Identifier / split columns (3)**

| Column | Type | Description |
|---|---|---|
| `community_area` | int | Chicago community area code, 1-77. Not used as a raw model feature — see below. |
| `date` | date | Calendar date |
| `split` | str | `train` (2021-2022), `validation` (2023), or `test` (2024-2025) |

**Calendar features (7)**: `year`, `month`, `day_of_week` (0=Monday), `week_of_year`, `quarter`, `season` (categorical: Winter/Spring/Summer/Fall — one-hot encoded at model-fit time with `Fall` dropped as the reference category), `is_weekend` (bool).

**Weather features (11)**: `avg_temp`, `temp_range`, `PRCP`, `SNOW`, `AWND`, `is_rain`, `is_snow`, `is_heavy_rain`, `is_heavy_snow`, `is_extreme_heat`, `is_extreme_cold` — as defined above.

**Historical crime features (10)**: `crime_count_lag_1/3/7/14/28`, `crime_rolling_7/14/28`, `recent_7d_avg`, `previous_7d_avg` — as defined above, carried forward from `crime_daily.parquet`.

**Target (1)**

| Column | Type | Description |
|---|---|---|
| `high_crime_day` | int, 0/1 | 1 if this area's `crime_count` on this date exceeds that area's own 75th-percentile crime count, threshold computed from the training split (2021-2022) only. Not an official city classification — an analytical construct built for this project. |

**Excluded from features, and why**:

| Excluded | Reason |
|---|---|
| `crime_count` and its category/arrest/domestic breakdowns | Same-day outcome — the target's own raw material |
| `TMAX`, `TMIN` | Collinear with `avg_temp` by construction (r = 0.95-0.99) |
| `trend_ratio`, `violent_ratio`, `property_ratio` | Structural NaN bug — see `crime_daily.parquet` note above |
| `community_area` (as a raw feature) | Deliberate design choice — area identity is carried implicitly through its own lag/rolling history, not a raw identity column |

**Model-fit column count**: 30, not 28 — `season`'s one-hot encoding (`season_Spring`, `season_Summer`, `season_Winter`, with `Fall` dropped) replaces the single `season` column with 3.

## Output tables (`outputs/tables/`)

| File | Produced by | Contents |
|---|---|---|
| `correlation_results.csv` | 06 | Pearson/Spearman correlations, weather vs. crime |
| `statistical_test_results.csv` | 06 | Formal hypothesis test results (t-test/Mann-Whitney/ANOVA/Kruskal-Wallis) |
| `weather_group_comparisons.csv` | 06 | Effect sizes for weather-condition group comparisons |
| `community_weather_associations.csv` | 06 | Per-community-area weather-crime correlations |
| `crime_weather_summary.csv` | 06 | OLS regression summary (season/weekend-adjusted) |
| `model_comparison.csv` | 08 | Validation metrics for all 5 candidates, plus Logistic Regression's test row |
| `cv_summary.csv` | 08 | 5-fold chronological cross-validation results |
| `feature_importance.csv` | 09 | Random Forest impurity-based `feature_importances_`, all 30 model columns |
| `error_analysis_by_community.csv` | 09 | Per-community-area false positive/negative counts and rates, test set |
| `weather_ablation.csv` | 09 | Model A/B/C nested ablation, 5-fold CV mean/std |
| `weather_ablation_robustness.csv` | 09 | Arm 1/2/3 non-nested robustness check, 5-fold CV mean/std |
| `ablation_significance_tests.csv` | 09 | Paired Wilcoxon signed-rank test results across ablation arms |
| `rf_test_metrics.csv` | 09 | Random Forest (tuned) test-set metrics, single row |
| `final_model_comparison.csv` | 10 | All of `model_comparison.csv` plus `rf_test_metrics.csv`, merged |
