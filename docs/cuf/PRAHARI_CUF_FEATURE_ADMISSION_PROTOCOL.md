# PRAHARI CUF Feature Admission Protocol

No CUF field enters Schedule or Cost models merely because it is official or plausible. Admission requires, in order: availability, exact definition, as-of safety, identity support, missingness audit, distribution audit, temporal stability, leakage audit, incremental model test, paired ablation, operational metrics, robustness, explainability, and an explicit promotion decision.

Allowed decisions are `PROMOTED`, `RETAINED_FOR_RESEARCH`, `REJECTED`, and `NOT_TESTABLE_WITH_CURRENT_DATA`.

The frozen E0 baseline is Compact V2.1 with 14 features. Definitions E1-E10 are stored in `config/cuf_experiment_registry.json`: physical gap, financial gap, milestone, land, clearance, tender, ROW, funding, all safe families, then leave-one-family-out. They have not been executed. Future tests must keep targets, cohorts, chronology, imputation and threshold-selection procedure identical, and compare PR-AUC, recall at review capacity, false alerts per 100, precision, Brier/calibration, fold stability and lead time.

Actual completion, completion cost, future revisions, future progress/expenditure and post-event information are blacklisted. Full-dataset peer statistics require training-fold-only derivation. Promotion requires human/domain validation where semantics depend on approvals or administrative status.
