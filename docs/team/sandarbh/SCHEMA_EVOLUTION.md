# Schema Evolution â€” MoSPI Flash Reports

**Owner:** Sandarbh
**Area:** Data Engineering / Schema Research
**Document Type:** RESEARCH
**Status:** RESEARCH IN PROGRESS
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Data Engineering pipeline, extraction specs
**Canonical:** YES

> Previously: `docs/SCHEMA_EVOLUTION.md`  
> Moved to: `docs/team/sandarbh/SCHEMA_EVOLUTION.md` — 2026-09-01

---

**Document Purpose:** Record observed schema differences across reporting eras.  
**Last Updated:** 2026-09-01 (post-audit â€” based on actual PDF content)  
**Previous status:** All PLAUSIBLE. **Current status:** Partly VERIFIED â€” see table below.

---

## Classification System

| Schema Version | Code | Status | Source Evidence |
|---|---|---|---|
| Early simplified reports | `LEGACY` | **VERIFIED** | FlashReport_2005_06.pdf â€” keywords DOA/DOC on pages 3â€“4 |
| OCMS-era reports | `OCMS` | **VERIFIED** | FlashReport_2015_06, _2020_07, _2023_07, _2024_05(01) â€” OCMS keyword |
| Early PAIMANA with Project Code | `PAIMANA_V1` | **VERIFIED** | FlashReport_2024_06, _07, FlashReport_2025_05, _06 â€” "Project Code" column |
| New web-generated PAIMANA | `PAIMANA_V2_CANDIDATE` | **VERIFIED (structure only)** | FlashReport_2026_05, _06, _07, July 2025 â€” PAIMANA URL, inline Project Code |
| Full PAIMANA with Legacy OCMS + PMGID | `PAIMANA_V2` | **PLAUSIBLE â€” NOT YET OBSERVED** | Not found in any currently held PDF |
| Unclassified | `UNKNOWN` | â€” | â€” |

> [!WARNING]
> The PAIMANA_V2 schema as originally defined in the project brief â€” with explicit "Legacy OCMS Code" and "PMGID" columns â€” has **not been found in any currently held PDF**. All 2026 reports fall into the new PAIMANA_V2_CANDIDATE category.

---

## LEGACY Era (â‰ˆ pre-2010)

**Evidence Source:** June 2005 Flash Report (not yet inspected)  
**Status:** PLAUSIBLE â€” based on project brief description only.

### Observed / Expected Concepts

| Concept | Raw Header (Approximate) | Notes |
|---|---|---|
| Project name | Unknown â€” to be extracted | â€” |
| Date of approval | "DOA" | Abbreviation used |
| Original cost | â€” | â€” |
| Original date of completion | "DOC" | Abbreviation used |
| Anticipated cost | â€” | â€” |
| Anticipated date of completion | "Anticipated DOC" | â€” |
| Cumulative expenditure | â€” | â€” |
| Project status | "Status" | Completion/dropped/frozen |

### Absence Evidence

- **Project Code**: NOT observed in brief description â€” PLAUSIBLE ABSENT
- **Legacy OCMS Code**: NOT observed â€” PLAUSIBLE ABSENT
- **PMGID**: NOT observed â€” PLAUSIBLE ABSENT

---

## OCMS Era (â‰ˆ 2010â€“2023)

**Evidence Sources:** June 2015, July 2020, July 2023 (not yet inspected)  
**Status:** PLAUSIBLE â€” based on project brief description only.

### Observed / Expected Concepts

| Concept | Notes |
|---|---|
| Delayed projects analysis | Report-level aggregate |
| Additionally delayed projects | Report-level aggregate |
| Cost overrun analysis | Report-level aggregate |
| Time overrun analysis | Report-level aggregate |
| Anticipated completion cost | Project-level |
| Original schedule dates | Project-level |
| Latest schedule dates | Project-level |
| Cumulative expenditure | Project-level |
| Completed project lists | Separate section |
| Sector analysis | â€” |
| Month-on-month comparison | Some reports explicitly compare to previous month |

### Absence Evidence

- **PMGID**: PLAUSIBLE ABSENT in this era
- **Legacy OCMS Code** (labelled as such): PLAUSIBLE ABSENT â€” codes may exist but column label may differ

---

## PAIMANA V1 Era (â‰ˆ 2024 transitional)

**Evidence Source:** June 2024 report description in project brief  
**Status:** PLAUSIBLE â€” based on project brief description only.

### Key Addition

- `Project Code` column explicitly present in project-level tables

### Open Question

- Are `Legacy OCMS Code` and `PMGID` absent or merely not mentioned in the brief?
  - This must be verified by inspecting June 2024 PDF content directly.

---

## PAIMANA V2 Era (â‰ˆ 2025â€“2026)

**Evidence Source:** July 2026 report description in project brief  
**Status:** PLAUSIBLE â€” based on project brief description only.

### Key Fields (from brief)

| Field | Column Header | Notes |
|---|---|---|
| Project name | "Project Name" | â€” |
| Agency | "Agency" | â€” |
| Project code | "Project Code" | Modern identifier |
| Legacy code | "Legacy OCMS Code" | Bridge to historical data |
| PMGID | "PMGID" | â€” |
| State | "State" | â€” |
| Date of approval | "Date of Approval" | â€” |
| Start date | "Start Date" | â€” |
| Original/target DOC | "Original/Target Date of Completion" | â€” |
| Revised DOC | "Revised Date of Completion" | â€” |
| Original cost | "Original Cost" | â€” |
| Revised cost | "Revised Cost" | â€” |
| Cumulative expenditure | "Cumulative Expenditure" | â€” |
| Physical progress | "Physical Progress" | â€” |

### Approximate Row Count

- July 2026: ~1,775 ongoing projects (from project brief â€” PLAUSIBLE)

---

## Schema Detection Logic

The `src/extraction/schema_detector.py` module uses keyword matching configured in `config.yaml`.

Detection order:
1. Check for `PAIMANA_V2` keywords â†’ assign if matched
2. Else check for `PAIMANA_V1` keywords â†’ assign if matched
3. Else check for `OCMS` keywords â†’ assign if matched
4. Else check for `LEGACY` keywords â†’ assign if matched
5. Else assign `UNKNOWN`

**This logic must be validated by inspecting at least one report from each assumed era.**

---

## Open Schema Questions

- [ ] What exact column headers appear in the 2005 report?
- [ ] When does `Project Code` first appear? (2024? Earlier?)
- [ ] When does `Legacy OCMS Code` first appear?
- [ ] When does `PMGID` first appear?
- [ ] Are there intermediate schema changes within the OCMS era?
- [ ] Are there reports that mix OCMS and PAIMANA structures?
- [ ] Do Completed Project table schemas differ from Ongoing Project schemas?

---

## Update Instructions

When a new report is inspected and schema is confirmed:

1. Update the classification table at the top with `VERIFIED` status.
2. Record the exact column headers observed in the relevant section.
3. Note any deviations from expected schema.
4. Update `data/metadata/source_manifest.csv` with `schema_version`.
5. Add a note to `docs/shared/DECISION_LOG.md`.


