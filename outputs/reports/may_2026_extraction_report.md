# May 2026 Table 6 Extraction Report

## Source and schema

- Source: `SRC-2026-05` / `FlashReport_2026_05.pdf`
- SHA-256: `480d98632cd1b1d4fe70b58a5a753924b2735b0135e7c8507c1ec05ff2ddf005`
- Schema: `PAIMANA_V2` / `HIGH`
- Extractor: `extractor_paimana_may_table6:0.1.0`
- Method: `pdfplumber_table`
- May versus June: `COMPATIBLE_VARIATION`

## Boundaries and reconciliation

- Physical title page: 53
- Physical data pages: 54–162
- Printed data pages: 53–161
- Expected count: 1,987, stated on physical page 4 / printed page 3
- Accepted: 1987
- Unresolved: 0
- Difference: 0
- Duplicate serials/locators/observations: 0/0/0
- Natural serial sequence 1–1987: True

## Structure and fields

The verified eight-column PAIMANA V2 structure was extracted as raw project,
agency, identifiers, state, dates, costs, expenditure, progress, full compound
cells, and mandatory May provenance. Ministry/sector carry-forward,
normalization, linking, features, labels, outcomes, and risk values are omitted.

The May-specific compatible variation is 11 DoC cells containing only `(-)`.
Their complete source cell is preserved; target is empty and revised DoC is `-`.

## Missingness

- `serial_number_raw`: 0 (0.0%)
- `project_name_raw`: 0 (0.0%)
- `agency_raw`: 0 (0.0%)
- `project_code_raw`: 0 (0.0%)
- `legacy_ocms_code_raw`: 817 (41.12%)
- `pmgid_raw`: 786 (39.56%)
- `state_raw`: 0 (0.0%)
- `approval_date_raw`: 0 (0.0%)
- `start_date_raw`: 11 (0.55%)
- `original_target_doc_raw`: 11 (0.55%)
- `revised_doc_raw`: 352 (17.72%)
- `original_cost_raw`: 0 (0.0%)
- `revised_cost_raw`: 0 (0.0%)
- `cumulative_expenditure_raw`: 0 (0.0%)
- `physical_progress_raw`: 0 (0.0%)
- `project_identity_cell_raw`: 0 (0.0%)
- `approval_start_cell_raw`: 0 (0.0%)
- `doc_cell_raw`: 0 (0.0%)
- `cost_cell_raw`: 0 (0.0%)

## Page diagnostics

The JSON summary contains all 109 page-level diagnostic records.

- PDF 162: COUNT_OUTLIER (7 rows)

## Artifacts and assessment

- Raw extraction: `C:/Users/ASUS/Documents/Projects/PRAHARI/data/extracted/ongoing/ongoing_2026_05.csv`
- Unresolved review: `C:/Users/ASUS/Documents/Projects/PRAHARI/data/extracted/review/ongoing_2026_05_unresolved_rows.csv`
- Deterministic manual sample: `C:/Users/ASUS/Documents/Projects/PRAHARI/validation/extraction_validation/may_2026_manual_sample_30.csv`

Ready for independent human review. This does not authorize project linking,
normalization, another month, or historical expansion.
