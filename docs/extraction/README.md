# Extraction Specifications

**Area:** Extraction
**Last Updated:** 2026-09-02

This directory contains frozen extraction specifications for each source report.

An extraction specification documents exactly what was extracted, from which
source (by SHA-256), using which method, with what structural rules applied.

Extraction specifications are **frozen** once extraction is complete and validated.
They are NOT modified when new extractions are done — a new spec is created instead.

---

## Active Specifications

| Document | Source | Status |
|---|---|---|
| [APRIL_2026_EXTRACTION_SPEC.md](APRIL_2026_EXTRACTION_SPEC.md) | April 2026 (SRC-2026-04) | AUTOMATED VALIDATION COMPLETE — HUMAN PENDING |
| [APRIL_2026_SCHEMA_COMPARISON.md](APRIL_2026_SCHEMA_COMPARISON.md) | April vs May/June | REVIEWED |
| [PAIMANA_V2_EXTRACTION_SPEC.md](PAIMANA_V2_EXTRACTION_SPEC.md) | June 2026 (SRC-2026-06) | APPROVED |
| [PAIMANA_V2_MAY_2026_EXTRACTION_SPEC.md](PAIMANA_V2_MAY_2026_EXTRACTION_SPEC.md) | May 2026 (SRC-2026-05) | APPROVED |
| [MAY_2026_SCHEMA_COMPARISON.md](MAY_2026_SCHEMA_COMPARISON.md) | May vs June comparison | APPROVED |

---

## Creating a New Extraction Specification

Use the template: [`../templates/EXTRACTION_REVIEW_TEMPLATE.md`](../templates/EXTRACTION_REVIEW_TEMPLATE.md)

Required elements:
- Source ID and SHA-256
- Table boundaries (physical PDF pages)
- Exact column structure
- Row and page behavior rules
- Missing value conventions
- Method and output fields
- Final status

Do not create a spec for extractions that have not been independently verified.
