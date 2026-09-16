# Backend Integration Handoff

Replace imports from `src/data/mock` with a typed adapter layer. Do not change page semantics to accommodate raw transport shapes.

## Recommended adapters

1. Portfolio adapter: summary KPIs, projects, state distribution and updates.
2. Unified project adapter: Current State, Data Quality, research/release status, Execution Health, peer comparison and Officer Action.
3. Workflow adapter: governed alerts, reviews, lifecycle events, notes and evidence snapshots.
4. Assistant adapter: context, cited evidence and fail-closed response states.

## Governance requirements

- Preserve backend release status; never derive it from probability.
- Render `WITHHELD`, unavailable and insufficient-evidence states explicitly.
- Alerts may only come from the governed Officer Decision/policy layer.
- Preserve provenance IDs, reporting month, page references and evidence hashes.
- Treat Data Quality, reliability, model probability, risk and administrative priority as separate fields.
- Authenticate server-side; the current login is visual-only.

Add loading, empty, authorization and retry states at the adapter boundary. Mutations should use idempotency keys and server-returned lifecycle state.
