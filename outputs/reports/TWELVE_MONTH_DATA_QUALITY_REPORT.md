# PRAHARI Twelve-Month Data Quality Report

**Dataset:** `gate2-12m-2025-07-2026-06-provisional-v0.1`

**Window:** July 2025–June 2026

**Decision:** Automated gates passed; human review is pending for the nine newly extracted months.

**Permitted use:** Engineering only. This is not a final Gate 2 freeze and contains no labels, features, predictions, or risk scores.

## Source integrity and inventory

All 12 expected PDFs exist under `data/raw/`, are text-extractable, have distinct SHA-256 hashes, and retained their pre-build hashes. The source manifest records canonical relative paths, page counts, sizes, hashes, and eligibility. April–June source and extraction hashes, plus both prior pilot datasets, remain unchanged.

| Month | Source ID | PDF pages | PDF SHA-256 | Official ongoing | Accepted | Gate |
|---|---|---:|---|---:|---:|---|
| 2025-07 | SRC-2025-07-P01 | 67 | `1064c963…1508` | 791 | 791 | PASS_AUTOMATED |
| 2025-08 | SRC-2025-08 | 67 | `7b28c68c…f2c8` | 800 | 800 | PASS_AUTOMATED |
| 2025-09 | SRC-2025-09 | 72 | `520f100f…f318` | 794 | 794 | PASS_AUTOMATED |
| 2025-10 | SRC-2025-10 | 73 | `4817bb54…bc3` | 820 | 820 | PASS_AUTOMATED |
| 2025-11 | SRC-2025-11 | 73 | `db9e2eff…eb9` | 823 | 823 | PASS_AUTOMATED |
| 2025-12 | SRC-2025-12 | 108 | `07f56e54…2401` | 1,392 | 1,392 | PASS_AUTOMATED |
| 2026-01 | SRC-2026-01 | 134 | `9c043ad4…4c83` | 1,702 | 1,702 | PASS_AUTOMATED |
| 2026-02 | SRC-2026-02 | 168 | `f29010c2…7df9` | 1,948 | 1,948 | PASS_AUTOMATED |
| 2026-03 | SRC-2026-03 | 157 | `e1041152…0253` | 1,941 | 1,941 | PASS_AUTOMATED |
| 2026-04 | SRC-2026-04 | 163 | `90a6959e…18d5` | 1,981 | 1,981 | VALIDATED_FROZEN |
| 2026-05 | SRC-2026-05 | 163 | `480d9863…f005` | 1,987 | 1,987 | VALIDATED_FROZEN |
| 2026-06 | SRC-2026-06 | 161 | `d26872ac…8a15` | 1,847 | 1,847 | VALIDATED_FROZEN |

## Extraction and structural reconciliation

Every newly processed raw table row is accounted for as a project row or an explicit structural class. Project rows exactly equal each independently sourced official count. Unresolved rows are zero in all nine new months. Serial sequences are exactly 1 through the official count, with no missing, duplicate, or out-of-order serials. Project Code is complete, numeric, whitespace-clean, and unique within every month.

| Month | Raw table rows | Projects | Structural | Unresolved |
|---|---:|---:|---:|---:|
| 2025-07 | 910 | 791 | 119 | 0 |
| 2025-08 | 902 | 800 | 102 | 0 |
| 2025-09 | 903 | 794 | 109 | 0 |
| 2025-10 | 932 | 820 | 112 | 0 |
| 2025-11 | 932 | 823 | 109 | 0 |
| 2025-12 | 1,535 | 1,392 | 143 | 0 |
| 2026-01 | 1,867 | 1,702 | 165 | 0 |
| 2026-02 | 2,141 | 1,948 | 193 | 0 |
| 2026-03 | 2,136 | 1,941 | 195 | 0 |

Detailed class counts and page diagnostics are stored in each monthly extraction summary. Structural labels originate in the existing classifier (`REPEATED_HEADER`, `SECTION_HEADING`, `TOTAL`, `BLANK`, and `OTHER_NON_PROJECT`); together they implement the required structural-accounting categories without silent row loss.

## Field quality and identifier availability

No reported value was imputed or corrected. Across each new month, all populated date/DoC values conform to `MM/YYYY`, and all populated cost, expenditure, and progress values are numeric. Detailed parsed, missing, malformed, unusual-token, and percentage results are machine-readable in the monthly summaries.

| Month | Missing approval | start | original DoC | revised DoC | Legacy populated / unique / duplicate | PMGID populated |
|---|---:|---:|---:|---:|---|---:|
| 2025-07 | 3 | 791 | 0 | 263 | 0 / 0 / 0 | 0 |
| 2025-08 | 280 | 5 | 0 | 250 | 0 / 0 / 0 | 0 |
| 2025-09 | 94 | 3 | 0 | 239 | 0 / 0 / 0 | 0 |
| 2025-10 | 24 | 1 | 0 | 251 | 0 / 0 / 0 | 0 |
| 2025-11 | 12 | 1 | 0 | 251 | 0 / 0 / 0 | 0 |
| 2025-12 | 19 | 0 | 0 | 525 | 0 / 0 / 0 | 0 |
| 2026-01 | 44 | 0 | 0 | 768 | 0 / 0 / 0 | 0 |
| 2026-02 | 54 | 0 | 0 | 963 | 1,190 / 1,133 / 57 | 0 |
| 2026-03 | 17 | 0 | 0 | 347 | 1,189 / 1,129 / 60 | 0 |
| 2026-04 | 11 | 0 | 0 | 354 | 1,184 / 1,124 / 60 | 1,213 |
| 2026-05 | 22 | 11 | 11 | 352 | 1,170 / 1,110 / 60 | 1,201 |
| 2026-06 | 19 | 0 | 0 | 308 | 0 / 0 / 0 | 0 |

Legacy OCMS and PMGID are descriptive source fields, not canonical identifiers; neither is assumed complete or unique. The absence of populated values in a month is preserved as reported and is not inferred from schema family.

## Provenance and identity continuity

All 16,826 project-month observations retain source ID and SHA-256, reporting month, physical and printed page, table identifiers, raw row locator, extraction method, and extractor version. Provenance validation and within-source locator uniqueness failures are zero.

Exact Project Code matching across the 11 adjacent boundaries produced 14,583 matched transitions and zero identity conflicts. Boundary-level exact/left-only/right-only results are in `validation/longitudinal/twelve_month/pairwise_identity_continuity.csv`. No fuzzy identity links were created.

The canonical union contains 2,207 unique `PRH-<Project Code>` identities and 16,826 unique project-month keys. Thirty-six identities contain an internal presence gap; those absences remain absences, with no synthetic rows or completion/new/cancellation inference.

## Temporal QA

The exhaustive primary-QA artifact contains 1,639 matched transitions with at least one primary flag. Counts are: approval date changed 887; start date changed 837; cumulative expenditure decreased 358; physical progress decreased 149; project name changed 56; original cost changed 48. These flags surface official-report differences for review; they are not corrections, labels, features, or risk signals.

## Human validation and limitations

- Deterministic seed-26103 samples contain 20 rows for each of the nine new months, with empty manual-review fields.
- Automated validation passed, but those 180 sampled rows have not yet been manually confirmed against the PDFs.
- April–June remain the pre-existing validated/frozen pilot; this build reads rather than recreates them.
- Exact modern-period Project Code identity is supported within this window only. Absence from a report has no lifecycle meaning.
- Source-reported missingness, identifier duplication, and temporal reversals are preserved. They must not be treated as data-engineering errors without source review.
- The dataset is suitable for provisional ML engineering, leakage research, and pipeline development—not final accuracy claims, model selection, feature freeze, thresholds, or held-out metrics.
