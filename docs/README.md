# PRAHARI Documentation Index

**Document Type:** INDEX
**Status:** ACTIVE
**Last Updated:** 2026-09-01
**Canonical:** YES

This directory is the **single shared technical knowledge base** for PRAHARI (SIH26103).
All research, decisions, data contracts, handoffs, and implementation notes live here.

---

## Current Project Stage

**Gate 2 — Data Engineering & Longitudinal Dataset Construction**

| Status | Detail |
|---|---|
| June 2026 extraction | VERIFIED — 1,847 rows, manually validated |
| May 2026 extraction | COMPLETE — 1,987 rows |
| July 2026 extraction | BLOCKED — PDF not obtained |
| Multi-month linkage | BLOCKED — awaiting July 2026 |
| Gate 2 completion | PENDING — milestones 7, 10, 11 blocked |

See: [Gate Status](shared/GATE_STATUS.md)

---

## Start Here

### New team member
→ [Project Overview](shared/PROJECT_OVERVIEW.md)  
→ [Current Technical Hypothesis](shared/CURRENT_TECHNICAL_HYPOTHESIS.md)  
→ [Gate Status](shared/GATE_STATUS.md)  
→ [Team Dependencies](shared/TEAM_DEPENDENCIES.md)  
→ Your teammate folder (below)

### Data work / Gate 2
→ [Data Contract](shared/DATA_CONTRACT.md)  
→ [Sandarbh's folder](team/sandarbh/README.md)  
→ [Extraction Specifications](extraction/README.md)  
→ [Temporal Leakage Notes](team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md)

### Prediction / ML design
→ [Pavitra's folder](team/pavitra/README.md)  
→ [Temporal Leakage Notes](team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md)  
→ [Data Contract](shared/DATA_CONTRACT.md)  
→ [Open Questions](shared/OPEN_QUESTIONS.md) — OQ-005, OQ-006

### Backend work
→ [Jashan's folder](team/jashan/README.md)  
→ [API & Data Handoff](shared/API_DATA_HANDOFF.md)  
→ [Data Contract](shared/DATA_CONTRACT.md)  
→ [Team Dependencies](shared/TEAM_DEPENDENCIES.md)

### Frontend / UX work
→ [Sanskaar's folder](team/sanskaar/README.md)  
→ [API & Data Handoff](shared/API_DATA_HANDOFF.md)  
→ Jashan's [API Contracts](team/jashan/API_CONTRACTS.md)

### Domain / product work
→ [Akshita's folder](team/akshita/README.md)  
→ [CUF Research Status](reference/CUF_RESEARCH_STATUS.md)  
→ [Open Questions](shared/OPEN_QUESTIONS.md) — OQ-007, OQ-008, OQ-009

### Codex / Antigravity agent
→ [Project Overview](shared/PROJECT_OVERVIEW.md)  
→ [Current Technical Hypothesis](shared/CURRENT_TECHNICAL_HYPOTHESIS.md)  
→ [Data Contract](shared/DATA_CONTRACT.md)  
→ [Gate Status](shared/GATE_STATUS.md)  
→ [Open Questions](shared/OPEN_QUESTIONS.md) — do NOT answer these without evidence  
→ [Research Evidence Guidelines](reference/RESEARCH_EVIDENCE_GUIDELINES.md)  
→ [Review Workflow](shared/REVIEW_WORKFLOW.md)

---

## Team Documentation

### Sandarbh — Data Engineering & ML Integration

| Document | Status |
|---|---|
| [README](team/sandarbh/README.md) | Role, blockers, active task |
| [Data Engineering Status](team/sandarbh/DATA_ENGINEERING_STATUS.md) | ACTIVE |
| [Schema Evolution](team/sandarbh/SCHEMA_EVOLUTION.md) | RESEARCH IN PROGRESS |
| [Project Identity Analysis](team/sandarbh/PROJECT_IDENTITY_ANALYSIS.md) | RESEARCH IN PROGRESS |
| [Temporal Leakage Notes](team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md) | APPROVED WITH LIMITATIONS |
| [Data Dictionary Notes](team/sandarbh/DATA_DICTIONARY_NOTES.md) | RESEARCH IN PROGRESS |
| [ML Integration Notes](team/sandarbh/ML_INTEGRATION_NOTES.md) | NOT STARTED |

### Pavitra — Prediction Research & Independent Audit

| Document | Status |
|---|---|
| [README](team/pavitra/README.md) | Role, blockers, reading list |
| [Prediction Formulation](team/pavitra/PREDICTION_FORMULATION.md) | NOT STARTED |
| [Target and Label Research](team/pavitra/TARGET_AND_LABEL_RESEARCH.md) | NOT STARTED |
| [Baseline Model Research](team/pavitra/BASELINE_MODEL_RESEARCH.md) | NOT STARTED |
| [Dataset Independent Audit](team/pavitra/DATASET_INDEPENDENT_AUDIT.md) | NOT STARTED |

### Akshita — Domain Research & Product

| Document | Status |
|---|---|
| [README](team/akshita/README.md) | Role, blockers |
| [Domain Research](team/akshita/DOMAIN_RESEARCH.md) | RESEARCH IN PROGRESS |
| [PAIMANA Gap Analysis](team/akshita/PAIMANA_GAP_ANALYSIS.md) | RESEARCH IN PROGRESS |
| [Existing Solutions Review](team/akshita/EXISTING_SOLUTIONS_REVIEW.md) | RESEARCH IN PROGRESS |
| [Product Differentiation](team/akshita/PRODUCT_DIFFERENTIATION.md) | NOT STARTED |

### Jashan — Backend Architecture & Database

| Document | Status |
|---|---|
| [README](team/jashan/README.md) | Role, blockers, prereqs |
| [Backend Architecture](team/jashan/BACKEND_ARCHITECTURE.md) | NOT STARTED |
| [API Contracts](team/jashan/API_CONTRACTS.md) | NOT STARTED |
| [Database Design](team/jashan/DATABASE_DESIGN.md) | NOT STARTED |
| [Backend Implementation Status](team/jashan/BACKEND_IMPLEMENTATION_STATUS.md) | NOT STARTED |

### Sanskaar — UX / Frontend & Dashboard

| Document | Status |
|---|---|
| [README](team/sanskaar/README.md) | Role, blockers |
| [UX Research](team/sanskaar/UX_RESEARCH.md) | RESEARCH IN PROGRESS |
| [Dashboard Information Architecture](team/sanskaar/DASHBOARD_INFORMATION_ARCHITECTURE.md) | NOT STARTED |
| [User Flows](team/sanskaar/USER_FLOWS.md) | NOT STARTED |
| [Frontend Contract Requirements](team/sanskaar/FRONTEND_CONTRACT_REQUIREMENTS.md) | NOT STARTED |

---

## Shared Canonical Documents

> These are the single source of truth for team-wide decisions.
> Research files in `team/` inform these. Never create competing versions.

| Document | Description | Status |
|---|---|---|
| [Project Overview](shared/PROJECT_OVERVIEW.md) | PRAHARI system concepts, why each decision was made | APPROVED |
| [Current Technical Hypothesis](shared/CURRENT_TECHNICAL_HYPOTHESIS.md) | Architecture layers and evidence requirements | APPROVED |
| [Data Contract](shared/DATA_CONTRACT.md) | Canonical data model — project_master, project_month, completion_events | PROVISIONAL |
| [API & Data Handoff](shared/API_DATA_HANDOFF.md) | Cross-team handoff contracts (data, backend, ML, frontend) | PROVISIONAL |
| [Team Dependencies](shared/TEAM_DEPENDENCIES.md) | Who depends on whom for what | ACTIVE |
| [Decision Log](shared/DECISION_LOG.md) | All significant technical decisions (append-only) | ACTIVE |
| [Open Questions](shared/OPEN_QUESTIONS.md) | Unresolved technical questions with owners | ACTIVE |
| [Gate Status](shared/GATE_STATUS.md) | Gate dashboard and milestone tracker | ACTIVE |
| [Review Workflow](shared/REVIEW_WORKFLOW.md) | Research → decision → implementation process | APPROVED |
| [Terminology & Conventions](shared/TERMINOLOGY_AND_CONVENTIONS.md) | Shared terminology, evidence labels, naming | APPROVED |

---

## Extraction Specifications

| Document | Source | Status |
|---|---|---|
| [PAIMANA V2 — June 2026](extraction/PAIMANA_V2_EXTRACTION_SPEC.md) | SRC-2026-06 | APPROVED |
| [PAIMANA V2 — May 2026](extraction/PAIMANA_V2_MAY_2026_EXTRACTION_SPEC.md) | SRC-2026-05 | APPROVED |
| [May vs June Schema Comparison](extraction/MAY_2026_SCHEMA_COMPARISON.md) | — | APPROVED |

---

## Reference Documents

| Document | Description | Status |
|---|---|---|
| [CUF Research Status](reference/CUF_RESEARCH_STATUS.md) | CUF field inventory and gap research | NOT STARTED |
| [Official Source Notes](reference/OFFICIAL_SOURCE_NOTES.md) | Official government documentation | NOT STARTED |
| [Data Source Register](reference/DATA_SOURCE_REGISTER.md) | All data sources used or considered | ACTIVE |
| [Research Evidence Guidelines](reference/RESEARCH_EVIDENCE_GUIDELINES.md) | VERIFIED/PLAUSIBLE/UNKNOWN/REJECTED rules | APPROVED |

---

## Audits

| Audit | Scope | Status |
|---|---|---|
| [Audit Index](audits/INDEX.md) | All audits, completed and pending | ACTIVE |
| Source integrity audit | SHA-256 of 13 PDFs | COMPLETE |
| June 2026 manual validation | 30-row sample | COMPLETE |

---

## Templates

| Template | Use For |
|---|---|
| [Team Research](templates/TEAM_RESEARCH_TEMPLATE.md) | New research documents in `team/` |
| [Technical Decision](templates/TECHNICAL_DECISION_TEMPLATE.md) | Design decisions and DECISION_LOG entries |
| [Audit](templates/AUDIT_TEMPLATE.md) | Formal audit reports |
| [Handoff](templates/HANDOFF_TEMPLATE.md) | Cross-team data/API handoffs |
| [Extraction Review](templates/EXTRACTION_REVIEW_TEMPLATE.md) | Extraction specification + audit |

---

## Rules for Adding or Updating Documentation

1. **Adding research:** Write under `docs/team/<your_name>/`
2. **Conclusion accepted:** Summarise/migrate into `docs/shared/`
3. **Decision changes:** Mark old material SUPERSEDED — add DECISION_LOG entry
4. **Architecture changes:** Update DECISION_LOG + notify team
5. **Data contract changes:** Notify Backend + ML + Frontend owners
6. **API contract changes:** Notify Frontend (Sanskaar)
7. **Prediction contract changes:** Notify Backend + Frontend

All empirical claims must carry: **VERIFIED | PLAUSIBLE | UNKNOWN | REJECTED**

See: [Research Evidence Guidelines](reference/RESEARCH_EVIDENCE_GUIDELINES.md)  
See: [Review Workflow](shared/REVIEW_WORKFLOW.md)
