# June 2026 Table 6 Extraction Report

## Source identity and integrity

- Source ID: `SRC-2026-06`
- SHA-256: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- Pre-extraction SHA: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- Post-extraction SHA: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- Schema: `PAIMANA_V2` / `HIGH`
- Extractor: `extractor_paimana_table6:0.1.0`
- Method: `pdfplumber_table`

## Boundaries and reconciliation

- Table: Table 6 — All Ongoing Projects
- Physical title page: 58
- Physical data pages: 59–159
- Printed data pages: 58–158
- Expected report count: 1847
- Accepted project rows: 1847
- Unresolved rows: 0
- Difference: 0
- Duplicate raw locators: 0
- Duplicate serials: 0
- Rejected structural/non-project rows: 180

## Extracted fields

Raw project/agency/identifier, state, approval/start date, target/revised DoC,
original/revised cost, expenditure, physical progress, complete source cells,
and mandatory provenance fields. No business normalization was performed.

Fields intentionally omitted: ministry, sector, normalized values, cross-month
identity, labels, features, and risk values.

## Missingness

- `serial_number_raw`: 0 (0.0%)
- `project_name_raw`: 0 (0.0%)
- `agency_raw`: 0 (0.0%)
- `project_code_raw`: 0 (0.0%)
- `legacy_ocms_code_raw`: 1847 (100.0%)
- `pmgid_raw`: 1847 (100.0%)
- `state_raw`: 0 (0.0%)
- `approval_date_raw`: 0 (0.0%)
- `start_date_raw`: 0 (0.0%)
- `original_target_doc_raw`: 0 (0.0%)
- `revised_doc_raw`: 308 (16.68%)
- `original_cost_raw`: 0 (0.0%)
- `revised_cost_raw`: 0 (0.0%)
- `cumulative_expenditure_raw`: 0 (0.0%)
- `physical_progress_raw`: 0 (0.0%)
- `project_identity_cell_raw`: 0 (0.0%)
- `approval_start_cell_raw`: 0 (0.0%)
- `doc_cell_raw`: 0 (0.0%)
- `cost_cell_raw`: 0 (0.0%)

## Page diagnostics

The JSON summary contains all page-level counts.

- None under the declared page-count thresholds.

## Ambiguities and review

Legacy OCMS Code and PMGID columns exist but contain the source missing marker
`-` throughout this report. Section headings were not carried forward into
project records. Ambiguous numeric rows would be routed to review rather than
guessed.

- Raw extraction: `C:/Users/ASUS/Documents/Projects/PRAHARI/data/extracted/ongoing/ongoing_2026_06.csv`
- Unresolved review: `C:/Users/ASUS/Documents/Projects/PRAHARI/data/extracted/review/ongoing_2026_06_unresolved_rows.csv`
- Deterministic 30-row manual sample: `C:/Users/ASUS/Documents/Projects/PRAHARI/validation/extraction_validation/june_2026_manual_sample_30.csv`

## Assessment

Ready for independent manual review. This report does not authorize processing
another month or constructing analytical project tables.
