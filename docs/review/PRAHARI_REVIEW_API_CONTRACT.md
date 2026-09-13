# PRAHARI Alert and Review API Contract

All routes are under `/api/v1`. Real historical mode is the default. Use `mode=SYNTHETIC_SANDBOX` explicitly for synthetic records.

## Alert routes

- `POST /projects/{project_id}/alerts/evaluate`
- `POST /sandbox/projects/{project_id}/alerts/evaluate`
- `GET /alerts` and `GET /alerts/{alert_id}`
- `POST /alerts/{alert_id}/acknowledge`
- `POST /alerts/{alert_id}/start-review`
- `POST /alerts/{alert_id}/monitor`
- `POST /alerts/{alert_id}/resolve`
- `POST /alerts/{alert_id}/dismiss`
- `POST /alerts/{alert_id}/reopen`
- `GET /alerts/{alert_id}/history`

## Review routes

- `GET /reviews` and `GET /reviews/{review_id}`
- `PATCH /reviews/{review_id}`
- `POST /reviews/{review_id}/assign`
- `POST /reviews/{review_id}/notes`
- `POST /reviews/{review_id}/actions`
- `GET /workflow/metrics`

Example officer mutation:

```json
{"actor_type":"OFFICER","actor_id":"officer-17","reason":"Accepted for source verification"}
```

Queue filters include mode, review status, priority, decision, Watch state, Data Trust state, assignee and alert type. Sorts are priority, oldest unacknowledged, persistence, latest update and decision. Probability sorting is intentionally unavailable.

Validation rejects unknown fields, unsupported enum values, blank notes/reasons, unsafe identifiers, invalid dates, unsupported actions and illegal transitions. Domain failures return bounded `WORKFLOW_CONTRACT_ERROR` payloads; database transactions roll back.

The reopen action never overrides policy. It rebuilds current project intelligence server-side and succeeds only when newer equivalent governed evidence reopens the requested episode.
