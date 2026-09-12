# PRAHARI Cost Model Evaluation

**Status:** NO RESEARCH CANDIDATE ADMITTED  
**Primary horizon:** 3 reporting months

The primary design is expanding-origin pseudo-future evaluation. For every fold, target outcomes mature before the test period; inner training precedes validation; validation precedes test. Imputation, scaling, calibration and thresholds are fit without test data. Minimum ranking support is 1,000 test anchors, 300 projects, 30 events, 500 training anchors, 20 training events and both classes in inner training/validation.

C1 Basic 3M has three admitted folds. Mean PR-AUCs were approximately 0.049 (rule), 0.102 (logistic), 0.056 (HistGB), 0.054 (RF), 0.063 (XGBoost) and 0.067 (equal vote). The logistic mean was driven by one stronger fold while its worst-fold PR-AUC was about 0.009 and recall about 0.027. The rule recalled about 0.266 with roughly 10.2 false alerts per 100 anchors, but its mean ECE was catastrophically high at about 0.280. The ensemble had zero mean recall at validation-selected thresholds. These trade-offs fail admission.

C2 results are descriptive only because no fold meets the support minimum. Compact C1 has only one admitted fold, so Basic-versus-Compact cannot support a general superiority claim. C1 6M has enough folds for research evaluation but cannot become an operational watch because no stable primary candidate exists. Fixed 12/18/24-month window outputs are support diagnostics only.

Calibration uses Platt scaling fitted on past validation data. Brier score, ECE and descriptive calibration slope/intercept are reported on test data. Project-cluster bootstrap, lead-time and contributor artifacts are intentionally withheld because there is no admitted final candidate.

Weighted voting and stacking are not admitted. July-month labels and model ranking remain machine-provisional.
