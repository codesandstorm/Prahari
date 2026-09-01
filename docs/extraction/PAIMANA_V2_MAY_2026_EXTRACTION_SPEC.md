# PAIMANA V2 May 2026 Table 6 extraction specification

## Source and scope

- Source ID: `SRC-2026-05`
- Filename: `FlashReport_2026_05.pdf`
- SHA-256: `480d98632cd1b1d4fe70b58a5a753924b2735b0135e7c8507c1ec05ff2ddf005`
- Reporting month: `2026-05`
- Automated schema: `PAIMANA_V2`, confidence `HIGH`
- Table: Table 6 — All Ongoing Projects
- Report count evidence: 1,987 ongoing projects on physical PDF page 4,
  printed page 3.

## Boundaries

| Content | Physical PDF page | Printed page |
|---|---:|---:|
| Table 6 title | 53 | 52 |
| First data page | 54 | 53 |
| Final data page | 162 | 161 |
| Page after table | 163 | 162 |

Page 163 contains no table and is excluded. Data-page discovery independently
returns the contiguous physical range 54–162.

## Exact eight-column structure

1. `Sl.No`
2. `Project Name (Agency) (Project Code) (Legacy OCMS Code) (PMGID)`
3. `State`
4. `Date of Approval (Start Date)`
5. `Original/Target DoC (Revised DoC)`
6. `Original Cost (Revised Cost)`
7. `Cumulative Expenditure`
8. `Physical Progress (%)`

The identity cell is parsed from the bottom: its last line holds Legacy OCMS
Code and PMGID, the preceding line holds Project Code, and the preceding line
holds the agency. All earlier nonblank lines belong to the project name.
Parentheses and square brackets inside project names or agencies are preserved.

## Verified variation and missing values

The source dash `-` is preserved. Legacy OCMS Code is source-missing for 817
rows and PMGID for 786 rows; populated values are retained without mapping.

For 1,976 rows the DoC cell has an unparenthesized target value followed by a
parenthesized revised value. Eleven rows (serials 446–451, 464, 467, 470–472)
contain only the parenthesized source value `(-)`. For these, the May adapter
records an empty `original_target_doc_raw`, records `-` as
`revised_doc_raw`, and retains the exact `doc_cell_raw` value `(-)`.

Approval/start and original/revised-cost cells use the normal two-line form in
all 1,987 rows. Wrapped names, agencies, and states remain within their
pdfplumber cells. Every project row has its own serial; no cross-page project
continuation was observed.

## Structural rows

- Repeated headers: 109
- Section headings: 48
- Totals: 31
- Blank or other continuation fragments: none in the extracted tables

Structural rows are rejected. A numeric row which cannot satisfy the verified
May structure is sent to the unresolved file with its complete raw cells and
provenance.

## Method and output

Method: `pdfplumber.extract_tables`, using the locked dependency environment.
The output is raw/loss-minimized and includes serial, identity fields, state,
dates, costs, expenditure, progress, complete raw compound cells, and mandatory
source provenance.

Ministry and sector headings are intentionally not carried into project rows.
No normalization, cross-month identity, linking, features, labels, outcomes, or
risk values are produced.

## Reuse decision

May is a **COMPATIBLE_VARIATION**. The frozen June implementation remains
unchanged. May has a separate adapter and reuses only evidence-backed structural
constants/classification; its single-line DoC behavior is May-specific.
