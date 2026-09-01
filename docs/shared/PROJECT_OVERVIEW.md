# PRAHARI — Project Overview

**Owner:** Team (Sandarbh — primary author)
**Area:** Shared / Project Understanding
**Document Type:** REFERENCE
**Status:** APPROVED
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Entire team, new members, Codex/Antigravity agents
**Canonical:** YES

> Previously: `docs/TEAM_LEAD_TECHNICAL_UNDERSTANDING.md`  
> Moved to: `docs/shared/PROJECT_OVERVIEW.md` — 2026-09-01

---

**Document Purpose:** Conceptual reference for the entire team — explains the WHY behind
key technical decisions. Written for clarity, not to impress. Does not contain
invented PRAHARI results.

---

## What is PRAHARI?

PRAHARI (Predictive Risk Assessment for HIgh-value Infrastructure) is an explainable,
confidence-aware predictive decision-intelligence layer intended to sit on top of
PAIMANA (Project Assessment, Infrastructure Monitoring and Analytics for Nation-building),
MoSPI's infrastructure project monitoring platform.

**PRAHARI complements PAIMANA. It is decision support, not automated government action.**

PRAHARI will eventually become:
- A system that can predict cost and schedule overruns before they formally materialise
- A risk-scoring and early-warning engine
- A benchmarking and prioritisation tool
- An evidence-grounded decision-intelligence layer

The system is architected as evidence-gated layers:

```
Rules       → data integrity, temporal integrity, operational guardrails
Statistics  → scientific baseline (must be beaten before ML is added)
Supervised ML → candidate predictive engine (gated on validated data)
LLM         → optional downstream explanation/query layer (grounded, not predictive)
```

---

## 1. What Is One Observation?

One observation is the **state of a single infrastructure project as reported in a
single monthly Flash Report**.

It is NOT the project itself. It is a snapshot of the project at one point in time.

Example:
- Project 618702 as reported in May 2026 → **one observation**
- Project 618702 as reported in June 2026 → **another observation**
- Project 618702 as reported in July 2026 → **a third observation**

The project is one entity. The observations are many.

---

## 2. Why Is This Longitudinal Data?

Longitudinal data tracks the same entities (projects) repeatedly over time.

MoSPI publishes monthly Flash Reports. Each report covers hundreds or thousands of
ongoing projects. When we align the same project across reports, we get a time series
of how that project evolved — its cost grew, its schedule slipped, its physical
progress changed.

This is fundamentally different from cross-sectional data. Longitudinal data requires:
- Projects cannot be randomly split row-by-row into train/test sets.
- Features must respect the direction of time.
- The history of a project up to month T is different from its future after T.

---

## 3. What Is a Project ID?

A project ID is the **canonical identifier** that lets us say "these two rows refer
to the same physical infrastructure project".

In modern PAIMANA V2 reports, the `Project Code` column serves this role.
The `Legacy OCMS Code` field in modern reports is supposed to bridge old and new.

Whether these identifiers are reliable, stable, and complete is a **research question**
that Gate 2 must answer empirically.

---

## 4. How Do Monthly Reports Connect?

Reports connect through project identity. If project P appears in the May 2026 report
and again in the June 2026 report with the same `Project Code`, then we can align their
observations into a time series for project P.

This alignment is the central task of Gate 2.

---

## 5. Which Fields Change Over Time?

| Field | Changes? | Notes |
|---|---|---|
| `revised_cost` | YES | May change every month |
| `cumulative_expenditure` | YES | Should increase monotonically |
| `physical_progress_pct` | YES | Should increase (but may stall) |
| `revised_doc` | YES | May be pushed back repeatedly |
| `project_status_raw` | YES | May transition (active → delayed → completed) |
| `project_name` | USUALLY NO | But name changes are possible |
| `agency` | USUALLY NO | But agency transfers occur |
| `original_cost` | USUALLY NO | Should be fixed at approval |
| `date_of_approval` | NO | Fixed |
| `start_date` | NO | Fixed |
| `original_doc` | USUALLY NO | Technically fixed but may be corrected |

---

## 6. Which Fields Are Stable?

Static fields: project name, agency, state, approval date, start date, original cost,
original target DOC.

In practice, minor administrative changes can cause apparent "changes". Anomaly
detection must flag unexpected changes rather than silently accept them.

---

## 7. What Constitutes a Future Outcome?

An outcome is something that happens **after** the prediction date.

Examples:
- Did the revised cost increase by more than 20% in the next 12 months?
- Was the revised DOC pushed back more than 6 months?
- Was the project completed on its current revised DOC?

These outcomes are derived from future observations and become labels during dataset
preparation. They must NEVER appear as input features to a model.

---

## 8. What Is Temporal Leakage?

Temporal leakage is when a model is given information not available at the time
the prediction was supposed to be made.

Temporal leakage causes evaluation metrics to be optimistically biased. The model
appears to perform well in testing but fails in deployment.

See [`docs/team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md`](../team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md)
for the full risk catalogue.

---

## 9. Why Should Project-Month Rows Not Be Randomly Split?

With project-month data, a random split may assign month T+6 of project P to the
training set and month T of project P to the test set. The model effectively trains
on the "future" of a project.

The correct approach:
- **Project-level split**: all months of project P go to either train OR test, never both.
- **Temporal split**: all observations before date D are training; all after D are test.

---

## 10. How Do Completed Projects Provide Ground Truth?

Completed projects are the only projects where we know the actual outcome:
- Actual completion date (vs. original target and last revised target)
- Final reported cumulative expenditure (vs. original and revised cost)

Only completed projects can provide verified outcome labels.

---

## 11. How Are Prediction Horizons Tested?

Testing prediction horizons requires:
1. A longitudinal dataset spanning multiple years.
2. Ground-truth outcomes (from completed-project records).
3. Features derived only from observations at or before the prediction date.
4. Separate evaluation at different horizons (3 months, 6 months, 12 months, etc.)

This is only possible after Gate 2 is complete and data spans enough years.

---

## 12. Why Benchmark Conventional Statistics Against ML?

- If a simple linear regression performs as well as a neural network, the simpler
  model is preferred for interpretability and trust in a government context.
- Establishing a baseline prevents teams from "proving" ML works when a naive
  baseline would do the same.
- Government decision-makers may be more likely to trust explainable statistical
  models over black-box ML.

---

## 13. What Is Model Calibration?

A calibrated model is one where its stated confidence matches empirical accuracy.

Example: If a model says "80% probability of cost overrun" for 100 projects,
approximately 80 of those should actually experience a cost overrun.

For administrative decision support, calibration matters because stakeholders need
to understand what a "high risk" score actually means in practice.

---

## 14. How Will Model Output Eventually Reach the Backend?

[PLACEHOLDER — To be designed after Gate 3]

General expected path:
- Model produces predictions + confidence scores + SHAP explanations.
- These are stored in a database (or flat files in early stage).
- A backend API (FastAPI or similar) reads predictions and exposes them.
- The frontend dashboard queries the API.

See [`docs/shared/API_DATA_HANDOFF.md`](API_DATA_HANDOFF.md) for the provisional handoff contract.

---

## 15. How Will the Backend Expose Predictions to the Frontend?

[PLACEHOLDER — To be designed after Gate 3]

Likely approach: REST API with JSON responses. Each project has an endpoint
returning current risk scores, trend data, and explanation tokens.

See [`docs/team/jashan/API_CONTRACTS.md`](../team/jashan/API_CONTRACTS.md) for backend API contract progress.

---

## 16. Why Should an LLM Not Perform the Predictive Task?

An LLM:
- Has no access to MoSPI project data unless explicitly provided.
- Cannot reliably perform numerical extrapolation or time-series prediction.
- Has no mechanism for uncertainty quantification or calibration.
- Can hallucinate plausible-sounding project statistics.

LLMs are appropriate for: summarising verified findings, answering NL questions
grounded in verified data, generating report text from structured model outputs.

LLMs are NOT appropriate for: making the primary predictive judgment on cost or
schedule, replacing a validated statistical model, or inventing risk scores.

---

*No section of this document contains PRAHARI results. All descriptions are conceptual.*
