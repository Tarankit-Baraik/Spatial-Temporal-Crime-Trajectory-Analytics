# Limitations

## Data limitations

- **Crime data is reported and police-recorded, not a census of all actual crime.** Underreporting and enforcement patterns are not observable from this dataset and are not corrected for.
- **Classifications and records can change over time** as cases are investigated, reclassified, or closed. A record pulled today may not exactly match the same incident pulled at a later date.
- **Location is generalized to block level**, not exact coordinates — a deliberate privacy protection in the source data. No claim in this project relies on exact-coordinate precision.
- **Weather is approximated citywide from a single station** (NOAA GHCN-Daily, O'Hare, `USW00094846`). No community area's weather is measured directly; every area on a given day is assigned the same reading. This is a real, stated approximation, not treated as spatially exact.
- **The crime-category composition figures are internally inconsistent** between an earlier exploratory pass (notebook 04: violent 40.7% / property 34.8% / drug 14.9% / fraud 9.5%) and a later full-dataset computation (notebook 06: violent 31.2% / property 47.2% / drug 2.4% / other 19.1%). The notebook 06 figures are treated as the working numbers because they sum to the full cleaned dataset, but this has not been formally reconciled. See `findings.md`, Section 1.

## Target and modeling construct

- **`high_crime_day` is an analytical construct built for this project**, not an official city classification of any kind. It is defined relative to each community area's own historical 75th percentile, computed from the training period only.
- **Crime patterns drift over time.** The target's positive rate moves from 15.7% (2021) to a peak of 32.4% (2023) down to 24.5% (2025) — a real risk to model stability. The chronological train/validation/test split is designed to expose this drift, not eliminate it.
- **The weather-crime relationship reported throughout is an observational association, not a causal claim.** No causal design (e.g., a natural experiment, instrumental variable, or randomized intervention) is used anywhere in this project. Findings are worded as "associated with," never "causes."
- **Feature importance is not a causal ranking.** Random Forest's impurity-based importance describes what the model uses to split nodes on the training data; it does not describe what causes crime, and — per the weather-ablation robustness check — it does not necessarily describe what carries the strongest out-of-fold predictive signal either (see below).

## Model limitations

- **The project's own F1-based model-selection rule chose the wrong model to deploy.** It selected Logistic Regression (validation F1 0.492) over tuned Random Forest (validation F1 0.473), even though Random Forest had the better ROC-AUC and PR-AUC. On test, Logistic Regression degenerated to a near-constant positive classifier (recall 0.999, negative-class recall 0.00) — worse than the majority-class baseline on accuracy. Random Forest, not the model the stated selection rule chose, is the model this project treats as primary. Any reuse of this project's selection logic should account for this failure mode rather than trust F1 alone.
- **Random Forest's own predictions are not reliable at the level of a single date.** Its errors follow a seasonal cycle — false negatives dominate January-April, false positives dominate May-December, repeating across both test years — rather than being evenly distributed. A prediction made in isolation, without knowing which half of this cycle the date falls in, should be treated with corresponding caution.
- **Random Forest's predictions rely more on calendar position than on any area's own recent crime history**: `week_of_year`, `year`, and `month` account for roughly 46% of total feature importance combined. This is a real pattern in what the model learned, and it is the likely mechanical source of the seasonal error cycle above.
- **Whether weather's contribution survives without calendar features is now measured, and nuances the importance ranking above.** Weather alone reaches ROC-AUC statistically indistinguishable from the full feature set, while calendar alone trails meaningfully — the opposite emphasis from the impurity-importance ranking. Both results are real; they measure different things (what the model uses to fit training data vs. what generalizes across held-out folds), and neither should be read as contradicting the other.
- **The weather-ablation significance test has limited statistical power.** With only 5 cross-validation folds, a paired Wilcoxon signed-rank test cannot reach conventional significance (p < 0.05) at all, and its smallest possible p-value is 0.0625. Results are reported as directional evidence, not confirmatory hypothesis tests.
- **Ten community areas show meaningfully higher error rates than the rest** (56%-60% vs. 48% overall test error) and have not been individually investigated for a cause.

## Engineering / reproducibility gaps

- **`src/modeling/` does not exist.** Chronological-fold construction and metrics computation are currently duplicated inline in notebooks 08 and 09 rather than shared from a single module. Flagged, not yet fixed.
- **This project's own data has never been directly inspected by the assistant that built it.** Every notebook was authored fail-fast against real file paths and verified privately against a synthetic, schema-matched fixture before delivery, then filled in with real findings only after being executed locally and re-uploaded. This process is designed to prevent fabricated results, but it does mean no finding in this project was independently spot-checked against the raw source data by a second party.

## Scope not covered

- Individual-incident-level analysis (this project works at community area x date, not incident grain).
- Time-of-day or night/day breakdown — not present in the confirmed daily-aggregate schema; blueprint interaction terms that assumed this granularity (`snow x night`, `precip x time-of-day`) were dropped rather than approximated with a fabricated stand-in column.
- A full spatial-temporal treatment of how crime patterns shift across all 77 community areas over time (`findings.md`, Section 4, covers only the top 5 areas).
