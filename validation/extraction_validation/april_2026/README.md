# April 2026 Human Extraction Review

**Status:** HUMAN VALIDATION PENDING

Review every row in `april_2026_manual_sample.csv`. Populate only the six `manual_*`, `reviewer`, and `review_notes` columns; do not edit source or provenance columns.

For each sample row:

1. Open `data/raw/2026/FlashReport_2026_04.pdf`.
2. Go to `pdf_page_index` and confirm `printed_page_number`.
3. Use `raw_row_locator` to identify the table and row.
4. Verify the serial and Project Code.
5. Verify project name, agency, and state.
6. Verify approval and start dates.
7. Verify original and revised DoC.
8. Verify original cost, revised cost, and cumulative expenditure.
9. Verify physical progress.
10. Verify that the source ID, table, page, and locator describe that row.

Allowed confirmation values are `YES`, `NO`, and `UNCERTAIN`. Do not correct an unusual official value. Use `UNCERTAIN` and explain the ambiguity in `review_notes`.
