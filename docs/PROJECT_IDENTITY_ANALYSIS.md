# Project Identity Analysis

**Document Purpose:** Track the investigation of project identity across reporting eras.  
**Status:** NOT STARTED — all claims below are research questions, not findings.

---

## Why Identity Matters

To build a longitudinal dataset, the same physical infrastructure project must be
linked across multiple monthly reports over potentially two decades.

Without reliable identity linkage, "tracking" a project over time is impossible and
any longitudinal analysis is invalid.

---

## Known Identifiers (Modern Reports)

| Identifier | Column Name (PAIMANA V2) | Coverage | Stability | Status |
|---|---|---|---|---|
| Project Code | `Project Code` | UNKNOWN | UNKNOWN | Not yet verified |
| Legacy OCMS Code | `Legacy OCMS Code` | UNKNOWN | UNKNOWN | Not yet verified |
| PMGID | `PMGID` | UNKNOWN | UNKNOWN | Not yet verified |
| Project Name | `Project Name` | High (present in all eras) | Uncertain | Not yet verified |

---

## Research Questions to Investigate

Each question below must be answered through evidence, not assumption.

### Q1: Is Project Code stable month-to-month?

- Approach: Extract July 2026, June 2026, May 2026. Compare Project Code distributions.
- Expected: Most codes stable. Exceptions to be flagged.
- Status: NOT STARTED

### Q2: Is Project Code stable year-to-year?

- Approach: Compare July 2026 codes against July 2025 codes.
- Expected: Stable, but assumption only.
- Status: NOT STARTED

### Q3: When does Project Code first appear?

- Approach: Inspect 2023, 2024 reports. Identify first report with `Project Code` column.
- Status: NOT STARTED

### Q4: How often is Legacy OCMS Code populated (non-null)?

- Approach: Extract July 2026 `Legacy OCMS Code` column. Count non-null values.
- Status: NOT STARTED

### Q5: How often is PMGID populated (non-null)?

- Approach: As above for PMGID.
- Status: NOT STARTED

### Q6: Can old OCMS records be linked to PAIMANA records?

- Approach: After answering Q4/Q5, attempt matching OCMS-era project names to
  modern records using Legacy OCMS Code where populated.
- Constraint: Do NOT perform uncontrolled fuzzy name matching automatically.
  Any name-based matching must be supervised and audited.
- Status: NOT STARTED

### Q7: Do projects disappear and later reappear?

- Approach: Identify projects present in month T but absent in month T+1, then
  present again in month T+2. Count and investigate reasons.
- Status: NOT STARTED

### Q8: Do project names change for the same Project Code?

- Approach: Group by Project Code across months; check name consistency.
- Status: NOT STARTED

### Q9: Are Project Codes ever reused for different projects?

- Approach: Check for Project Codes where project name or agency changes dramatically.
- Status: NOT STARTED

### Q10: Are duplicate Project Codes present within a single report?

- Approach: Check for duplicate `project_code` values in extracted CSVs.
- Status: NOT STARTED

---

## Identity Resolution Rules (Draft)

> These rules will be finalised after Q1–Q10 are answered.

**Rule 1 — Preferred identity:** Use `Project Code` as primary identifier in PAIMANA V2 era.

**Rule 2 — Cross-era bridge:** Use `Legacy OCMS Code` (where populated) to link PAIMANA records
to OCMS-era records.

**Rule 3 — Unresolvable records:** If identity cannot be established with confidence,
mark the project as `identity_status = UNRESOLVED`. Do NOT silently merge or infer.

**Rule 4 — No uncontrolled fuzzy matching:** Name-based fuzzy matching must only be used
as a research tool to surface candidates, never as automatic record linkage.

---

## Outputs to be Created

- `data/validation/identity_audit.csv` — Per-project identity resolution status
- Updated `project_master.csv` with `identity_confidence` column

---

## Known Risks

- Project names in older reports may include typos, abbreviations, or language changes.
- The same project may be listed under different agencies if agency changes.
- Completed projects may reappear in the completed-projects table of a future report.
- Projects may be merged, split, or administratively cancelled and re-initiated.
