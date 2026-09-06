# PRAHARI Mixed-Coverage Schema Matrix

**Calendar window:** July 2023--June 2026 (36 intended months)

**Observed coverage:** 30 project-level, 5 aggregate-only, 1 missing

**Status:** PROVISIONAL - MIXED COVERAGE - HUMAN VALIDATION PENDING

The machine-readable matrix is `data/metadata/schema_family_2023_07_2026_06.csv`.
Schema routing is based on table titles, headers, column structure, and identifiers--not year.

| Period/months | Coverage | Evidence-backed schema | Identity | Important limitation |
|---|---|---|---|---|
| 2023-07--2023-11 | PROJECT_LEVEL | OCMS, seven logical cells | embedded Legacy OCMS/project code | no physical-progress percentage; milestones reported instead |
| 2023-12 | AGGREGATE_ONLY | NO_PROJECT_LEVEL_SCHEMA | none | summary and selected annexures only |
| 2024-01--2024-03 | PROJECT_LEVEL | OCMS, seven logical cells | embedded Legacy OCMS/project code | no physical-progress percentage |
| 2024-04, 2024-05 | AGGREGATE_ONLY | NO_PROJECT_LEVEL_SCHEMA | none | short report-level summaries |
| 2024-06, 2024-07 | PROJECT_LEVEL | PAIMANA_V1 compatible variation | Project Code | variable 7/8/9 extracted cells; seven stable rightmost fields |
| 2024-08, 2024-09 | AGGREGATE_ONLY | NO_PROJECT_LEVEL_SCHEMA | none | two-page report-level summaries |
| 2024-10--2025-01 | PROJECT_LEVEL | PAIMANA_V1 compatible variation | Project Code | national table selected separately from North-East subset |
| 2025-02 | MISSING_SOURCE | NO_PROJECT_LEVEL_SCHEMA | none | public source unavailable |
| 2025-03--2025-06 | PROJECT_LEVEL | PAIMANA_V1 compatible variation | Project Code | national table only |
| 2025-07--2026-03 | PROJECT_LEVEL | existing validated PAIMANA variants | Project Code; Legacy OCMS in later variants | reused frozen 12-month outputs |
| 2026-04--2026-06 | PROJECT_LEVEL | existing validated PAIMANA_V2 | Project Code, Legacy OCMS, PMGID | reused frozen outputs |

`UNKNOWN` fails closed. Aggregate-only and missing months never enter `project_month.csv`.
