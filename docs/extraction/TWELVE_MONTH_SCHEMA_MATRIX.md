# Twelve-Month Schema Matrix

**Window:** July 2025–June 2026

**Status:** PROVISIONAL — ENGINEERING USE ONLY

**Machine-readable matrix:** `data/metadata/schema_family_2025_07_2026_06.csv`

Schema selection is based on the table header and compound identity-cell structure, not the report date. A header without `Project Code` is `UNKNOWN` and fails closed.

| Month | Family | Structural variant | Table | Physical title / data pages | Adapter | Confidence |
|---|---|---|---:|---|---|---|
| 2025-07 | PAIMANA_V1 | approval date only; inline Project Code | 4 | 36 / 37–66 | `PAIMANA_V1_APPROVAL_ONLY` | HIGH |
| 2025-08 | PAIMANA_V1 | inline Project Code; approval/start pair | 4 | 36 / 37–66 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2025-09 | PAIMANA_V1 | inline Project Code; approval/start pair | 6 | 41 / 42–71 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2025-10 | PAIMANA_V1 | inline Project Code; approval/start pair | 6 | 41 / 42–72 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2025-11 | PAIMANA_V1 | inline Project Code; approval/start pair | 6 | 41 / 42–72 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2025-12 | PAIMANA_V1 | inline Project Code; approval/start pair | 6 | 49 / 50–107 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2026-01 | PAIMANA_V1 | inline Project Code; approval/start pair | 6 | 61 / 62–133 | `PAIMANA_V1_INLINE_CODE` | HIGH |
| 2026-02 | PAIMANA_V1 | inline Project Code and Legacy OCMS | 6 | 64 / 65–167 | `PAIMANA_V1_WITH_LEGACY` | HIGH |
| 2026-03 | PAIMANA_V1 | inline Project Code and Legacy OCMS | 6 | 54 / 55–156 | `PAIMANA_V1_WITH_LEGACY` | HIGH |
| 2026-04 | PAIMANA_V2 | validated frozen variant | 6 | 54 / 55–162 | frozen validated extractor | HIGH |
| 2026-05 | PAIMANA_V2 | validated frozen variant | 6 | 53 / 54–162 | frozen validated extractor | HIGH |
| 2026-06 | PAIMANA_V2 | validated frozen variant | 6 | 58 / 59–159 | frozen validated extractor | HIGH |

## Shared structural contract

- Eight logical cells after removal of extraction-only blank edge columns.
- Project identity is a compound cell containing the project name, implementing agency, and Project Code; Legacy OCMS is present only in its structural variant.
- Dates and dates of completion are reported as `MM/YYYY`; cost is reported in crore as an original/revised pair.
- Recognized missing tokens are blank, `-`, and `NA`. No imputation or anomaly correction is applied.
- Repeated headers, sector headings, totals, blanks, and other non-project rows are explicitly classified. Any unparseable digit-led row is retained as unresolved and blocks the monthly gate.

The month-to-adapter mapping in configuration is an expected-schema assertion. The parser uses the header-detected adapter on every page and blocks the month if actual structure differs from that assertion.
