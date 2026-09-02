# April 2026 Table 6 Extraction Specification

**Owner:** Sandarbh
**Area:** Extraction / April 2026
**Document Type:** REVIEW
**Status:** AUTOMATED VALIDATION COMPLETE — HUMAN VALIDATION PENDING
**Last Updated:** 2026-09-02
**Depends On:** APRIL_2026_SCHEMA_COMPARISON.md
**Used By:** Gate 2 Data Engineering, independent reviewer
**Canonical:** YES

## Contract

- Source: `SRC-2026-04`, hash `90a6959e976da6928440efdea9c68847d1178356e4c0ebd078c51026ddb118d5`.
- Table: Table 6 — All Ongoing Projects.
- Official count: 1,981 on physical page 4 / printed page 3.
- Title: physical 54 / printed 53.
- Data: physical 55–162 / printed 54–161.
- Extractor: `extractor_paimana_april_table6:0.1.0`.
- Output: `data/extracted/ongoing/ongoing_2026_04.csv`.

Every numeric table row must satisfy the eight-column, bottom-anchored PAIMANA V2 contract. Non-numeric rows are classified as repeated header, section heading, total, or other structural row. A numeric row that fails parsing is preserved in the unresolved artifact and blocks readiness.

Serials must be exactly 1–1981 in natural order. Project Code must be present, decimal, whitespace-clean, and unique. Every accepted row retains the complete compound cells and source ID, hash, physical and printed pages, table identity, extraction version, and unique raw-row locator.

No normalization, canonical PRAHARI identity, cross-month linking, completion meaning, feature, label, outcome, or risk value is created. The extraction remains provisional until the 30-row human sample passes.
