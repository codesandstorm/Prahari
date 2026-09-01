# Data Dictionary Notes

**Document Purpose:** Working notes on field definitions. This feeds into
`data/metadata/data_dictionary.csv`.  
**Status:** DRAFT — populated from project brief. All fields marked appropriately.

---

## Status Definitions

| Status | Meaning |
|---|---|
| `VERIFIED` | Directly demonstrated by source/data/code |
| `PLAUSIBLE` | Reasonable but not yet demonstrated |
| `UNKNOWN` | Insufficient evidence |
| `REJECTED` | Tested and found invalid |

---

## Static (Project-Level) Fields

| Field | Meaning | Source Schema | Status | Notes |
|---|---|---|---|---|
| `project_code` | Modern PAIMANA project identifier | PAIMANA V2 | PLAUSIBLE | Existence confirmed in brief but not yet extracted |
| `legacy_ocms_code` | Historical OCMS identifier | PAIMANA V2 | PLAUSIBLE | Column present in modern reports; completeness unknown |
| `pmgid` | PMGID identifier | PAIMANA V2 | PLAUSIBLE | Column present in modern reports; completeness unknown |
| `project_name` | Name of the infrastructure project | ALL | PLAUSIBLE | Present in all eras; may have normalisation issues |
| `agency` | Implementing agency | ALL | PLAUSIBLE | May be labeled differently across eras |
| `ministry` | Responsible ministry / department | OCMS+ | UNKNOWN | May appear as metadata or header, not project-row field |
| `sector` | Infrastructure sector | OCMS+ | UNKNOWN | May appear as section header only |
| `state` | State of implementation | ALL | PLAUSIBLE | — |
| `date_of_approval` | Date project was formally approved | ALL | PLAUSIBLE | Format varies; "DOA" in legacy era |
| `start_date` | Project start date | PAIMANA V1+ | UNKNOWN | May not appear in older reports |
| `original_cost` | Original approved cost (₹ crore) | ALL | PLAUSIBLE | "Original Cost" in modern; may be labeled differently in OCMS |
| `original_doc` | Original / target date of completion | ALL | PLAUSIBLE | "DOC" in legacy era |

---

## Dynamic (Monthly Observation) Fields

| Field | Meaning | Source Schema | Status | Notes |
|---|---|---|---|---|
| `revised_cost` | Revised / anticipated cost as of reporting month (₹ crore) | ALL | PLAUSIBLE | "Anticipated Cost" in older reports |
| `cumulative_expenditure` | Cumulative expenditure as of reporting month (₹ crore) | ALL | PLAUSIBLE | — |
| `physical_progress_pct` | Physical completion percentage as of reporting month | PAIMANA V1+ | UNKNOWN | May not appear in legacy/OCMS era |
| `revised_doc` | Revised anticipated date of completion as of reporting month | ALL | PLAUSIBLE | "Anticipated DOC" in older reports |
| `project_status_raw` | Status string as extracted (active / delayed / completed etc.) | LEGACY+ | PLAUSIBLE | Not normalised at extraction; raw string preserved |

---

## Completion Event Fields

| Field | Meaning | Source Schema | Status | Notes |
|---|---|---|---|---|
| `actual_completion_date` | Date project actually completed | PAIMANA V2 | PLAUSIBLE | From Completed Projects table |
| `reported_cumulative_expenditure` | Cumulative expenditure at time of completion reporting (₹ crore) | PAIMANA V2 | PLAUSIBLE | May NOT equal final cost — see official caveat in brief |

---

## Provenance Fields

| Field | Meaning | Status | Notes |
|---|---|---|---|
| `source_file` | PDF filename | REQUIRED | All rows |
| `source_page` | Page number in PDF | REQUIRED | All rows |
| `source_table` | Table label / section in PDF | REQUIRED | All rows |
| `reporting_month` | YYYY-MM format | REQUIRED | All rows in project_month.csv |
| `extraction_flags` | Pipe-delimited anomaly flags | REQUIRED | All rows |

---

## Fields Considered and Rejected

| Field | Reason for Rejection |
|---|---|
| *(none yet)* | — |

---

## Future ML Usage Notes

> These notes are planning markers only. No ML model is being built in Gate 2.
> Do not interpret these as confirmed features.

| Field | Candidate ML Usage | Leakage Risk | Notes |
|---|---|---|---|
| `original_cost` | INPUT FEATURE | LOW | Available at project start |
| `date_of_approval` | INPUT FEATURE | LOW | Available at project start |
| `start_date` | INPUT FEATURE | LOW | — |
| `original_doc` | INPUT FEATURE | LOW | — |
| `revised_cost` | LABEL COMPONENT | HIGH (if future value used) | Past values = features; future = label |
| `revised_doc` | LABEL COMPONENT | HIGH (if future value used) | As above |
| `actual_completion_date` | LABEL ONLY | CRITICAL | Never use as feature |
| `physical_progress_pct` | INPUT FEATURE (past only) | MEDIUM | Historical trend valid; future value = leak |
| `cumulative_expenditure` | INPUT FEATURE (past only) | MEDIUM | As above |
