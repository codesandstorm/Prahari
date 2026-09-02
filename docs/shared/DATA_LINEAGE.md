# Data lineage — Gate 2 April–June 2026 pilot

## Official PDF → raw source

- Inputs: canonical `SRC-2026-04`, `SRC-2026-05`, and `SRC-2026-06`
  manifest records.
- Outputs: immutable PDFs under `data/raw/2026/`.
- Transformation: none.
- Validation: manifest eligibility, file existence, SHA-256, page count, and
  text/table extractability.
- Provenance: `source_id` is the immutable source key; filename is descriptive.

## Raw source → validated extraction

- Inputs: the three canonical PDFs.
- Outputs: `ongoing_2026_04.csv`, `ongoing_2026_05.csv`, and
  `ongoing_2026_06.csv`.
- Transformation: month-specific, loss-minimized Table 6 extraction.
- Validation: table boundaries, natural serial inventory, structure,
  missingness, page diagnostics, source SHA, automated tests, and human review.
- Provenance: every observation retains source SHA, physical and printed page,
  table, method, extractor version, and deterministic raw-row locator.

## Validated extraction → identity continuity

- Inputs: only the three frozen extraction CSVs.
- Outputs: exact-code matches, metadata variations, unmatched sets, review
  candidates, summary, and manual identity sample.
- Transformation: exact raw Project Code intersection plus review-only text
  comparison. No fuzzy candidate is automatically accepted.
- Validation: input digests, row counts, Project Code uniqueness, conflicts,
  provenance counts, and human identity review.
- Provenance: observation IDs and raw source locators remain attached.

## Identity continuity → project master

- Input: the authorized exact-Project-Code identity rule and all three validated
  monthly observations.
- Output: `data/processed/pilot_2026_04_06/project_master.csv`.
- Transformation: deterministic `PRH-<project_code>` ID and source-derived
  first/latest observation selection.
- Validation: Project Code union, unique canonical IDs, observation counts, and
  presence-category reconciliation.
- Provenance: the current/latest representation retains the exact observation
  and source locator from which it was selected.

## Identity continuity → project month

- Inputs: all validated monthly observations.
- Output: `data/processed/pilot_2026_04_06/project_month.csv`.
- Transformation: column mapping only; no historical value overwrite and no
  business normalization.
- Validation: 5,815-row reconciliation, unique project-month key, master foreign
  key, source SHA, and exact observation/provenance equality.
- Provenance: every transformed row preserves source ID/SHA, physical/printed
  page, table, extraction method/version, and raw-row locator.

## Project month → temporal diagnostics

- Inputs: 1,951 exact-code April–May pairs, 1,825 exact-code May–June pairs,
  and 1,790 all-three-month identity chains.
- Outputs: longitudinal summary, temporal diagnostic/review CSVs, and manual
  sample.
- Transformation: categorical comparison of reported values. Numeric movement
  is used only for validation diagnostics.
- Validation: matched-pair count, categorical totals, provenance on both sides,
  deterministic sampling, and human review.
- Provenance: flagged records retain both May and June observation IDs and full
  source locators. The `APR_JUN_ONLY` pattern has a separate gap-review artifact;
  no May observation is filled or interpolated.

No downstream completion events, labels, features, risk scores, or ML datasets
are part of this lineage stage.
