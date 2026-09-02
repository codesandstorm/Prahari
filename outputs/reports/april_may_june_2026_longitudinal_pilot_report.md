# April-May-June 2026 Longitudinal Pilot Report

## Dataset and inputs

- Version: `gate2-pilot-2026-04-06-v1`
- Frozen extraction hashes: `{"2026-04": "55d84996925b4d5d0f2bb3bc9367a685c2ad49a14c009acddc7662b0b9ee11dd", "2026-05": "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e", "2026-06": "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9"}`
- Monthly rows: `{"2026-04": 1981, "2026-05": 1987, "2026-06": 1847}`
- Project-month rows: 5815
- Unique project union: 2038
- Three-month exact intersection: 1790

## Identity continuity

- April-May: `{"ambiguous": 0, "conflicts": 0, "left_only": 30, "matches": 1951, "right_only": 36, "verified_exact": 1487}`
- May-June independently recomputed: `{"ambiguous": 0, "conflicts": 0, "left_only": 162, "matches": 1825, "right_only": 22, "verified_exact": 1060}`
- Presence patterns: `{"APR_JUN_ONLY": 1, "APR_MAY_JUN": 1790, "APR_MAY_ONLY": 161, "APR_ONLY": 29, "JUN_ONLY": 21, "MAY_JUN_ONLY": 35, "MAY_ONLY": 1}`
- Duplicate Project Codes / canonical IDs / project-month keys: 0 / 0 / 0
- Identity conflicts / ambiguous accepted links: 0 / 0

Presence patterns describe observation availability only. They do not mean new, completed, dropped, terminated, or cancelled.

## Metadata and temporal diagnostics

- All-three metadata variations: `{"agency_raw": 573, "approval_date_raw": 2, "original_cost_raw": 10, "original_target_doc_raw": 18, "project_name_raw": 6, "revised_cost_raw": 18, "revised_doc_raw": 621, "start_date_raw": 11, "state_raw": 0}`
- Boundary flag counts: `{"APR_TO_MAY": {"AGENCY_CHANGED": 4, "APPROVAL_DATE_CHANGED": 2, "CUMULATIVE_EXPENDITURE_DECREASED": 39, "ORIGINAL_COST_CHANGED": 4, "ORIGINAL_TARGET_DOC_CHANGED": 7, "PHYSICAL_PROGRESS_DECREASED": 35, "PROJECT_NAME_CHANGED": 1, "REVISED_COST_CHANGED": 11, "REVISED_DOC_CHANGED": 450, "START_DATE_CHANGED": 2, "STATE_CHANGED": 0}, "MAY_TO_JUN": {"AGENCY_CHANGED": 577, "APPROVAL_DATE_CHANGED": 3, "CUMULATIVE_EXPENDITURE_DECREASED": 38, "ORIGINAL_COST_CHANGED": 6, "ORIGINAL_TARGET_DOC_CHANGED": 22, "PHYSICAL_PROGRESS_DECREASED": 19, "PROJECT_NAME_CHANGED": 6, "REVISED_COST_CHANGED": 7, "REVISED_DOC_CHANGED": 319, "START_DATE_CHANGED": 21, "STATE_CHANGED": 0}}`
- Descriptive reversal counts: `{"agency_reversion": 0, "expenditure_reversal": 49, "progress_reversal": 33, "project_name_reversion": 0, "revised_cost_reversal": 0, "state_reversion": 0}`
- April-June presence-gap cases: 1
- Exhaustive primary-flag review projects: 158

Changes and reversals are preserved source observations for review. They are not corrected or interpreted as risk.

## Provenance and review

- Provenance failures: 0
- Duplicate source/locator keys: 0
- Identity sample: `validation/identity_continuity/april_may_june_2026_manual_identity_sample.csv`
- Temporal sample: `validation/longitudinal/april_may_june_2026_temporal_sample.csv`
- Exhaustive review: `validation/longitudinal/april_may_june_2026_temporal_review.csv`
- Presence-gap review: `validation/identity_continuity/april_may_june_2026_presence_gap_review.csv`

## Limits

This pilot uses exact Project Code only for the validated April-June PAIMANA V2 period. It preserves every monthly value and source locator. No completion inference, outcome, target, label, feature, prediction, risk score, confidence score, or alert priority was created. Human validation of the new identity and temporal artifacts remains required.
