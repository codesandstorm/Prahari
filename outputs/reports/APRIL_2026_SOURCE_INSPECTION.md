# April 2026 Source Inspection

## Source identity

| Property | Observed value |
|---|---|
| Source ID | `SRC-2026-04` |
| File | `data/raw/2026/FlashReport_2026_04.pdf` |
| SHA-256 | `90a6959e976da6928440efdea9c68847d1178356e4c0ebd078c51026ddb118d5` |
| File size | 3,215,216 bytes |
| Physical pages | 163 |
| PDF title | `FlashIntegratedReport1` |
| Creator / producer | Microsoft Reporting Services 2022.1.0.0 / iLovePDF |
| Text extractable | YES |

Text was present on the opening pages, physical pages 54–55, representative middle page 108, final data page 162, and page 163 after the table. OCR is not required.

## Official count and Table 6

- Expected ongoing projects: **1,981**.
- Evidence: physical page 4, printed page 3, April 2026 overview, statement `1981 | 17 Ongoing Projects | Line Ministries & Departments`.
- Table title: `Table 6: All Ongoing Projects`.
- Title page: physical 54 / printed 53.
- Data pages: physical 55–162 / printed 54–161, contiguous.
- Page 163 contains only the report footer and is excluded.

## Structure

| Inspection item | Result |
|---|---|
| Column count | 8 |
| Columns | Serial; compound project identity; State; Approval/Start; Original/Revised DoC; Original/Revised Cost; Cumulative Expenditure; Physical Progress |
| Repeated headers | One on every data page: 108 |
| Section headings | 48 |
| Total rows | 31 |
| Cross-page project rows | None observed; each accepted row carries its own serial |
| Header/footer contamination | Outside extracted table cells |
| Final page | 11 project rows, one repeated header, one total, then report notes |
| Missing tokens observed | `-`, `NA` |

All 2,168 extracted table rows reconcile to 1,981 project rows plus 187 structural rows. No numeric row was unresolved.

## Schema and adapter decision

- Classification: `PAIMANA_V2`
- Confidence: `HIGH`
- Evidence rule: `paimana_v2_dual_identity`
- Decision: `COMPATIBLE_VARIATION`
- Recommended adapter: April-specific orchestration reusing the verified May row parser.

The decision is based on the observed Table 6 structure, not the report year. April has the normal two-line DoC representation throughout; unlike May, it has no single-cell `(-)` DoC variation. Its report count and page boundaries are April-specific. The June extractor remains unchanged.
