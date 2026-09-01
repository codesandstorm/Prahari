# Pavitra — Prediction Research & Independent Data Audit

**Role:** ML/Statistical Research Lead + Independent Data Auditor
**Area:** Prediction formulation, targets, labels, statistical/ML evaluation
**Last Updated:** 2026-09-01

---

## Current Responsibility

- Prediction problem formulation (what PRAHARI predicts, how, for whom)
- Target and label research (what constitutes a cost/schedule overrun)
- Baseline model research (statistical baselines that ML must beat)
- Independent audit of the Gate 2 dataset (cross-validation of Sandarbh's extraction)
- Temporal validity rules (working with Sandarbh on leakage prevention)

---

## Owned Documents

| Document | Status |
|---|---|
| [PREDICTION_FORMULATION.md](PREDICTION_FORMULATION.md) | NOT STARTED |
| [TARGET_AND_LABEL_RESEARCH.md](TARGET_AND_LABEL_RESEARCH.md) | NOT STARTED |
| [BASELINE_MODEL_RESEARCH.md](BASELINE_MODEL_RESEARCH.md) | NOT STARTED |
| [DATASET_INDEPENDENT_AUDIT.md](DATASET_INDEPENDENT_AUDIT.md) | NOT STARTED |

---

## Inputs Required

| From | What | Status |
|---|---|---|
| Sandarbh | Validated Gate 2 dataset (project_month, completion_events) | NOT YET FINAL |
| Sandarbh | Leakage risk catalogue | AVAILABLE (TEMPORAL_LEAKAGE_NOTES.md) |
| Akshita | Domain definition of "overrun" in operational context | RESEARCH IN PROGRESS |

---

## Outputs Provided

| To | What | Status |
|---|---|---|
| Sandarbh | Target horizon decision | OPEN |
| All | Independent audit findings on Gate 2 data | NOT STARTED |
| Jashan | Feature/label schema (post-Gate 3) | FUTURE |

---

## Current Blockers

- Gate 2 dataset not yet finalized — cannot begin label research without validated data.
- Domain definition of "overrun" threshold not yet agreed.

---

## Reading List (to orient before Gate 3)

- [`../../shared/PROJECT_OVERVIEW.md`](../../shared/PROJECT_OVERVIEW.md) — conceptual model
- [`../../shared/CURRENT_TECHNICAL_HYPOTHESIS.md`](../../shared/CURRENT_TECHNICAL_HYPOTHESIS.md) — architecture
- [`../../shared/DATA_CONTRACT.md`](../../shared/DATA_CONTRACT.md) — data model
- [`../sandarbh/TEMPORAL_LEAKAGE_NOTES.md`](../sandarbh/TEMPORAL_LEAKAGE_NOTES.md) — leakage risks
- [`../../shared/OPEN_QUESTIONS.md`](../../shared/OPEN_QUESTIONS.md) — OQ-005, OQ-006
