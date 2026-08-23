# Findings

Full statistical detail backing this document lives in `outputs/tables/`. Methodology is in [`methodology.md`](methodology.md); limitations affecting how far to trust these results are in [`limitations.md`](limitations.md).

## 1. What crime types dominate?

**Open, unresolved discrepancy.** An earlier exploratory pass (notebook 04) reported violent 40.7%, property 34.8%, drug 14.9%, fraud 9.5%, on an implied base of roughly 18,000 incidents. A later computation on the full cleaned dataset (notebook 06, 1,210,059 incidents) gives violent 31.2%, property 47.2%, drug 2.4%, other 19.1%. The notebook 06 figures are almost certainly authoritative — they sum to the full cleaned dataset exactly, while notebook 04's implied base is a small fraction of it — but this has not been formally reconciled against notebook 04's original computation. **This document cites 31.2% / 47.2% / 2.4% / 19.1% as the working figure** and flags the discrepancy as open work.

## 2. When does crime peak or decline?

Citywide crime rose from 209,688 incidents in 2021 to a peak of 263,409 in 2023, then declined for two consecutive years: 259,223 (2024), 237,629 (2025). This turning point is confirmed independently by the `high_crime_day` target rate, which also peaks in 2023 (32.4%, against 15.7% in 2021 and 24.5% in 2025) — two separately computed signals agreeing on the same year.

## 3. Where is crime concentrated?

Community area 25 has the highest total crime volume over 2021-2025 (61,512 incidents), followed by areas 8 (52,854), 28 (48,228), 43 (41,258), and 32 (40,397). This top-5 ranking is stable across all five years — no reordering among the leading areas.

## 4. How do spatial patterns change over time?

Among the top 5 areas, four (8, 25, 28, 32) peak in 2024 — one year after the citywide 2023 peak — before declining in 2025. Area 43 is the exception, peaking in 2023 alongside the citywide trend and declining for two years after. A full spatial-temporal breakdown across all 77 areas was out of scope for this consolidation and remains notebook 04's responsibility.

## 5. Which weather conditions associate with crime?

- Citywide, temperature and crime associate at Spearman r = 0.552, but the relationship is season-dependent: Winter r = 0.548, Summer r = 0.083 (not statistically significant).
- Extreme cold is the single strongest weather effect (rank-biserial -0.686); extreme heat is next, and positive (+0.420).
- Violent crime is the most temperature-sensitive category (r = 0.640).
- An OLS model adjusting for season and weekend still finds `avg_temp`, `PRCP`, and `SNOW` significant (R-squared = 0.368) — weather adds information beyond a calendar proxy.
- Area-level heterogeneity is real: per-area Spearman r ranges from 0.013 to 0.371 (mean 0.168), well below the citywide-pooled 0.552. This is an expected artifact of aggregating 77 areas (noise cancels in the pooled figure), not an error — but it means the citywide number does not describe a typical single area.
- All of the above describe **association, not causation**.

## 6. Does weather improve predictive performance?

**Yes, modestly, and it is weather doing the work — not calendar position.**

Adding weather to calendar and historical crime features (under the tuned Random Forest configuration, evaluated with 5-fold chronological cross-validation) raises ROC-AUC from 0.548 +/- 0.020 to 0.563 +/- 0.014 and PR-AUC from 0.261 +/- 0.087 to 0.270 +/- 0.086 — a small but consistent gain given the tight fold-to-fold variance. F1 does not move (0.329 to 0.316, within noise). Adding the tested interaction terms (`avg_temp x is_weekend`, `avg_temp x season`, `is_rain x is_weekend`, `is_snow x is_weekend`) provides no further gain on any metric.

A follow-up robustness check isolated weather from calendar entirely. **Weather alone** (crime history + weather, no calendar features) reaches ROC-AUC 0.562 +/- 0.015 — statistically indistinguishable from the full feature set's 0.563 +/- 0.014 (3 of 5 folds favor the full set, p = 0.4375). **Calendar alone** trails at 0.548 +/- 0.020. The paired Wilcoxon test shows weather consistently beating calendar-only in all 5 folds, whether weather is added to calendar (p = 0.0625) or compared to calendar directly with no other change (p = 0.0625) — the strongest signal obtainable at this sample size. Adding calendar on top of weather adds almost nothing (3 of 5 folds, p = 0.4375).

This nuances, rather than contradicts, the feature-importance result in Section 8 below: calendar features dominate what the model uses to fit the training data, but weather alone carries nearly all of the out-of-fold ranking-quality signal. Impurity-based importance and cross-validated discrimination measure different things, and both results here are real.

## 7. Can high-crime community-days be classified reliably?

**Not reliably in an absolute sense, but genuinely better than chance — and better than the alternative candidate.** Tuned Random Forest reaches test F1 0.425 and ROC-AUC 0.589, retaining real discrimination on both classes (negative-class recall 0.40, positive-class recall 0.69).

Logistic Regression, the model actually selected by the project's F1-based selection rule (validation F1 0.492, the best of five candidates), fails this test outright: on test it predicts positive on 99.9% of rows (recall 0.999, negative-class recall 0.00), producing an F1 (0.436) that looks competitive only because the metric doesn't penalize this failure mode as harshly as accuracy does (accuracy 0.281 — worse than the majority-class baseline). This gap between what the selection rule chose and what actually generalizes is itself a finding, documented in [`methodology.md`](methodology.md).

## 8. Which features matter most?

By Random Forest's impurity-based importance: calendar position dominates. `week_of_year` (0.184), `year` (0.154), and `month` (0.124) combined account for roughly 46% of total importance. `avg_temp` (0.099) is the leading weather feature; `is_extreme_cold` (0.053) is the only weather flag in the top six. Historical crime features rank lower — `crime_rolling_14` (0.029) is the highest of that group.

This is a pattern in what the model relies on to split nodes, not evidence that calendar position causes crime, and — per Section 6 above — not the same thing as which features carry the most out-of-fold predictive signal.

## 9. Where does the model err?

**Unevenly across community areas.** The 10 weakest areas (26, 44, 1, 49, 2, 4, 10, 67, 66, 77) show error rates of 56%-60%, against 48% overall test error.

**On a seasonal cycle, not gradual drift.** January-April in both test years (2024, 2025) shows 17%-30% error, composed entirely of false negatives (false-positive rate exactly 0.000 in every one of those months). May-December shows 53%-78% error, composed almost entirely of false positives. The pattern repeats across both years rather than trending monotonically worse — pointing to a seasonal effect tied to the model's calendar-heavy reliance, not staleness as the test period progresses.

This lines up with the weather-linked error check: error rate is lower on extreme-cold days (30.3% vs. 54.3%) and snow days (32.3% vs. 53.1%) — both winter conditions, coinciding with the low-error months — and higher on extreme-heat days (63.9% vs. 50.8%), a summer condition coinciding with the high-error months.

## 10. Major limitations

See [`limitations.md`](limitations.md) for the full list.

## Model comparison summary

| Model | Split | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| Baseline (Dummy) | validation | 0.676 | 0.000 | 0.000 | 0.000 | 0.500 | 0.324 |
| Decision Tree | validation | 0.498 | 0.356 | 0.680 | 0.468 | 0.564 | 0.376 |
| Logistic Regression | validation | 0.347 | 0.329 | 0.973 | 0.492 | 0.582 | 0.397 |
| Random Forest (default) | validation | 0.573 | 0.375 | 0.474 | 0.419 | 0.571 | 0.391 |
| **Random Forest (tuned)** | validation | 0.491 | 0.356 | 0.705 | 0.473 | 0.587 | 0.402 |
| Logistic Regression | test | 0.281 | 0.279 | 0.999 | 0.436 | 0.548 | 0.315 |
| **Random Forest (tuned)** | test | 0.483 | 0.308 | 0.687 | 0.425 | 0.589 | 0.368 |

Random Forest (tuned) is the model this project treats as primary, for the reasons in Section 7 above and in `methodology.md`.

## Open items

1. Crime-category composition discrepancy between notebooks 04 and 06 (Section 1) — not formally reconciled.
2. `src/modeling/` (chronological-fold construction, metrics computation) does not yet exist; this logic is currently duplicated inline in notebooks 08 and 09.
