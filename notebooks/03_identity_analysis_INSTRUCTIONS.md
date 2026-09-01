# Notebook: 03 — Identity Analysis

**Purpose:** Investigate cross-report project identity using available identifiers.

**Status:** NOT STARTED — requires three months of extracted data.

## Instructions

1. Load `data/extracted/ongoing/ongoing_2026_05.csv`, `_06.csv`, `_07.csv`.
2. Check: are all `project_code` values in July present in June? In May?
3. How many project codes are in July but NOT in June (new projects)?
4. How many project codes are in June but NOT in July (completed / dropped)?
5. For matched project codes: are `project_name`, `agency`, `state` consistent?
6. What percentage of rows have `legacy_ocms_code` populated?
7. What percentage of rows have `pmgid` populated?
8. Are any `project_code` values duplicated within a single month?
9. Save findings to `data/validation/identity_audit.csv`.
10. Update `docs/PROJECT_IDENTITY_ANALYSIS.md` Q1–Q10 with VERIFIED answers.
