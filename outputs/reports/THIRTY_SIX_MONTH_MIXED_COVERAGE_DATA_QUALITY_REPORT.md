# PRAHARI 36-Month-Window Mixed-Coverage Data Quality Report

**Window:** July 2023--June 2026

**Coverage:** 30 project-level snapshots, 5 aggregate-only reports, 1 missing source

**Status:** PROVISIONAL - MIXED COVERAGE - HUMAN VALIDATION PENDING

## Core result

- 18 newly extracted historical project-level months: 31,500 rows.
- Combined project-month table: 48,326 actual observations.
- Canonical identities: 3,417, using exact source identifiers and verified unambiguous Legacy OCMS bridges only.
- Duplicate canonical project-month keys: zero.
- Unresolved digit-led rows in accepted monthly inventories: zero.
- Each new month reconciles accepted count = official count = complete serial sequence.
- Existing 12-month, two-month, three-month, and April--June frozen artifacts passed the protected-hash audit.
- July 2026 is excluded because it is byte-identical to June 2026.

## Coverage gaps

Aggregate-only: 2023-12, 2024-04, 2024-05, 2024-08, 2024-09. Missing: 2025-02. These months appear in `report_month.csv` but never in `project_month.csv`. Aggregate artifacts are separate and must not be used to impute projects.

## Schemas and provenance

OCMS inventories use seven logical cells and embedded official codes. PAIMANA historical inventories have seven stable rightmost fields with optional state/sector columns. Every extracted row records source ID/hash, reporting month, physical/printed page, table, extractor version, and raw locator. Schema selection is structural and `UNKNOWN` fails closed.

## Identity limitations

The exact Legacy OCMS bridge supplies 1,122 unambiguous mappings from the frozen modern data. Thirty Legacy OCMS values map ambiguously to multiple modern Project Codes and are deliberately not bridged. No name, agency, state, or cost similarity is used automatically.

## Temporal limitations

Adjacent stored observations are not assumed one month apart. The dataset records previous/next observed month, interval length, and a gap flag. Future targets crossing unavailable source months must be censored or explicitly classified as partially observable; absence cannot be a negative outcome.

## Human validation

Deterministic 20-row samples (seed 26103) exist for all 18 new months. Human confirmation fields remain empty. Until those checks are completed, the data is not training-ready and must not support operational claims.
