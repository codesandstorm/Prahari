---
title: PRAHARI Schedule Model Selection V3
status: CURRENT
---

# PRAHARI Schedule Model Selection V3

Selection considers target validity, leakage, multiple admitted folds, PR-AUC, worst-fold behavior, recall, false-alert burden, calibration, lead time, uncertainty and simplicity—in that order. Rule, Logistic Regression, HistGradientBoosting, Random Forest, XGBoost and equal soft voting were evaluated on aligned anchors.

S1 and S2 are both `WITHHELD_NO_ADMITTED_CANDIDATE` because each has only one admitted fold after strict correction/reversal censoring. Machine target truth also remains unvalidated, so neither can complete the full admission chain through stability, lead time and uncertainty.

Weighted voting is not justified after equal voting, and stacking lacks sufficient independent temporal out-of-fold layers. No deployable `pipeline.joblib` or contributor explanation is created. Backend inference remains fail-closed.
