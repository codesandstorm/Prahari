# API & Data Handoff Contract

**Owner:** Sandarbh (Data) + Jashan (Backend) + Sanskaar (Frontend)
**Area:** Shared / Integration
**Document Type:** PROPOSAL
**Status:** PROVISIONAL — Gate 2 not complete; schemas not final
**Last Updated:** 2026-09-01
**Depends On:** DATA_CONTRACT.md, TEAM_DEPENDENCIES.md
**Used By:** Backend, Frontend, ML
**Canonical:** YES

> [!WARNING]
> This document describes INTENDED handoffs, not completed ones.
> All schemas are provisional. No implementation should begin until Gate 2 datasets
> are validated and DATA_CONTRACT.md is finalized.

---

## Data Engineering → Backend

### Canonical Datasets (Gate 2 output)

| Dataset | Path | Description | Status |
|---|---|---|---|
| `project_master.csv` | `data/processed/` | One row per unique project | NOT FINAL |
| `project_month.csv` | `data/processed/` | One row per project per reporting month | NOT FINAL |
| `project_completion_events.csv` | `data/processed/` | Completed project outcome records | NOT FINAL |
| `data_dictionary.csv` | `data/metadata/` | Field definitions | DRAFT |
| `source_manifest.csv` | `data/metadata/` | Source file registry | ACTIVE |
| `provenance.csv` | `data/metadata/` | Row-level source traceability | ACTIVE |

### Handoff Rules

- Backend ingests canonical CSVs into PostgreSQL — does not re-extract from PDFs.
- Every backend row retains `source_file`, `source_page`, `source_table` from the CSV.
- Provenance is never discarded during ingestion.
- Data dictionary defines all field types and allowed values.

---

## Backend → Frontend

### API Shape (Provisional)

Frontend queries backend API only — not raw CSVs.

Provisional API surface (to be designed by Jashan, consumed by Sanskaar):

```
GET /api/projects                     — project list with filters
GET /api/projects/{project_id}        — project master + latest snapshot
GET /api/projects/{project_id}/history — monthly time series
GET /api/portfolio                    — portfolio-level aggregates
GET /api/projects/{project_id}/provenance — source traceability
```

Response format: JSON.  
All monetary values in ₹ crore.  
All dates in ISO 8601 format.

### Frontend Contract Requirements

See [`../team/sanskaar/FRONTEND_CONTRACT_REQUIREMENTS.md`](../team/sanskaar/FRONTEND_CONTRACT_REQUIREMENTS.md)
for Sanskaar's frontend requirements.

See [`../team/jashan/API_CONTRACTS.md`](../team/jashan/API_CONTRACTS.md)
for Jashan's API contract specifications.

---

## ML → Backend (Future — Gate 5+)

Prediction artifacts to be persisted by ML team, ingested by backend:

```
predictions.csv / predictions table:
  project_id
  prediction_date
  horizon_months
  risk_score           (calibrated probability)
  confidence_lower
  confidence_upper
  model_version
  dataset_version
  feature_version

explanation_tokens.csv:
  project_id
  prediction_date
  feature_name
  shap_value
```

> [!CAUTION]
> ML → Backend handoff must not happen before Gate 5 is complete.
> Prediction artifacts produced before Gate 5 are experimental and must NOT be
> exposed to the frontend as authoritative risk scores.

---

## Versioning Policy

Every handoff artifact must carry version metadata:

| Field | Format | Example |
|---|---|---|
| Dataset version | `YYYY-MM-vN` | `2026-06-v1` |
| Model version | `gate5-vN` | `gate5-v1` |
| Feature version | `fvN` | `fv1` |
| Extraction version | pipeline version from config | `1.0.0` |

---

## Known Limitations (2026-09-01)

- Project identity continuity across months not yet validated — project_id not final.
- July 2026 PDF not obtained — 3-month linkage incomplete.
- Backend schema not yet designed — API shapes are provisional.
- Prediction contract is future — no ML has been implemented.
