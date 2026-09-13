# PRAHARI Project Intelligence API Contract

**Owner:** PRAHARI Backend
**Status:** APPROVED
**Last Updated:** 2026-09-13

Endpoints:

- `GET /api/v1/projects/{project_id}/intelligence` — real historical intelligence;
- `GET /api/v1/projects/{project_id}/benchmark` — embedded real peer benchmark;
- `GET /api/v1/sandbox/projects` — paginated synthetic catalog with optional Watch filter;
- `GET /api/v1/sandbox/projects/{project_id}/intelligence` — synthetic intelligence.
- `GET /api/v1/dashboard/intelligence-summary?mode=...` — explicit-mode portfolio summary.

Real routes return `mode=REAL_HISTORICAL` and `data_origin=HISTORICAL_FLASH_REPORT`. Sandbox routes return `mode=SYNTHETIC_SANDBOX` and `data_origin=SYNTHETIC_CUF_PROTOTYPE`. There is no implicit mode switch.

The backend returns presentation-ready quartile bands, percentiles, group labels, reason codes, Watch state, decision state, actions, evidence, null prediction fields, and limitations. Frontends must not recompute these governed values. Review-queue entries include the intelligence endpoint and permitted prioritization bases; no queue sorting depends on a withheld probability.

Example payloads are under `outputs/product_intelligence_v1/`.
