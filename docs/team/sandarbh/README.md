# Sandarbh — Data Engineering & ML Integration

**Role:** Data Engineering Lead + Technical Integration Owner
**Area:** Data Engineering, ML Architecture, System Integration
**Last Updated:** 2026-09-01

---

## Current Responsibility

- Source PDF audit and SHA-256 integrity verification
- Schema detection and classification across report eras
- Extraction pipeline implementation (pdfplumber-based)
- Row parsing, provenance binding, missing-value handling
- Multi-month project identity research and linkage
- Data dictionary maintenance
- Cross-team technical integration (data → backend → ML → frontend)
- Leakage-safe data model design for future ML

---

## Owned Documents

| Document | Status |
|---|---|
| [SCHEMA_EVOLUTION.md](SCHEMA_EVOLUTION.md) | RESEARCH IN PROGRESS |
| [PROJECT_IDENTITY_ANALYSIS.md](PROJECT_IDENTITY_ANALYSIS.md) | RESEARCH IN PROGRESS |
| [TEMPORAL_LEAKAGE_NOTES.md](TEMPORAL_LEAKAGE_NOTES.md) | APPROVED WITH LIMITATIONS |
| [DATA_DICTIONARY_NOTES.md](DATA_DICTIONARY_NOTES.md) | RESEARCH IN PROGRESS |
| [DATA_ENGINEERING_STATUS.md](DATA_ENGINEERING_STATUS.md) | ACTIVE |
| [ML_INTEGRATION_NOTES.md](ML_INTEGRATION_NOTES.md) | NOT STARTED |

Also owns: `docs/extraction/`, `docs/shared/DATA_CONTRACT.md`, `docs/shared/GATE_STATUS.md`

Notebook instructions (in `notebooks/`):
- [01_schema_exploration_INSTRUCTIONS.md](../../../notebooks/01_schema_exploration_INSTRUCTIONS.md)
- [02_extraction_validation_INSTRUCTIONS.md](../../../notebooks/02_extraction_validation_INSTRUCTIONS.md)
- [03_identity_analysis_INSTRUCTIONS.md](../../../notebooks/03_identity_analysis_INSTRUCTIONS.md)

---

## Inputs Required

| From | What | Status |
|---|---|---|
| Pavitra | Target horizon decision | OPEN — Gate 3 |
| Akshita | Domain validation of project categories | RESEARCH IN PROGRESS |
| Jashan | Feedback on data dictionary field usability | PENDING |
| MoSPI/PAIMANA | July 2026 PDF | BLOCKED |
| MoSPI/PAIMANA | CUF documentation | NOT OBTAINED |

---

## Outputs Provided to Team

| To | What | Status |
|---|---|---|
| Jashan | project_master, project_month, completion_events, data dictionary | NOT YET FINAL |
| Pavitra | Leakage risk catalogue, data model schema | DRAFT available |
| All | Gate status updates | ONGOING |

---

## Current Blockers

1. **July 2026 PDF not obtained** — blocks milestones 7, 10, 11 in Gate 2.
2. **Identity continuity not yet validated** — project_month schema not final.

---

## Current Active Task (2026-09-01)

Gate 2: May 2026 extraction complete. June 2026 extraction validated.
Next: Obtain July 2026 PDF. Begin 3-month identity linkage.

