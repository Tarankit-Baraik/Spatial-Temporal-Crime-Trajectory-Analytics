# Methodology

## Scope

Chicago crime and NOAA weather data, 2021-01-01 to 2025-12-31 (post-COVID, five years). Unit of analysis is community area x date — one row per Chicago community area (77 total) per calendar day (1,826 days), not individual incidents. This grain was chosen for the best resolution-to-volume tradeoff among the location fields available in the crime data.

## Data ingestion

- **Crime**: Chicago Data Portal, Socrata dataset `ijzp-q8t2` ("Crimes 2001-Present"), queried directly for the 2021-2025 window rather than downloading the full ~8.58M-row dataset. Schema was inspected against the live API rather than assumed from older archived versions of the dataset.
- **Weather**: NOAA GHCN-Daily, station `USW00094846` (Chicago O'Hare), same window. NOAA sentinel/missing-value codes are handled explicitly and never treated as real readings. The station's extract has no `TAVG` field, so `avg_temp` is computed as `(TMAX + TMIN) / 2` for every row.

Raw files are stored locally and are never committed to version control or modified after download.

## Cleaning

Crime records were audited before any row was dropped: row count, dtypes, missingness percentage, duplicate IDs and case numbers, invalid or future dates, invalid latitude/longitude, invalid community area codes, and inconsistent category labels. Duplicates were investigated rather than dropped by default. An audit trail (raw -> transformed -> removed/flagged -> final) was kept at each stage.

## Feature engineering

**Temporal**: year, month, day of week, week of year, quarter, season, weekend flag.

**Spatial**: `community_area` is the primary spatial key used to aggregate the data, but it is *not* included as a raw model feature — an area's identity is carried implicitly through its own lag and rolling crime history instead. This was a deliberate choice, not an oversight, made so the model generalizes on time-varying local patterns rather than memorizing 77 area-identity dummy variables.

**Crime categories**: broad groups (violent, property, drug, fraud/other) are defined by an explicit, documented mapping — no undocumented category logic.

**Daily aggregation**: for each community area x date, `crime_count`, `violent_crime_count`, `property_crime_count`, `drug_crime_count`, unique crime types, arrest rate, and domestic rate. Days with zero recorded crime are zero-filled rather than omitted, so every area has a complete 1,826-day grid.

**Historical crime features**: for each community area x date, computed strictly from information available before that date — `crime_count_lag_{1,3,7,14,28}`, `crime_rolling_{7,14,28}`, `recent_7d_avg`, `previous_7d_avg`, plus `trend_ratio`, `violent_ratio`, and `property_ratio`. The three ratio columns were later excluded from modeling (see Data Quality below).

**Weather features**: `avg_temp`, `temp_range`, plus flags for rain, snow, heavy rain, heavy snow, extreme heat, and extreme cold. No composite weather score was built without a documented justification for its construction.

## Crime-weather merge

Crime (community area x date) is left-joined to weather (date-only, single citywide station) on `date`. This means every community area on a given day is assigned the same weather reading — a real limitation, stated explicitly rather than implied to be spatially exact (see [`limitations.md`](limitations.md)).

## Target definition

`high_crime_day` = 1 if a community area's crime count on a given day exceeds that area's own 75th-percentile historical crime count, else 0. The percentile threshold is computed **from the training period only** (2021-2022) and applied unchanged to validation and test — no future information enters the threshold.

## Data quality decision: excluded features

Three engineered ratio columns (`trend_ratio`, `violent_ratio`, `property_ratio`) were excluded from the final feature set after a real bug was caught during smoke-testing: the ratio computation replaces a zero denominator with `NaN` before dividing, and zero-crime weeks occur in any year for lower-crime areas, not only during the training warm-up period. Keeping these columns would have dropped validation and test rows non-randomly. The fix was applied at the root — excluding the columns from the feature list — rather than patched with an imputation workaround.

`TMAX` and `TMIN` were excluded as collinear with `avg_temp` by construction (r = 0.95-0.99). `crime_count` and its category/arrest/domestic breakdowns were excluded because they are the target's own raw material — including them would be same-day outcome leakage.

## Modeling dataset

After excluding the leakage/collinearity columns above and removing 2,156 warm-up rows (rows in 2021 where lag/rolling features are not yet defined), the final modeling dataset has 138,446 rows and 32 columns: 3 identifier/split columns (`community_area`, `date`, `split`), 28 features, and the `high_crime_day` target. See [`data_dictionary.md`](data_dictionary.md) for the full column list.

Season is one-hot encoded with the first category (`Fall`, alphabetically) dropped, producing 30 columns the models are actually trained on.

## Chronological split

Never a random `train_test_split`. Splits are strictly chronological:

| Split | Years | Rows | `high_crime_day` rate |
|---|---|---|---|
| Train | 2021-2022 | 54,054 | 20.7% |
| Validation | 2023 | 28,105 | 32.4% |
| Test | 2024-2025 | 56,287 | 27.8% |

A leakage audit confirmed no date overlap between splits and no feature computed using information from a later split.

## Modeling

`DummyClassifier(strategy="most_frequent")` baseline, then Logistic Regression (interpretable linear baseline), Decision Tree (nonlinear baseline), and Random Forest (default, then tuned). `class_weight="balanced"` (or `balanced_subsample` for Random Forest) was used to address class imbalance (20.7%-32.4% positive rate across splits); SMOTE was not used — the imbalance was judged moderate, not severe, and the project's stated rule is not to add complexity without evidence it helps.

Random Forest was tuned with `RandomizedSearchCV` over `n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`, `max_features`, and `class_weight`, evaluated within 5-fold chronological cross-validation (`TimeSeriesSplit` on unique training dates, mapped back to rows — not a random k-fold). The tuned configuration: `n_estimators=100, max_depth=5, min_samples_split=2, min_samples_leaf=4, max_features="log2", class_weight="balanced_subsample"`.

**A methodological finding surfaced during training, not before it**: single-split validation ranked default Random Forest at F1 0.419, but 5-fold chronological cross-validation showed it collapsing to F1 0.104 +/- 0.107 — the single split was not representative. This is why cross-validation, not a single validation split, is the standard used throughout model comparison and the ablation study.

## Evaluation

Accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, ROC curve, and PR curve are all reported — accuracy alone is treated as insufficient given class imbalance. No target accuracy number was set in advance; the project reports the actual leakage-safe result, including a negative one (see [`findings.md`](findings.md) on the F1-selection-rule pitfall).

## Model selection and its consequence

The project's model-selection rule was F1 on the validation split. This rule selected Logistic Regression (F1 0.492) over tuned Random Forest (F1 0.473), even though Random Forest had the best ROC-AUC (0.587) and PR-AUC (0.402) of all five candidates. On test, the selected Logistic Regression degenerated to a near-constant positive classifier (recall 0.999, negative-class recall 0.00) — worse than the majority-class baseline on accuracy. This is documented as a methodological lesson, not hidden: **Random Forest, saved regardless of the selection outcome, was carried forward as the primary model for interpretation and the final analysis**, while Logistic Regression's test-set failure is reported as a cautionary result.

## Interpretation and ablation

Random Forest's `feature_importances_` (impurity-based) is reported as what the model relies on to split nodes, not as a causal ranking. Error analysis covers false positives/negatives by community area and by month across the test period.

The weather ablation compares feature sets under one fixed model configuration (Random Forest's tuned hyperparameters), so any score difference is attributable to feature content, not to hyperparameters differing between runs. Three nested sets were tested (calendar + historical crime; + weather; + weather interaction terms), followed by a fourth, non-nested robustness check isolating weather from calendar entirely (crime + weather, no calendar features), with a paired Wilcoxon signed-rank test across the 5 CV folds. At n = 5 folds, the test cannot reach conventional significance (p < 0.05) and its smallest possible p-value is 0.0625 — results are reported as directional evidence, not confirmatory hypothesis tests.

Interaction terms tested: `avg_temp x is_weekend`, `avg_temp x season`, `is_rain x is_weekend`, `is_snow x is_weekend`. The blueprint's original candidates, `snow x night` and `precip x time-of-day`, could not be built — this daily community-area x date dataset has no night or time-of-day breakdown in its confirmed schema, and a placeholder column was not fabricated to stand in for one.

## Statistical language

Association, not causation, throughout: correlations and group comparisons are described as "associated with," never "causes," in the absence of a causal study design. Statistical tests are chosen by distribution — Pearson/Spearman for correlation, t-test/Mann-Whitney U or ANOVA/Kruskal-Wallis for group comparisons, depending on normality.

## Reproducibility

Every notebook is delivered fail-fast against real file paths — a missing upstream file raises an error naming which earlier notebook produces it, rather than continuing silently. All random processes are seeded (`RANDOM_STATE = 42`). Reusable logic lives in `src/`; notebooks orchestrate and explain. One analytical responsibility per notebook (see the notebook table in [`README.md`](../README.md)).
