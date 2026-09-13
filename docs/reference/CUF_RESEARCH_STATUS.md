# CUF Research Status

**Owner:** Akshita (domain lead) + Sandarbh
**Area:** Reference / CUF / Data Sources
**Document Type:** RESEARCH
**Status:** COMPLETE
**Last Updated:** 2026-09-13
**Depends On:** NONE
**Used By:** Entire team
**Canonical:** YES

> Previously: `docs/CUF_RESEARCH_STATUS.md`  
> Moved to: `docs/reference/CUF_RESEARCH_STATUS.md` — 2026-09-01

---

**Document Purpose:** Track research into MoSPI Common Upload Form (CUF) fields
and their relationship to PRAHARI's data model.  
**Status:** COMPLETE - official CUF obtained and reconciled

---

## Background

The SIH problem statement asks teams to evaluate:

> The predictive value of **existing CUF fields** versus additional variables.

This document tracks:
1. Which fields in the CUF overlap with what is visible in Flash Reports.
2. Which CUF fields have NO visible counterpart in Flash Reports.
3. Whether additional variables beyond CUF might improve predictions.

---

## What Is the CUF?

The Common Upload Form (CUF) is the data submission mechanism through which
implementing agencies report project status to PAIMANA.

The Flash Reports likely derive from CUF data, but the CUF may contain more
detailed fields that are aggregated or omitted in published Flash Reports.

**Research Question:** Are Flash Report fields a subset or superset of CUF fields?

---

## CUF Field Inventory

> **Status: VERIFIED.** The official 17-page MoSPI/IPMD memorandum and annexures were reviewed. The controlling record is [`../cuf/PRAHARI_CUF_FIELD_CONTRACT_V1.md`](../cuf/PRAHARI_CUF_FIELD_CONTRACT_V1.md), with machine-readable mappings in `config/cuf_field_registry.json`.

| CUF Field | Present in Flash Reports? | Notes |
|---|---|---|
| Annexure II 29 major parameters | Mixed | Dates and cost/expenditure overlap; funding and plan-phasing fields are absent historically. |
| Annexure I land, ROW, clearances and tenders | No structured counterpart | Future PAIMANA/CUF input only. |
| Annexure III milestones | Raw text exists in a minority of rows but is not structured | Not currently computable. |

---

## Flash Report Fields Without CUF Counterpart (Candidate List)

Historical Flash Reports additionally contain agency labels and anticipated completion/cost fields. Agency is not assumed to be contractor; anticipated values retain their distinct historical semantics.

---

## Additional Variables (Beyond CUF)

Research Question RQ5 asks whether external variables improve prediction.

Candidate categories (all PLAUSIBLE, none VERIFIED):

| Category | Example Variables | Source | Status |
|---|---|---|---|
| Macroeconomic | Steel price index, cement price index, construction cost index | MOSPI / CMI | PLAUSIBLE |
| Governance | Implementing agency historical performance | Flash Reports | PLAUSIBLE |
| Geography | State / district infrastructure maturity index | External | PLAUSIBLE |
| Weather / monsoon | Extreme weather events affecting construction | IMD | PLAUSIBLE |
| Regulatory | Environmental clearance delays | MoEF records | UNKNOWN |

**No external data will be incorporated until CUF fields are fully understood and
the Gate 2 dataset is validated.**

---

## Open Questions

- [x] Official CUF schema obtained and fingerprinted.
- [x] CUF is richer than current Flash Report project-month data.
- [x] CUF contains plan, funding, land, ROW, clearance, tender and milestone fields that can precede final revisions.
- [x] CUF contains tender and implementing-agency information; it does not establish a contractor-performance field.
- [x] CUF Annexure III defines broad physical milestone categories and dates/costs.

---

*The detailed current contract and availability matrix are maintained under `docs/cuf/`.*

