# Jashan — Backend Architecture & Database Design

**Role:** Backend Lead — FastAPI + PostgreSQL + Data Serving
**Area:** Backend API, database design, data ingestion from canonical datasets
**Last Updated:** 2026-09-01

---

## Current Responsibility

- Design backend architecture (FastAPI + PostgreSQL)
- Define database schema for ingesting canonical PRAHARI datasets
- Design API contract for frontend consumption
- Design prediction artifact storage schema (post-Gate 5)
- Ensure provenance is preserved during database ingestion

---

## Owned Documents

| Document | Status |
|---|---|
| [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md) | NOT STARTED — awaiting Gate 2 data schema |
| [API_CONTRACTS.md](API_CONTRACTS.md) | NOT STARTED |
| [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | NOT STARTED |
| [BACKEND_IMPLEMENTATION_STATUS.md](BACKEND_IMPLEMENTATION_STATUS.md) | NOT STARTED |

---

## Inputs Required

| From | What | Status |
|---|---|---|
| Sandarbh | project_master, project_month, completion_events schemas | NOT YET FINAL |
| Sandarbh | Data dictionary | DRAFT available |
| Sanskaar | Frontend API contract requirements | NOT STARTED |

---

## Outputs Provided

| To | What | Status |
|---|---|---|
| Sanskaar | Stable API endpoint specifications | NOT STARTED |
| ML team | Prediction artifact storage interface (future) | FUTURE |

---

## Current Blockers

- Data schema from Gate 2 not yet finalized — cannot design database schema.
- Frontend requirements from Sanskaar not yet specified.

---

## Key Rules

- Backend does not re-extract from raw PDFs — ingests canonical CSVs only.
- Provenance fields (source_file, source_page, source_table) must be preserved in all DB tables.
- Backend does not define prediction mathematics — stores and serves ML outputs only.
- Implementation begins after Gate 2 data schema is finalized.

---

## Reading List

- [`../../shared/DATA_CONTRACT.md`](../../shared/DATA_CONTRACT.md) — data model to implement
- [`../../shared/API_DATA_HANDOFF.md`](../../shared/API_DATA_HANDOFF.md) — handoff contracts
- [`../../shared/TEAM_DEPENDENCIES.md`](../../shared/TEAM_DEPENDENCIES.md) — dependency chain
- [`../sandarbh/DATA_DICTIONARY_NOTES.md`](../sandarbh/DATA_DICTIONARY_NOTES.md) — field definitions
