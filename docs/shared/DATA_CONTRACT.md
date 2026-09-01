# Dataset README

**Document Purpose:** Human-readable guide to the dataset structure in `data/`.  
**Status:** DRAFT — to be updated as extraction progresses.

---

## Overview

The PRAHARI dataset is a longitudinal, project-month panel dataset reconstructed from official MoSPI monthly Flash Reports.

The fundamental unit of observation is:

```
PROJECT × REPORTING MONTH
```

This means each row records the **state of a single project as reported in a single monthly report**.

---

## Final Target Tables

### `data/processed/project_master.csv`

Contains **stable or mostly-stable** project-level attributes.  
One row per unique project.

| Field | Type | Notes |
|---|---|---|
| `project_id` | string | Canonical identifier in PRAHARI. Maps to `Project Code` in modern reports. |
| `legacy_ocms_code` | string | Legacy OCMS identifier. Populated only where available. |
| `pmgid` | string | PMGID field. Populated only where available. |
| `project_name` | string | As reported in source. Normalised (whitespace stripped). |
| `agency` | string | Implementing agency. |
| `ministry` | string | Responsible ministry / department. May not appear in all eras. |
| `sector` | string | Infrastructure sector. |
| `state` | string | State of implementation. |
| `date_of_approval` | date | Date project was approved. |
| `start_date` | date | Project start date. |
| `original_cost` | float | Original approved cost (₹ crore). |
| `original_doc` | date | Original / target date of completion. |
| `first_seen_report` | string | Reporting month when project first appeared (YYYY-MM). |
| `source_file` | string | Source PDF filename for initial record. |

> **IMPORTANT:** Fields in `project_master.csv` should be verified as stable across months before being trusted. Some fields may technically appear in month rows first and only be promoted to master after stability is confirmed.

---

### `data/processed/project_month.csv`

Contains **monthly observations** — fields that change over time.  
One row per project per reporting month.

| Field | Type | Notes |
|---|---|---|
| `project_id` | string | Foreign key to `project_master`. |
| `reporting_month` | string | YYYY-MM format. |
| `revised_cost` | float | Revised / anticipated cost (₹ crore) as of this month. |
| `cumulative_expenditure` | float | Cumulative expenditure (₹ crore) as of this month. |
| `physical_progress_pct` | float | Physical progress (%). |
| `revised_doc` | date | Revised / anticipated date of completion as of this month. |
| `project_status_raw` | string | Status string as-extracted from source. |
| `source_file` | string | Source PDF filename. |
| `source_page` | int | Page number in source PDF. |
| `source_table` | string | Table label in source PDF. |
| `extraction_flags` | string | Pipe-separated list of anomaly flags raised. |

---

### `data/processed/project_completion_events.csv`

Contains **completed-project outcome records**.  
One row per project completion record as reported.

| Field | Type | Notes |
|---|---|---|
| `project_id` | string | Foreign key to `project_master` (where linkable). |
| `project_name_raw` | string | Name as extracted. |
| `agency` | string | Agency as extracted. |
| `state` | string | State as extracted. |
| `date_of_approval` | date | — |
| `start_date` | date | — |
| `actual_completion_date` | date | Actual date of completion as reported. |
| `original_doc` | date | Original / target date of completion. |
| `revised_doc` | date | Revised date of completion (last known). |
| `original_cost` | float | ₹ crore. |
| `revised_cost` | float | ₹ crore. |
| `reported_cumulative_expenditure` | float | ₹ crore. See note below. |
| `source_file` | string | Source PDF filename. |
| `source_page` | int | — |
| `source_table` | string | — |

> **CAVEAT (from official source):** Cumulative expenditure for completed projects may NOT equal final project completion cost. Do not treat `reported_cumulative_expenditure` as the definitive final cost.

---

## Extracted (Intermediate) Tables

`data/extracted/ongoing/<report>.csv` — Raw extraction, ongoing table.  
`data/extracted/completed/<report>.csv` — Raw extraction, completed table.  
`data/extracted/added/<report>.csv` — Raw extraction, newly-added projects table.

These preserve the raw PDF extraction output before normalization.  
**Never overwrite these files.** Normalization creates separate copies.

---

## Provenance Fields

Every observation must ultimately be traceable to its source:

```
project_id + reporting_month
  → source_file (PDF filename)
  → source_page (page number)
  → source_table (table label in PDF)
```

These are recorded in `project_month.csv` and `project_completion_events.csv`.  
The full provenance registry is also in `data/metadata/provenance.csv`.

The provenance CSV remains header-only until real observations are extracted.
Every future row must bind `source_id` and `source_sha256` to an eligible entry
in `source_manifest.csv`. `pdf_page_index` is the one-based physical PDF page;
`printed_page_number` is the label printed by the report and may be blank or
different. Required audit fields also include the source table, extraction
method, extractor version, and a stable raw-row locator.

---

## Known Limitations (to be updated with evidence)

- [ ] Completeness of `legacy_ocms_code` linkage: UNKNOWN
- [ ] Completeness of `pmgid` linkage: UNKNOWN
- [ ] Whether `project_id` is stable across all months: UNKNOWN
- [ ] Whether name changes occur for the same project: UNKNOWN
- [ ] Whether project codes are ever reused: UNKNOWN
- [ ] Whether cumulative expenditure ever non-monotonically decreases: UNKNOWN
