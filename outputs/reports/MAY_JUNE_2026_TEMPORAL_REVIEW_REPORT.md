# May–June 2026 Exhaustive Temporal Review Report

## 1. Purpose

This review independently reconstructs the defined May–June temporal flags, creates a reviewer-friendly side-by-side artifact, and checks every flagged longitudinal observation against the frozen validated monthly extraction. It does not correct source values or interpret changes as errors, outcomes, features, or risk.

## 2. Input hashes

- May extracted CSV: `f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e`
- June extracted CSV: `bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9`
- May source PDF: `480d98632cd1b1d4fe70b58a5a753924b2735b0135e7c8507c1ec05ff2ddf005`
- June source PDF: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- Frozen `project_master.csv`: `f760d5ac9fcf62fb52a6ddd029719f6a0653fd22fcfb58663d350224ae9c8d86`
- Frozen `project_month.csv`: `188189b03a8fcb8f1e431840ef96ab466b1414eb686c08fda994d276c7cf8761`

## 3. Independent reconstruction and prior-set comparison

- Existing review rows / unique Project Codes: 88 / 88
- Recomputed review rows / unique Project Codes: 88 / 88
- Intersection: 88
- Existing-only: []
- Recomputed-only: []
- Exact Project Code set match: YES

The reconstruction reads `project_month.csv` and independently applies the documented primary policy. Agency, revised-cost, and revised-DoC changes are retained as secondary diagnostics and do not expand the primary review set.

## 4. Automated source equality

- Reviewed projects: 88
- Automated PASS: 88
- Automated FAIL: 0
- Provenance failures: 0
- Identity failures: 0

Every preserved May and June field was compared exactly with the Project Code-matched validated extraction row, including missing markers, dates, numerics, source identity, page information, extraction metadata, and raw row locator.

## 5. Primary flag summary

Percentages use 1,825 exact matched projects as the denominator. Numeric changes are June minus May.

| Flag | Count | Matched % | Minimum | Maximum | Median | Also has another primary flag |
|---|---:|---:|---:|---:|---:|---:|
| PROJECT_NAME_CHANGED | 6 | 0.3288% | n/a | n/a | n/a | 1 |
| APPROVAL_DATE_CHANGED | 3 | 0.1644% | n/a | n/a | n/a | 1 |
| START_DATE_CHANGED | 21 | 1.1507% | n/a | n/a | n/a | 0 |
| ORIGINAL_COST_CHANGED | 6 | 0.3288% | -290.04 | -24.85 | -127.10 | 2 |
| PHYSICAL_PROGRESS_DECREASED | 19 | 1.0411% | -13.1 | -0.06 | -1.5 | 2 |
| CUMULATIVE_EXPENDITURE_DECREASED | 38 | 2.0822% | -1238.7 | -0.01 | -5.655 | 4 |

## 6. Secondary diagnostics

- Agency changes among all matched projects: 577
- State changes among all matched projects: 0
- Original-target-DoC changes among all matched projects: 22
- Revised-cost changes among all matched projects: 7
- Revised-DoC changes among all matched projects: 319

## 7. Overlap and review order

- Projects with multiple primary flags: 5
- Primary-flag pair overlaps: `{"ORIGINAL_COST_CHANGED+CUMULATIVE_EXPENDITURE_DECREASED": 2, "PHYSICAL_PROGRESS_DECREASED+CUMULATIVE_EXPENDITURE_DECREASED": 2, "PROJECT_NAME_CHANGED+APPROVAL_DATE_CHANGED": 1}`

- PRIORITY_1: 1
- PRIORITY_2: 8
- PRIORITY_3: 21
- PRIORITY_4: 53
- PRIORITY_5: 5

`review_priority` is deterministic review ordering only. It is not a risk score, business priority, or model feature.

## 8. Defect findings

- Longitudinal transformation defects: 0
- Provenance defects: 0
- Identity defects: 0

## 9. Human review artifact

`validation/longitudinal/may_june_2026_temporal_review_88_MANUAL.csv`

Review each row against the cited May and June PDF pages and raw row locators. Populate only the six manual columns. Confirmation fields allow `YES`, `NO`, or `UNCERTAIN`. `manual_issue_type` allows `NONE`, `SOURCE_REPORTED_VARIATION`, `EXTRACTION_ERROR`, `LONGITUDINAL_TRANSFORMATION_ERROR`, `IDENTITY_ERROR`, `PROVENANCE_ERROR`, or `UNCERTAIN`.

Do not edit non-manual fields. If any source value, identity, mapping, or provenance is not confirmable, record `UNCERTAIN` rather than inferring a cause.

## 10. Scientific interpretation

The automated result establishes whether the longitudinal representation faithfully preserves the validated extracted rows. It does not establish that every PDF extraction is semantically correct; that requires the requested human source review. Decreases and metadata revisions remain reported observations, not errors or risk indicators.

## 11. Limitations

- The scope is May and June 2026 only.
- Automated equality is bounded by the already validated monthly extraction.
- PDF-level confirmation remains deliberately manual.
- No causal meaning is assigned to changes.
- No source, extraction, master, or project-month file was modified.
