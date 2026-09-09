# PRAHARI Database Schema V1

**Owner:** PRAHARI Team
**Area:** Backend
**Document Type:** CANONICAL
**Status:** APPROVED PROTOTYPE
**Last Updated:** 2026-09-09
**Canonical:** YES

`projects` stores canonical identity. `source_reports` stores the full month calendar and its `PROJECT_LEVEL`, `AGGREGATE_ONLY`, or `MISSING_SOURCE` coverage. `project_snapshots` stores observed rows only and is unique by canonical project plus reporting month. `predictions` is versioned by anchor, target, horizon, model, features and target contract. `prediction_contributors` stores non-causal model evidence. `alerts` is a distinct policy record. `ingestion_runs` records immutable dataset fingerprints and outcomes.

Foreign keys protect identity and provenance. Database checks enforce coverage values, probability range, and null probability/risk for abstention. Indexes cover project-month history, current prediction lookup, contributors and alerts. Historical snapshots are never overwritten with a fabricated calendar row.
