# Current Technical Hypothesis

**Owner:** Sandarbh + Pavitra
**Area:** Shared / ML Architecture
**Document Type:** APPROVED
**Status:** APPROVED — architecture only; no model families locked
**Last Updated:** 2026-09-01
**Depends On:** PROJECT_OVERVIEW.md, DATA_CONTRACT.md
**Used By:** Entire team
**Canonical:** YES

---

## Statement

PRAHARI uses an evidence-gated multi-layer architecture:

```
Layer 1 — Rules
  Purpose: data integrity, temporal integrity, operational guardrails
  Examples: completeness checks, monotonicity checks, provenance validation
  Status: ARCHITECTURE APPROVED

Layer 2 — Statistical Baseline
  Purpose: scientific baseline that ML must demonstrably beat
  Examples: logistic regression, survival analysis, control chart rules
  Status: ARCHITECTURE APPROVED — implementation at Gate 5

Layer 3 — Supervised ML
  Purpose: candidate predictive engine
  Examples: gradient boosting, random forest (families NOT locked)
  Constraint: must be calibrated, interpretable, evidence-backed
  Status: ARCHITECTURE APPROVED — implementation at Gate 5

Layer 4 — LLM (optional)
  Purpose: downstream explanation and natural-language query layer
  Constraint: grounded in verified model output only; NOT predictive
  Status: PLAUSIBLE — not designed yet
```

---

## Evidence Requirements Before Each Layer Is Implemented

| Layer | Prerequisite Gate |
|---|---|
| Rules | Gate 2 complete (validated dataset) |
| Statistical Baseline | Gate 3 complete (label audit) + Gate 4 complete (leakage-safe features) |
| Supervised ML | Gate 5 (baseline established, ML must demonstrate improvement) |
| LLM | Gate 5 + validated prediction pipeline |

---

## What This Hypothesis Does NOT Lock

- Specific ML model families (tree, linear, neural — evidence decides)
- Specific target horizon (3 / 6 / 12 months — evidence from Gate 3)
- Specific features (Gate 4 research decides)
- LLM vendor or approach (post-Gate 5 decision)

---

## Relationship to Research Questions

| RQ | Question | Status |
|---|---|---|
| RQ1 | Can cost/schedule overruns be predicted before formal revision? | OPEN |
| RQ2 | How early can they be predicted? | OPEN — needs longitudinal data |
| RQ3 | Which CUF fields contribute most to prediction? | BLOCKED — CUF research needed |
| RQ4 | Do engineered temporal features add value? | OPEN — Gate 4 |
| RQ5 | Do external variables improve CUF-only prediction? | OPEN |
| RQ6 | Does ML outperform conventional statistical baselines? | OPEN — Gate 5 |
| RQ7 | Can predictions be calibrated and interpretable? | OPEN — Gate 5 |

---

## Revision Conditions

This hypothesis is revised when:
- New evidence from Gates 3–5 invalidates an assumption
- The statistical baseline is established and provides unexpected findings
- A specific ML approach is validated or rejected empirically

Every revision must be logged in [`DECISION_LOG.md`](DECISION_LOG.md).
