# PRAHARI API Contract V1

**Owner:** PRAHARI Team
**Area:** Backend
**Document Type:** CANONICAL
**Status:** APPROVED PROTOTYPE
**Last Updated:** 2026-09-09
**Canonical:** YES

All business routes use `/api/v1`.

- `GET /health`: bounded application, database, and assistant availability.
- `GET /projects`: server pagination (`page`, `page_size`), safe search/filter/sort.
- `GET /projects/{canonical_project_id}`: identity, latest observed snapshot, optional stored prediction.
- `GET /projects/{canonical_project_id}/history`: genuine observations plus separately listed unavailable months; never interpolated.
- `GET /projects/{canonical_project_id}/prediction`: latest auditable prediction or JSON `null`.
- `GET /dashboard/summary`: independent counts for projects, observations, predictions, and alerts.
- `GET /review-queue`: deterministic Officer Decision V1 results. Current live results contain data-verification, completed/excluded, or model-release-pending states; no provisional risk is fabricated.
- `POST /assistant/query`: accepts only `request_id`, `question`, and optional `canonical_project_id`.

Abstained/withheld predictions require null probability and risk band. Contributors are predictive evidence, not causes. Errors use `{"error":{"code","message"}}`; validation adds bounded details. OpenAPI at `/docs` is the machine-readable contract.
