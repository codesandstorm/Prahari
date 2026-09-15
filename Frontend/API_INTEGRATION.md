# PRAHARI Frontend-Backend API Integration

This document outlines the API contracts and endpoints required by the PRAHARI frontend. The frontend is currently configured to use mock data for these endpoints if `VITE_PRAHARI_API_BASE_URL` is not set.

**Base URL Context:** Read from `VITE_PRAHARI_API_BASE_URL` (e.g. `http://localhost:8000/api/v1`)

## Prepared Integration Points

All API access is routed through `src/services/apiClient.js` which handles base URLs and error formatting.
Domain-specific services are located in `src/services/`.

| Frontend Function | Endpoint Expected | Implementation Service |
| :--- | :--- | :--- |
| **Review Queue paginated list** | `GET /review-queue` | `reviewQueueService.js` |
| **Officer Dashboard summary** | `GET /dashboard/summary` | `dashboardService.js` |
| **Aggregated KPI cards** | `GET /dashboard/kpis` (Mock fallback) | `dashboardService.js` |
| **Early Warning Triage counts**| `GET /dashboard/early-warnings` (Mock fallback) | `dashboardService.js` |
| **Portfolio Analytics charts** | `GET /dashboard/analytics` (Mock fallback)| `dashboardService.js` |
| **Paginated Projects list** | `GET /projects` | `dashboardService.js` |
| **Project Details / Dossier** | `GET /projects/{project_id}` | `projectService.js` |
| **Project History** | `GET /projects/{project_id}/history` | `projectService.js` |
| **Project Machine Prediction** | `GET /projects/{project_id}/prediction`| `projectService.js` |
| **Assistant Query** | `POST /assistant/query` | `assistantService.js` |
| **Available Filters** | `GET /filters` (Mock fallback) | `filterService.js` |
| **Backend Health Check** | `GET /health` | `healthService.js` |

*(Note: Endpoints marked with "Mock fallback" are currently mapped in frontend services using standard data models, but the backend doesn't explicitly expose them yet. The frontend falls back to mock endpoints gracefully until these are implemented or combined).*

## Required API Contracts (Schemas)

The frontend expects JSON responses conforming to the TypeScript/JSDoc types defined in `src/services/types.js`. These are aligned with the Pydantic schemas in `backend/schemas.py`.

### 1. `GET /review-queue`
```json
{
  "items": [
    {
      "canonical_project_id": "CUF-001",
      "canonical_name": "Project Name",
      "sector": "Roads & Highways",
      "agency": "Implementation Agency",
      "state": "State Name",
      "officer_decision": "REVIEW_RECOMMENDED",
      "implementation_watch": "ELEVATED",
      "data_trust": "USABLE",
      "attention_trend": "WORSENING",
      "evidence": "PHYSICAL_PROGRESS_STAGNANT",
      "financial_exposure": "100 Cr"
    }
  ],
  "status": "OK",
  "policy_version": "v1",
  "counts": {
    "REVIEW_RECOMMENDED": 3,
    "DATA_VERIFICATION_REQUIRED": 1
  },
  "page": 1,
  "page_size": 25,
  "total": 50,
  "pages": 2
}
```

### 2. `GET /projects/{id}` (ProjectDetail)
```json
{
  "canonical_project_id": "CUF-001",
  "canonical_name": "Project Name",
  "project_code": "PROJ-123",
  "ministry": "Ministry Name",
  "sector": "Sector Name",
  "state": "State Name",
  "agency": "Agency Name",
  "latest_reporting_month": "2025-02-01",
  "identity_method": "METHOD",
  "identity_status": "CONFIRMED",
  "latest_snapshot": {
    "reporting_month": "2025-02-01",
    "progress_current": 45.2,
    "expenditure_current": 50.1,
    "source": { ... }
  },
  "prediction": null,
  "data_trust": { "status": "USABLE" },
  "model_release": { "release_state": "RELEASED" },
  "prediction_eligibility": { "eligible": true, "reasons": [] },
  "officer_decision": {
      "decision": "REVIEW_RECOMMENDED",
      "implementation_watch": "ELEVATED",
      "attention_trend": "WORSENING",
      "evidence": "SIGNAL"
  }
}
```

### 3. `POST /assistant/query`
**Request:**
```json
{
  "request_id": "req_123",
  "question": "What is the project status?",
  "canonical_project_id": "CUF-001"
}
```
**Response:**
```json
{
  "request_id": "req_123",
  "route": "RAG",
  "answer": {},
  "project_evidence_references": [],
  "document_citations": [],
  "reliability_statement": null,
  "limitations": [],
  "fallback_used": false,
  "fallback_reason": null,
  "model_version": "v1.0",
  "rag_index_version": "v1.0",
  "latency_metadata": { "inference": 0.5 }
}
```

## How to Connect the Real Backend

1. Ensure the Python backend is running locally (e.g., `uvicorn main:app --port 8000`).
2. Copy `Frontend/.env.example` to `Frontend/.env`
3. Set `VITE_PRAHARI_API_BASE_URL=http://localhost:8000/api/v1` (or your appropriate backend prefix).
4. Restart the Vite dev server. The frontend services (`apiClient.js`) will detect the variable and immediately route fetch requests to the real API.
