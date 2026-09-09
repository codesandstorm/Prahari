# PRAHARI Backend Final Architecture

**Owner:** PRAHARI Team
**Area:** Backend
**Document Type:** CANONICAL
**Status:** APPROVED PROTOTYPE
**Last Updated:** 2026-09-09
**Canonical:** YES

## Audit finding

At base commit `c3ed339`, no backend implementation existed. The Jashan documents were placeholders marked `NOT STARTED`. Integration V1 therefore introduces one modular backend under `backend/`; it does not create a competing implementation.

## Architecture

FastAPI owns HTTP validation and evidence construction. SQLAlchemy repositories read PostgreSQL (SQLite is a bounded development/test fallback). Alembic owns schema evolution. The canonical loader reads source-backed `project_month.csv`, never engineered `project_month_ml_ready.csv`. A `PredictionProvider` boundary prevents any model family from becoming permanent application logic. `AssistantAdapter` constructs trusted evidence from database records and calls `UnifiedPrahariAssistant.answer(...)`; the LLM never predicts or writes records.

Current status, future risk, reliability, data quality, review priority, prediction, alert, model contributors, and LLM explanation remain separate concepts. The design is a modular monolith, without queues, microservices, or cloud dependencies.
