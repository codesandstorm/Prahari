# PRAHARI Feature Contract

**Registry:** `data/metadata/prahari_feature_registry.csv`

**Version:** `features-v0.1`

**Status:** frozen for provisional research; validation pending

Every feature must be computable using information known at prediction month t. Model A uses six current CUF-equivalent fields. Model B adds six temporal/data-quality features. Model C has no measured result because the required additional fields are unavailable.

## Model A

`log_original_cost`, `planned_duration_months`, `project_age_months`, `expenditure_to_cost`, `physical_progress`, and `physical_progress_missing`.

## Model B additions

`progress_delta_1m`, `progress_delta_3m`, `expenditure_delta_1m`, `stagnant_progress_2m`, `history_months`, and `correction_count`.

The current revised date defines S1 eligibility and cannot be a predictor. Future revised dates, actual completion, future cost, future progress, full-dataset peer statistics, and post-event information are blacklisted.

Missing numeric values are fitted with training-fold medians and explicit indicators where supported. Structural schema absence stays distinct from reported missingness. No backward fill, interpolation, global statistic, or future-derived normalization is allowed.

Agency is excluded from the provisional models because the raw field mixes ministry, owner, PSU, authority, railway organization, and implementing agency. Contractor features cannot be derived from it.

The registry is the controlling feature-level record. A feature not registered and approved for the relevant model must be rejected at training time.
