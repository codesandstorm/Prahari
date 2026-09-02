# PRAHARI Gate Status

**Owner:** Sandarbh (Data Lead) / Team
**Area:** Shared / Project Gates
**Document Type:** REFERENCE
**Status:** ACTIVE — updated as gates progress
**Last Updated:** 2026-09-02
**Depends On:** DECISION_LOG.md
**Used By:** Entire team
**Canonical:** YES

> Previously: `docs/GATE2_DATASET_STATUS.md`
> Moved to: `docs/shared/GATE_STATUS.md` — 2026-09-01

---

## Gate Dashboard

| Gate | Title | Status |
|---|---|---|
| Gate 1 | Problem Definition & Architecture Research | COMPLETE |
| Gate 2 | Data Engineering & Longitudinal Dataset | **ACTIVE** |
| Gate 3 | Outcome / Label Audit | NOT STARTED (research only permitted) |
| Gate 4 | Leakage-Safe Feature Engineering | NOT STARTED |
| Gate 5 | Rule vs Statistics vs ML Evaluation | NOT STARTED |
| Gate 6 | Early Warning System Evaluation | NOT STARTED |

> [!IMPORTANT]
> Do not advance any gate until the prior gate is VERIFIED. Gate 3 must not start
> until all 12 Gate 2 milestones below are verified.

---

## Gate 2 — Active

**Status:** IN PROGRESS  
**Classification System:** VERIFIED | PLAUSIBLE | UNKNOWN | REJECTED

### Milestone Status

| # | Milestone | Status | Evidence | Notes |
|---|---|---|---|---|
| 1 | July 2026 ongoing table extracted | UNKNOWN | — | Not yet attempted — July 2026 PDF not obtained |
| 2 | Row count reconciled (~1,775) | UNKNOWN | — | Target was July; June has 1,847 |
| 3 | Source page recorded per row | VERIFIED | June 2026 extraction | All 1,847 rows include physical + printed page |
| 4 | 20–30 sample rows manually verified | VERIFIED | june_2026_manual_sample_30_REVIEWED.csv | Manual review complete |
| 5 | June 2026 extracted | VERIFIED | ongoing_2026_06.csv | 1,847 rows, SHA verified |
| 6 | May 2026 extracted | VERIFIED | ongoing_2026_05.csv | 1,987 rows, SHA verified |
| 7 | Project IDs linked across three months | UNKNOWN | — | Pending — July 2026 missing |
| 8 | Missingness quantified | PLAUSIBLE | May/June specs | Legacy OCMS/PMGID null rates documented |
| 9 | Identifier coverage measured | UNKNOWN | — | Pending full multi-month linkage |
| 10 | `project_month.csv` created (3 months) | UNKNOWN | — | Pending July 2026 |
| 11 | `project_master.csv` created | UNKNOWN | — | Pending identity resolution |
| 12 | Full provenance preserved | VERIFIED | provenance.csv | All rows bound to manifest SHA |

### Gate 2 Blocking Issues

- **July 2026 PDF not obtained.** July is required for 3-month linkage. Milestones 7, 10, 11 blocked.
- **Identity continuity not yet validated.** `project_month` is not final until identity research complete.

### Source Inventory (current)

| Source ID | File | Year/Month | Schema | Status |
|---|---|---|---|---|
| SRC-2026-04 | FlashReport_2026_04.pdf | 2026-04 | PAIMANA_V2 HIGH | AUTOMATED VALIDATION COMPLETE — HUMAN PENDING |
| SRC-2026-05 | FlashReport_2026_05.pdf | 2026-05 | PAIMANA_V2 HIGH | EXTRACTED |
| SRC-2026-06 | FlashReport_2026_06.pdf | 2026-06 | PAIMANA_V2 HIGH | EXTRACTED + VALIDATED |
| SRC-2026-06-DUP | FlashReport_2026_07.pdf | 2026-06 (DUPLICATE) | — | REJECTED_DUPLICATE |
| — | FlashReport_2026_07.pdf (actual) | 2026-07 | — | NOT OBTAINED |

See `data/metadata/source_manifest.csv` for complete source registry.

### Gate 2 → Gate 3 Transition Criteria

Gate 3 MUST NOT start until all 12 milestones above are `VERIFIED`.

Gate 3 is NOT approved by the existence of a CSV file alone.
Gate 3 is approved when extraction accuracy has been independently confirmed via manual sample validation.

---

## Gate 1 — Complete

Architecture decisions, repository structure, extraction library selection, schema
detection logic, provenance requirements, and ML gate policy all established.

See [`docs/shared/DECISION_LOG.md`](DECISION_LOG.md) for DEC-001 through DEC-016.

---

## Gates 3–6 — Not Started

Research may proceed. No implementation. No ML libraries. No risk scores.

See [`docs/shared/OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) for pending research questions.
