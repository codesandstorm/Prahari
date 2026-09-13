# PRAHARI CUF Derived Features V1

Implementation Watch calculations are deterministic functions in `src/implementation_watch/features.py`. They return a value, availability, state, formula, raw inputs, and note.

- `physical_progress_gap = actual physical progress - scheduled physical progress`; a behind-plan signal fires at -10 percentage points under policy v1. Scheduled progress is never inferred.
- `financial_progress_gap = actual financial progress - scheduled financial progress`; computation requires explicitly compatible definitions and time basis, otherwise `SEMANTIC_MISMATCH`.
- `financial_physical_divergence = actual financial percentage - actual physical percentage`; absolute divergence of at least 15 percentage points is an attention signal, never an allegation.
- `consecutive_stagnant` counts trailing non-increasing progress transitions across exact consecutive calendar months. Missing reports, aggregate-only months, source gaps, and missing progress break the sequence.
- The existing `remaining_schedule_months`, `required_future_velocity`, `progress_vs_elapsed_gap`, and `low_progress_near_deadline` calculations are exposed without changing Compact V2 behavior.
- Milestone outputs are delayed count, maximum delay and slippage rate. Future due dates are not overdue; non-applicable and missing milestones remain distinct. Trend requires repeated compatible snapshots.
- Land outputs are confirmed remaining percentage, explicit acquisition-pending state, and a transparent expected-land-completion versus relevant-milestone conflict.
- ROW pending requires explicit applicability and pending status.
- Clearance counts preserve unknown categories. The v1 critical category list is CRZ, Environmental, Forest, and Defence; it is a versioned review policy, not a causal or predictive claim.
- An active tender means published and not awarded. Cycle days use publication-to-award, or publication-to-as-of for an active tender. Absence never implies award.
- Funding and cost-composition ratios are contextual only and do not trigger Watch V1.

All thresholds are policy rules, not learned scores and not official MoSPI risk definitions.
