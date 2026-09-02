# May–June 2026 Longitudinal Pilot Report

## Inputs and identity

- Frozen May extraction: `f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e` (1987 observations)
- Frozen June extraction: `bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9` (1847 observations)
- Identity method: exact raw Project Code
- Internal ID: `PRH-<project_code>`
- Dataset version: `gate2-pilot-2026-05-06-v1`

## Reconciliation

- Project union / master rows: 2009
- Project-month observations: 3834
- May only / May and June / June only: 162 / 1825 / 22
- Duplicate master IDs / project-month keys: 0 / 0

Presence is observational. It is not a completion, addition, cancellation, or
removal label.

## Historical/static-field diagnostics

- Name changes: 6
- Agency changes: 577
- State changes: 0
- Approval-date changes: 3
- Start-date changes: 21
- Original-cost changes: 6
- Revised-cost changes: 7
- Revised-DoC changes: 319

Historical May values remain in the May ProjectMonth rows; June values never
overwrite them. Master `current_*` values mean latest reported values in this
two-month pilot only.

## Temporal diagnostics and review

- Physical-progress decreases: 19
- Cumulative-expenditure decreases: 38
- Temporal-review rows: 88

Flags are review diagnostics, not corrections, features, labels, outcomes, or
risk assessments. Every matched diagnostic and review row retains both source
observation IDs, SHAs, pages, and raw locators.

## Artifacts and limitations

- Manual sample: `validation/longitudinal/may_june_2026_manual_longitudinal_sample_30.csv`
- Known limitations: ["Identity rule validated only for May-June 2026.", "Presence does not establish completion, removal, or addition.", "Temporal movements are diagnostics, not corrected facts or ML features.", "Human longitudinal sample review is pending."]

The pilot is ready for human longitudinal validation. Expansion to another
month or construction of completion/ML artifacts is not authorized by this run.
