# PRAHARI Prediction Comparison V1

**Status:** RESEARCH ONLY

The canonical table is `outputs/ml/final_prediction_v1/model_comparison.csv`. All models receive the same target-specific cohort, Compact V2 order, chronological split, training-derived imputation and validation review-capacity threshold.

Models are the transparent rule, Logistic Regression, HistGradientBoosting, Random Forest and XGBoost. PR-AUC is primary; ROC-AUC is secondary. Brier, recall, precision, false alerts, confusion counts, rolling folds, history bands and event-level lead time are also reported.

These results are development/finalization evidence because the historical test months were previously inspected. They are not untouched confirmation. Historical Pavitra outputs remain evidence but are superseded for final inference by the canonical V1 artifacts.

## Development-test comparison

| Target | Model | PR-AUC | Recall | False alerts/100 | Brier |
|---|---|---:|---:|---:|---:|
| S1 | Rule | 0.308 | 0.564 | 29.62 | 0.413 |
| S1 | Logistic | 0.593 | 0.481 | 6.03 | 0.250 |
| S1 | HistGB | 0.670 | 0.557 | 5.47 | 0.186 |
| S1 | Random Forest | 0.697 | 0.514 | 5.00 | 0.195 |
| S1 | XGBoost | 0.740 | 0.549 | 4.74 | 0.178 |
| S2 | Rule | 0.523 | 0.407 | 20.03 | 0.512 |
| S2 | Logistic | 0.529 | 0.095 | 7.56 | 0.326 |
| S2 | HistGB | 0.727 | 0.358 | 5.72 | 0.219 |
| S2 | Random Forest | 0.773 | 0.427 | 6.20 | 0.202 |
| S2 | XGBoost | 0.774 | 0.381 | 5.10 | 0.202 |

HistGB is retained as the conservative serialized research candidate because its configuration was already reviewed, it is reproducible without an extra model runtime, and it provides a stable shared implementation for S1/S2. This is not a claim that it won every metric. Operational selection remains blocked by human label validation and later calibration confirmation.
