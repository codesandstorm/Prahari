# Data Engineering Status

**Owner:** Sandarbh
**Area:** Data Engineering
**Document Type:** REFERENCE
**Status:** ACTIVE — updated continuously
**Last Updated:** 2026-09-01
**Depends On:** DATA_CONTRACT.md, GATE_STATUS.md
**Used By:** Team lead, Jashan (backend dependency tracking)
**Canonical:** YES

---

## Current Status (2026-09-01)

### Completed

| Task | Evidence | Date |
|---|---|---|
| Source integrity audit (all 13 PDFs) | `validation/source_audit/raw_hashes_pre_extraction.csv` | 2026-09-01 |
| Schema classification across all held PDFs | SCHEMA_EVOLUTION.md + DECISION_LOG entries | 2026-09-01 |
| June 2026 extraction (1,847 rows) | `data/extracted/ongoing/ongoing_2026_06.csv` | 2026-09-01 |
| June 2026 manual validation (30 rows) | `validation/extraction_validation/june_2026_manual_sample_30_REVIEWED.csv` | 2026-09-01 |
| May 2026 extraction (1,987 rows) | `data/extracted/ongoing/ongoing_2026_05.csv` | 2026-09-01 |
| Provenance infrastructure | `data/metadata/provenance.csv`, `source_manifest.csv` | 2026-09-01 |

### Active

- Multi-month identity research (blocked on July 2026 PDF)

### Blocked

- July 2026 extraction — PDF not obtained
- 3-month project linkage — blocked by above
- project_month.csv final production — blocked by identity validation

### Not Started (Gate 3+)

- Feature engineering
- Outcome/label construction
- Leakage-safe temporal splitting

---

## Key Technical Decisions

All in [`../../shared/DECISION_LOG.md`](../../shared/DECISION_LOG.md):

| Decision | ID |
|---|---|
| Repository structure | DEC-001 |
| PDF extraction library (pdfplumber primary) | DEC-002 |
| No uncontrolled fuzzy matching | DEC-003 |
| Raw extraction files are immutable | DEC-004 |
| No ML until Gate 2 verified | DEC-005 |
| Filename convention | DEC-006 |
| July 2026 duplicate filing | DEC-007 |
| PAIMANA_V2_CANDIDATE schema class | DEC-008 |
| Partial/excerpt file flagging | DEC-009 |
| OCR ruled out | DEC-010 |
| Multipart naming convention | DEC-011 |
| REJECTED_DUPLICATE status | DEC-012 |
| Schema detector rules refactoring | DEC-013 |
| Error state distinction | DEC-014 |
| Raw-path write guard | DEC-015 |
| Manual vs automated schema assessment | DEC-016 |
