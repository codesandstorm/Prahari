# Audit Index

**Owner:** Team (Sandarbh as primary auditor)
**Area:** Audits
**Document Type:** REFERENCE
**Status:** ACTIVE
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Entire team
**Canonical:** YES

---

## Completed Audits

| Audit | Scope | Date | Status | Location |
|---|---|---|---|---|
| Source Integrity Audit | SHA-256 verification of all 13 source PDFs | 2026-09-01 | COMPLETE | `validation/source_audit/raw_hashes_pre_extraction.csv` |
| June 2026 Manual Sample Validation | 30 rows manually reviewed against source PDF | 2026-09-01 | COMPLETE | `validation/extraction_validation/june_2026_manual_sample_30_REVIEWED.csv` |
| May 2026 Extraction | 1,987 rows extracted and structurally validated | 2026-09-01 | COMPLETE | `validation/extraction_validation/may_2026_extraction_summary.json` |

---

## Pending Audits

| Audit | Scope | Prerequisite | Status |
|---|---|---|---|
| July 2026 Extraction Audit | Full extraction + manual sample validation | July 2026 PDF | BLOCKED — PDF not obtained |
| Multi-month Identity Audit | Project Code continuity across 3 months | All 3 months extracted | BLOCKED |
| Gate 2 Final Audit | Independent review of all Gate 2 milestones | All milestones VERIFIED | NOT STARTED |

---

## Audit Template

Use: [`../templates/AUDIT_TEMPLATE.md`](../templates/AUDIT_TEMPLATE.md)

## Adding a New Audit

1. Copy the audit template.
2. Name the file: `<SCOPE>_AUDIT_<YYYY_MM>.md` in this directory.
3. Add an entry to this INDEX.md.
4. Cross-reference from the relevant GATE_STATUS.md milestone.
