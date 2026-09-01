# Data Contract

**Owner:** Sandarbh (Data Engineering) + Team review
**Area:** Shared / Data Architecture
**Document Type:** APPROVED
**Status:** ACTIVE — GATE 2 May–June 2026 longitudinal pilot
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Backend, ML, Frontend, Data Engineering
**Canonical:** YES

> Previously: `docs/DATASET_README.md`
> Moved to: `docs/shared/DATA_CONTRACT.md` — 2026-09-01

> [!IMPORTANT]
> The May–June 2026 pilot identity rule is validated only for those two months.
> One observation = one project's reported state at one reporting month.
> Backend must not independently reinterpret raw PDFs.

---

## Conceptual Entities

| Entity | Table | Description |
|---|---|---|
| Project | project_master.csv | A unique infrastructure project. One row per project. |
| ProjectSnapshot | project_month.csv | One project's state at one reporting month. |
| ProjectIdentifier | columns on master | Project Code, Legacy OCMS Code, PMGID |
| CompletionEvent | project_completion_events.csv | Outcome record for a completed project. |
| Source/Provenance | data/metadata/provenance.csv | Row-level traceability to source PDF/page. |

---

**Document Purpose:** Human-readable guide to the dataset structure in `data/`.  
**Status:** DRAFT â€” to be updated as extraction progresses.

---

## Overview

The PRAHARI dataset is a longitudinal, project-month panel dataset reconstructed from official MoSPI monthly Flash Reports.

The fundamental unit of observation is:

```
PROJECT Ã— REPORTING MONTH
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
| `original_cost` | float | Original approved cost (â‚¹ crore). |
| `original_doc` | date | Original / target date of completion. |
| `first_seen_report` | string | Reporting month when project first appeared (YYYY-MM). |
| `source_file` | string | Source PDF filename for initial record. |

> **IMPORTANT:** Fields in `project_master.csv` should be verified as stable across months before being trusted. Some fields may technically appear in month rows first and only be promoted to master after stability is confirmed.

---

### `data/processed/project_month.csv`

Contains **monthly observations** â€” fields that change over time.  
One row per project per reporting month.

| Field | Type | Notes |
|---|---|---|
| `project_id` | string | Foreign key to `project_master`. |
| `reporting_month` | string | YYYY-MM format. |
| `revised_cost` | float | Revised / anticipated cost (â‚¹ crore) as of this month. |
| `cumulative_expenditure` | float | Cumulative expenditure (â‚¹ crore) as of this month. |
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
| `date_of_approval` | date | â€” |
| `start_date` | date | â€” |
| `actual_completion_date` | date | Actual date of completion as reported. |
| `original_doc` | date | Original / target date of completion. |
| `revised_doc` | date | Revised date of completion (last known). |
| `original_cost` | float | â‚¹ crore. |
| `revised_cost` | float | â‚¹ crore. |
| `reported_cumulative_expenditure` | float | â‚¹ crore. See note below. |
| `source_file` | string | Source PDF filename. |
| `source_page` | int | â€” |
| `source_table` | string | â€” |

> **CAVEAT (from official source):** Cumulative expenditure for completed projects may NOT equal final project completion cost. Do not treat `reported_cumulative_expenditure` as the definitive final cost.

---

## Extracted (Intermediate) Tables

`data/extracted/ongoing/<report>.csv` â€” Raw extraction, ongoing table.  
`data/extracted/completed/<report>.csv` â€” Raw extraction, completed table.  
`data/extracted/added/<report>.csv` â€” Raw extraction, newly-added projects table.

These preserve the raw PDF extraction output before normalization.  
**Never overwrite these files.** Normalization creates separate copies.

---

## Provenance Fields

Every observation must ultimately be traceable to its source:

```
project_id + reporting_month
  â†’ source_file (PDF filename)
  â†’ source_page (page number)
  â†’ source_table (table label in PDF)
```

These are recorded in `project_month.csv` and `project_completion_events.csv`.  
The full provenance registry is also in `data/metadata/provenance.csv`.

The provenance CSV contains the authorized validated May and June observations.
Every row must bind `source_id` and `source_sha256` to an eligible entry
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

---

## Gate 2 May–June 2026 Longitudinal Pilot Contract

This section controls only `data/processed/pilot_2026_05_06/`. It does not
authorize historical identity assumptions or replace the provisional target
tables described above.

### Entities and grain

A **Project** represents one canonical real-world infrastructure project. A
**ProjectMonth** represents exactly what one validated source reported about
that project in one reporting month. One Project may therefore have multiple
ProjectMonth observations. Historically reported values are immutable facts of
their reporting month and must never be overwritten by later values.

The pilot uses exact raw government `Project Code` as its sole identity
evidence. It does not use fuzzy names, agency-only or state-only matching,
Legacy OCMS Code as a unique key, or PMGID as a required identifier.

### Canonical identifier

`canonical_project_id = "PRH-" + project_code_raw`.

This is a deterministic internal PRAHARI identifier, not a replacement for or
reinterpretation of the government Project Code. The raw Project Code remains
stored separately. This rule is authorized only for the validated May and June
2026 pilot, where Project Code is complete, unique within each month, and has no
identity conflicts.

### Pilot project master

`project_master.csv` contains one row per Project Code in the union of the two
months. `current_*` means the value in the latest available pilot observation,
not eternal truth. The row retains the selected latest observation and source
provenance. Presence status is observational only: `MAY_ONLY`,
`MAY_AND_JUNE`, or `JUNE_ONLY`.

### Pilot project month

`project_month.csv` has the unique key
`(canonical_project_id, reporting_month)`. Reported identity, date, cost,
expenditure, and progress fields remain raw source strings. Every row retains
its complete source identity, physical and printed page, table, extractor, and
raw-row locator.

The pilot does not infer `COMPLETED`, `NEW`, `CANCELLED`, `DROPPED`, or
`REMOVED`. It creates no completion event, feature, target, label, outcome,
risk value, or ML artifact.

