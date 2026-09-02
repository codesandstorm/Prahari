# April 2026 Schema Comparison

**Owner:** Sandarbh
**Area:** Extraction / April 2026
**Document Type:** REVIEW
**Status:** AUTOMATED VALIDATION COMPLETE — HUMAN VALIDATION PENDING
**Last Updated:** 2026-09-02
**Depends On:** PAIMANA_V2_EXTRACTION_SPEC.md, PAIMANA_V2_MAY_2026_EXTRACTION_SPEC.md
**Used By:** Gate 2 Data Engineering
**Canonical:** YES

## Field-level comparison

| Concept | April | May | June | Compatibility |
|---|---|---|---|---|
| Table columns | 8 | 8 | 8 | Same |
| Header wording | PAIMANA V2 Table 6 | PAIMANA V2 Table 6 | PAIMANA V2 Table 6 | Same, including source spelling `Orignal` |
| Identity cell | Name, Agency, Project Code, Legacy OCMS, PMGID | Same | Same | Same bottom-anchored structure |
| Project Code | Own parenthesized line | Same | Same | Same |
| Legacy OCMS / PMGID | Paired final line | Same | Same | Same |
| Approval / start | Two lines; start parenthesized | Same | Same | Same |
| Original / revised DoC | Two lines throughout | 11 `(-)`-only cells | Two-line form | April matches normal form; May has documented exception |
| Original / revised cost | Two lines; revised parenthesized | Same | Same | Same |
| Expenditure / progress | Separate scalar columns | Same | Same | Same |
| Missing tokens observed | `-`, `NA` | `-` and documented `(-)` cell | `-` | Compatible; raw tokens preserved |
| Sector headings / totals | 48 / 31 | 48 / 31 | Present | Same structural pattern |
| Repeated headers | 108 | 109 | 101 | One per April data page |
| Project continuations | None observed | None observed | None observed | Same |
| Title / data pages | 54 / 55–162 | 53 / 54–162 | 58 / 59–159 | Different boundaries; explicitly contracted |

## Decision

April is a **COMPATIBLE_VARIATION**, not declared byte-identical to either month. A narrow April adapter reuses only the verified May row parser and supplies April-specific source identity, observation IDs, boundaries, expected count, validation, provenance, and sample generation. No year-based schema rule or modification to the frozen June extractor was introduced.
