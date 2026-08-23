# Modeling

Operational reference for `models/`. For why Random Forest is primary and what it found, see [`findings.md`](findings.md); for how the dataset and split were built, see [`methodology.md`](methodology.md).

## Files in `models/`

| File | Algorithm | Status |
|---|---|---|
| `random_forest.joblib` | `RandomForestClassifier`, tuned | **Primary model.** Use this one. |
| `logistic_regression.joblib` + `logistic_regression_scaler.joblib` | `LogisticRegression` | Selected by the project's F1 rule, degenerated on test (see below). Kept for the documented cautionary result, not for reuse. |
| `decision_tree.joblib` | `DecisionTreeClassifier` | Baseline candidate, not carried past notebook 08. |

## Primary model: `random_forest.joblib`

**Hyperparameters** (selected via `RandomizedSearchCV`, 5-fold chronological CV, training split only):

```
n_estimators      = 100
max_depth          = 5
min_samples_split  = 2
min_samples_leaf   = 4
max_features       = "log2"
class_weight       = "balanced_subsample"
random_state       = 42
```

**Trained on**: `data/processed/modeling_dataset.parquet`, `split == "train"` (2021-2022, 54,054 rows).

**Input schema — 30 columns, exact order matters.** Do not hardcode a column list to feed this model. Load it and read `feature_names_in_` directly:

```python
import joblib
model = joblib.load("models/random_forest.joblib")
print(model.feature_names_in_)   # canonical column order, from how it was fit
```

Reconstructing the input requires: casting the 7 boolean feature columns to int, one-hot encoding `season` with `drop_first=True` (drops `Fall`), and reindexing to `feature_names_in_`. See notebook 09, Section 04, for the exact code.

**Performance**

| Split | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Validation | 0.491 | 0.356 | 0.705 | 0.473 | 0.587 | 0.402 |
| Test | 0.483 | 0.308 | 0.687 | 0.425 | 0.589 | 0.368 |
| CV (5-fold, train) | -- | -- | -- | 0.326 | -- | -- |

Negative-class recall on test is 0.40 — a genuine, non-degenerate classifier (contrast below).

## Secondary: `logistic_regression.joblib`

Requires `logistic_regression_scaler.joblib` applied to inputs first (features were standardized before fitting; Random Forest was not).

Selected on validation (F1 0.492, best of 5 candidates) by the project's stated selection rule. **Do not deploy this model** — on test it predicts positive on 99.9% of rows (recall 0.999, negative-class recall 0.00, accuracy 0.281, below the majority-class baseline). Kept in `models/` only so the failure is reproducible, not because it is usable.

## Reproducing training

Run `08_model_training_and_comparison.ipynb` in full against `data/processed/modeling_dataset.parquet`. It rebuilds the baseline, Logistic Regression, Decision Tree, and both Random Forest variants, runs the `RandomizedSearchCV` tuning pass, and overwrites everything in `models/`. Chronological CV folds are constructed with `TimeSeriesSplit` over unique training dates (not a random k-fold) — the same construction is duplicated in notebook 09 for its ablation study, since `src/modeling/` does not yet exist (see `limitations.md`).

## Loading and predicting

```python
import joblib
import pandas as pd

model = joblib.load("models/random_forest.joblib")
df = pd.read_parquet("data/processed/modeling_dataset.parquet")
df = df[df["split"] == "test"].copy()

bool_cols = [c for c in df.columns if df[c].dtype == bool]
df[bool_cols] = df[bool_cols].astype(int)
df = pd.get_dummies(df, columns=["season"], drop_first=True)
X = df.reindex(columns=model.feature_names_in_)

predictions = model.predict(X)
probabilities = model.predict_proba(X)[:, 1]
```
