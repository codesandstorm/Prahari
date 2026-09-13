# PRAHARI Frontend API Contract V1

**Owner:** PRAHARI frontend and backend team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** REFERENCE

All routes are under `/api/v1`. Portfolio Dashboard uses `/dashboard/summary`; Project List uses `/projects`; Project Detail and Data Trust use `/projects/{id}`; History and Provenance use `/projects/{id}/history`; Prediction uses `/projects/{id}/prediction`; Review Queue uses `/review-queue`; Assistant uses `POST /assistant/query`.

The frontend may display returned identity, observation, source, trust dimension, release, eligibility, decision, reason, reliability and status fields. It must never calculate risk, trust, eligibility, priority, review state or alert state.

## Cost intelligence extension

Project detail/evidence may include `cost_intelligence` with status, C1/C2 family, horizon, nullable probability/band, reliability, trend, contributors, model/feature versions, as-of month, withheld reasons and explicit research/machine-provisional flags. The frontend must not infer LOW risk from a null value, combine schedule and cost probabilities, calculate a composite score, or create its own alert. In the current accepted state the object is `WITHHELD` because no cost model passed research admission.

State matrix:

| State | Required presentation |
|---|---|
| `LOADING` | Neutral progress indicator; retain no stale scientific claim. |
| `AVAILABLE` | Show server-returned probability/risk only with versions and reliability. |
| `WITHHELD` | Show no probability/risk; show eligibility reasons. |
| `DATA_VERIFICATION_REQUIRED` | Show evidence issue and recommended verification action. |
| `MODEL_RELEASE_PENDING` | Explain scientific release is pending; do not label data bad. |
| `EMPTY` | Show that no records match; do not infer success. |
| `ERROR` | Show bounded API error and request ID; do not reuse prior values. |

`NO_REVIEW_SIGNAL` records are excluded from the actionable queue API. Nullable priority means no approved ranking—not low priority.

Use `page_size=25` for project and review lists and lazy-load history and assistant content. Review queue supports `review_state`, `reason_code`, and `model_release_state` filters. Show “Retrieving verified source evidence…” during retrieval, “Generating grounded explanation…” during generation, and “Prediction withheld — evidence shown below” immediately when applicable. Timeouts must enter `ERROR` without reusing stale scientific values.
