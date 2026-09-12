# PRAHARI Temporal Backtesting V2

The primary evaluation is expanding-window pseudo-future testing. For a test month T, a training anchor is admitted only when its complete outcome horizon ends before T. Preprocessing, imputation, calibration, alert thresholds and any ensemble weights must be fitted inside the temporally prior training data.

Predeclared test groups are F1 2023-04–2023-08, F2 2024-06–2024-10, F3 2025-03–2025-09 and F4 2025-10–2026-03. Each cohort recalculates admissibility. A fold needs at least 1,000 rows, 300 projects, 30 S1 events or 20 S2 events; otherwise it is descriptive only. Fixed rolling windows are sensitivity analysis, never the primary winner-selection path.

Final comparisons require PR-AUC, ROC-AUC, Brier score, calibration, alert burden, lead time and project-cluster uncertainty. No test fold may tune its own model or policy.
