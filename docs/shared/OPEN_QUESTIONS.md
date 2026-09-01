# Open Technical Questions

**Owner:** Sandarbh (tracker) — individual questions have per-owner
**Area:** Shared
**Document Type:** REFERENCE
**Status:** ACTIVE — add new questions, update status as resolved
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Entire team
**Canonical:** YES

> When a question is resolved, mark it RESOLVED and add the decision reference.
> Do NOT delete resolved questions — they form part of the decision history.

---

## Data / Identity

### OQ-001 — Project Code continuity across months

**Question:** Can Project Code be used consistently as the primary project identifier across May, June, and (future) July 2026?
**Owner:** Sandarbh
**Status:** OPEN — 3-month linkage not yet possible (July PDF missing)
**Dependency:** July 2026 PDF acquisition
**Decision Needed By:** Before Gate 2 milestone 7
**Notes:** May and June both have Project Code. Partial check possible for 2-month overlap.

---

### OQ-002 — Legacy OCMS Code and PMGID population rates

**Question:** What fraction of Project Code rows have a populated (non-dash) Legacy OCMS Code? PMGID?
**Owner:** Sandarbh
**Status:** PARTIALLY ANSWERED — June: all dashes. May: 817 OCMS dashes, 786 PMGID dashes out of 1,987.
**Dependency:** None — data available
**Decision Needed By:** Gate 2 milestone 9
**Notes:** May partial population is significant — cross-era linking may be possible for some projects.

---

### OQ-003 — Historical archive eligibility

**Question:** Can pre-2024 reports (2015, 2020, 2023 era) be reliably linked to modern PAIMANA records?
**Owner:** Sandarbh + Pavitra
**Status:** OPEN — depends on OQ-002 and identity research
**Dependency:** OQ-002, identity analysis (PROJECT_IDENTITY_ANALYSIS.md)
**Decision Needed By:** Gate 3 planning
**Notes:** If cross-era linking fails, longitudinal history is limited to 2024–2026.

---

### OQ-004 — Project identity gaps (disappear/reappear)

**Question:** Do projects disappear from the ongoing table for 1+ months and then reappear?
**Owner:** Sandarbh
**Status:** OPEN
**Dependency:** Multi-month linkage (Gate 2 milestone 7)
**Decision Needed By:** Gate 2 completion
**Notes:** Could indicate temporary delisting, reclassification, or data quality issue.

---

## Prediction

### OQ-005 — Prediction target horizon

**Question:** Should PRAHARI predict at 3, 6, or 12 months? Or all three?
**Owner:** Pavitra + Sandarbh
**Status:** OPEN — requires longitudinal dataset to evaluate feasibility
**Dependency:** Gate 2 complete; multi-year data required
**Decision Needed By:** Gate 3 planning
**Notes:** Shorter horizons may have better data availability but lower utility. Longer horizons require more historical depth.

---

### OQ-006 — Cost vs. schedule overrun as primary target

**Question:** Is the primary prediction target cost overrun, schedule overrun, or both?
**Owner:** Pavitra
**Status:** OPEN
**Dependency:** Domain research (Akshita), Gate 3
**Decision Needed By:** Gate 3 design
**Notes:** SIH problem statement covers both. Operationalisation needs research.

---

## Sources / CUF

### OQ-007 — CUF field availability

**Question:** Does the PAIMANA CUF contain fields that do not appear in Flash Reports?
**Owner:** Akshita + Sandarbh
**Status:** NOT STARTED — CUF documentation not obtained
**Dependency:** CUF documentation from MoSPI/PAIMANA
**Decision Needed By:** Before Gate 4 feature design
**Notes:** See docs/reference/CUF_RESEARCH_STATUS.md

---

## Product / Operations

### OQ-008 — Alert policy definition

**Question:** What threshold of risk score should trigger an early warning alert? Who receives it?
**Owner:** Akshita + Sanskaar
**Status:** RESEARCH IN PROGRESS
**Dependency:** Domain research, operational context
**Decision Needed By:** Gate 5 evaluation design
**Notes:** Operational context matters — a 60% risk score may have different implications for different project types.

---

### OQ-009 — Evidence display alongside predictions

**Question:** What evidence should be displayed to officers alongside a risk score?
**Owner:** Sanskaar + Akshita
**Status:** RESEARCH IN PROGRESS
**Dependency:** UX research, domain context
**Decision Needed By:** Pre-frontend implementation
**Notes:** SHAP explanations are candidate evidence, but interpretability for non-technical users needs design.

---

## Backend

### OQ-010 — Trend materialisation strategy

**Question:** Should portfolio-level trend calculations be materialised (pre-computed) or calculated on request?
**Owner:** Jashan
**Status:** OPEN
**Dependency:** Data volume estimates (Gate 2), query patterns (Sanskaar)
**Decision Needed By:** Backend design phase
**Notes:** Materialized views offer performance; on-demand offers flexibility.
