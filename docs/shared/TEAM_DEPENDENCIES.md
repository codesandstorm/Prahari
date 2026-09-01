# PRAHARI Team Dependencies

**Owner:** Sandarbh (technical integration owner)
**Area:** Shared / Dependencies
**Document Type:** REFERENCE
**Status:** ACTIVE — updated as handoffs are confirmed
**Last Updated:** 2026-09-01
**Depends On:** DATA_CONTRACT.md, GATE_STATUS.md
**Used By:** Entire team
**Canonical:** YES

> [!IMPORTANT]
> CURRENT dependencies are what exists now.
> FUTURE dependencies are what will be needed after gates complete.
> Do not implement FUTURE handoffs before the prerequisite gate is done.

---

## Sandarbh → Jashan (FUTURE — after Gate 2)

Data Engineering provides:

| Artifact | Format | Status |
|---|---|---|
| `project_master.csv` | CSV with field definitions | NOT YET FINAL |
| `project_month.csv` | CSV with field definitions | NOT YET FINAL |
| `project_completion_events.csv` | CSV with field definitions | NOT YET FINAL |
| `data/metadata/data_dictionary.csv` | CSV | DRAFT |
| `data/metadata/provenance.csv` | CSV | ACTIVE |
| `data/metadata/source_manifest.csv` | CSV | ACTIVE |

Backend must not independently reinterpret raw PDFs.  
Backend must not reconstruct database relationships from raw source files.

---

## Sandarbh + Pavitra (ONGOING — joint responsibility)

Joint research ownership:

| Topic | Status |
|---|---|
| Target/outcome definition | RESEARCH IN PROGRESS (Gate 3) |
| Leakage rules | DOCUMENTED — enforcement at Gate 3 |
| Feature availability audit | NOT STARTED (Gate 4) |
| Temporal split strategy | DOCUMENTED — implementation at Gate 3 |
| Outcome construction methodology | NOT STARTED (Gate 3) |

See [`../team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md`](../team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md)
and [`../team/pavitra/TARGET_AND_LABEL_RESEARCH.md`](../team/pavitra/TARGET_AND_LABEL_RESEARCH.md).

---

## Jashan → Sanskaar (FUTURE — after Gate 2 + backend implementation)

Backend provides stable API endpoints:

| Endpoint Category | Description | Status |
|---|---|---|
| Project API | Project master data | NOT IMPLEMENTED |
| History API | Monthly observations | NOT IMPLEMENTED |
| Portfolio API | Aggregate/portfolio views | NOT IMPLEMENTED |
| Provenance API | Source traceability | NOT IMPLEMENTED |

Frontend must not reconstruct database relationships itself.  
Frontend must not interpret raw CSV files directly.

---

## ML → Backend (FUTURE — after Gate 5)

ML team will provide:

| Artifact | Description | Status |
|---|---|---|
| Persisted predictions | Per-project risk scores | NOT STARTED |
| Model version metadata | Version, training date, dataset version | NOT STARTED |
| Feature version | Which features were used | NOT STARTED |
| Calibration metadata | Reliability evidence | NOT STARTED |
| SHAP explanations | Per-project feature attribution | NOT STARTED |

Backend provides storage and API access only.  
Backend does not define prediction mathematics.

---

## Akshita → Entire Team (ONGOING)

Domain research provides:

| Output | Consumer | Status |
|---|---|---|
| PAIMANA gap analysis | All — validates what data is missing | RESEARCH IN PROGRESS |
| Existing solutions review | All — defines what PRAHARI must exceed | RESEARCH IN PROGRESS |
| Product differentiation | Frontend, presentation | NOT STARTED |
| Operational context | ML (what predictions mean in practice) | RESEARCH IN PROGRESS |
| Domain validation of predictions | ML evaluation | FUTURE |

---

## Sanskaar → Jashan (FUTURE — pre-backend implementation)

Frontend provides:

| Output | Description | Status |
|---|---|---|
| Frontend contract requirements | What API shapes are needed | NOT STARTED |
| Officer workflow specification | What officers do with predictions | NOT STARTED |
| Dashboard information architecture | What views are required | NOT STARTED |

---

## Currently Active Handoffs (September 2026)

| From | To | What | Status |
|---|---|---|---|
| Sandarbh | Pavitra | Leakage risk catalogue | AVAILABLE (`TEMPORAL_LEAKAGE_NOTES.md`) |
| Sandarbh | Pavitra | Data model schema | DRAFT (`DATA_CONTRACT.md`) |
| Sandarbh | Jashan | Data dictionary | DRAFT (`DATA_DICTIONARY_NOTES.md`) |
| Akshita | All | Domain context | RESEARCH IN PROGRESS |
| Pavitra | Sandarbh | Target horizon research | NOT STARTED |
