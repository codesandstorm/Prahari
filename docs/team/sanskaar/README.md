# Sanskaar — UX / Frontend & Dashboard Architecture

**Role:** UX and Frontend Lead — Officer Workflow and Dashboard Design
**Area:** UX research, dashboard information architecture, user flows, frontend contract
**Last Updated:** 2026-09-01

---

## Current Responsibility

- Research the officer workflow — how project monitoring officers currently use PAIMANA
- Design the dashboard information architecture for PRAHARI
- Map user flows for early warning notification and risk exploration
- Specify frontend API contract requirements for Jashan
- Ensure PRAHARI's output is interpretable and actionable for non-technical users

---

## Owned Documents

| Document | Status |
|---|---|
| [UX_RESEARCH.md](UX_RESEARCH.md) | RESEARCH IN PROGRESS |
| [DASHBOARD_INFORMATION_ARCHITECTURE.md](DASHBOARD_INFORMATION_ARCHITECTURE.md) | NOT STARTED |
| [USER_FLOWS.md](USER_FLOWS.md) | NOT STARTED |
| [FRONTEND_CONTRACT_REQUIREMENTS.md](FRONTEND_CONTRACT_REQUIREMENTS.md) | NOT STARTED |

---

## Inputs Required

| From | What | Status |
|---|---|---|
| Akshita | Operational context — how officers use predictions | RESEARCH IN PROGRESS |
| Jashan | API capabilities and endpoint shape | NOT STARTED |
| Pavitra | What prediction outputs look like (risk scores, horizons) | NOT STARTED |

---

## Outputs Provided

| To | What | Status |
|---|---|---|
| Jashan | Frontend API contract requirements | NOT STARTED |
| All | Officer workflow context (informs prediction design) | RESEARCH IN PROGRESS |

---

## Key Rules

- Frontend must not reconstruct database relationships from raw CSVs.
- Frontend queries the backend API only.
- Risk scores must be displayed with evidence — not as unexplained numbers.
- Design must account for non-technical users (government officers, not data scientists).

---

## Reading List

- [`../../shared/PROJECT_OVERVIEW.md`](../../shared/PROJECT_OVERVIEW.md)
- [`../../shared/API_DATA_HANDOFF.md`](../../shared/API_DATA_HANDOFF.md)
- [`../../shared/CURRENT_TECHNICAL_HYPOTHESIS.md`](../../shared/CURRENT_TECHNICAL_HYPOTHESIS.md)
- [`../../shared/OPEN_QUESTIONS.md`](../../shared/OPEN_QUESTIONS.md) — OQ-008, OQ-009
