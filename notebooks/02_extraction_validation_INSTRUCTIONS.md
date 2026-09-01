# Notebook: 02 — Extraction Validation

**Purpose:** Cross-check extracted rows against the source PDF manually.

**Status:** NOT STARTED — requires extraction output from 01.

## Instructions

1. After running extraction for July 2026, load `data/extracted/ongoing/ongoing_2026_07.csv`.
2. Randomly sample 30 rows using `df.sample(30, random_state=42)`.
3. Open the source PDF and navigate to the pages recorded in `source_page`.
4. For each sampled row, verify the following fields against the PDF:
   - `project_code`
   - `project_name`
   - `original_cost`
   - `revised_cost`
   - `cumulative_expenditure`
   - `physical_progress_pct`
   - `revised_doc`
5. Record each check in `data/validation/extraction_validation.csv`.
6. Compute overall match rate.
7. Investigate any mismatches — extraction bug vs. PDF ambiguity?

## Target Accuracy

Aim for ≥ 95% field-level match rate before proceeding to normalization.
If below 95%, investigate extraction logic before continuing.
