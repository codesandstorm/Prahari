# PRAHARI Feature Contract

**Registry:** `data/metadata/prahari_feature_registry.csv`

**Version:** `compact-v2.1-calendar-safe`

**Status:** frozen for provisional research; validation pending

Every feature must be computable using information known at prediction month t. The exact frozen implementation is the 14-member `COMPACT_V2` tuple in `src/ml/feature_discovery_v2.py`, built by `src/ml/final_prediction.py`. CUF candidates are not part of this baseline and have no measured result.

## Frozen 14-feature baseline

`log_original_cost`, `planned_duration_months`, `project_age_months`, `expenditure_to_cost`, `physical_progress`, `physical_progress_missing`, `history_span_months`, `remaining_schedule_months`, `required_future_velocity`, `progress_vs_elapsed_gap`, `low_progress_near_deadline`, `consecutive_stagnant`, `cumulative_cost_revision_pct`, and `expenditure_velocity`.

An exact-tuple regression test prevents documentation or inference drift. The former 12-feature `features-v0.1` text was historical and is superseded by this contract; model behavior was not changed during reconciliation.

The current revised date defines S1 eligibility and cannot be a predictor. Future revised dates, actual completion, future cost, future progress, full-dataset peer statistics, and post-event information are blacklisted.

Missing numeric values are fitted with training-fold medians and explicit indicators where supported. Structural schema absence stays distinct from reported missingness. No backward fill, interpolation, global statistic, or future-derived normalization is allowed.

Agency is excluded from the provisional models because the raw field mixes ministry, owner, PSU, authority, railway organization, and implementing agency. Contractor features cannot be derived from it.

The registry is the controlling feature-level record. A feature not registered and approved for the relevant model must be rejected at training time.
