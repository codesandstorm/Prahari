# PAIMANA V2 June 2026 Table 6 Extraction Specification

## Verified source

- Source ID: `SRC-2026-06`
- File: `FlashReport_2026_06.pdf` (descriptive only)
- Reporting month: `2026-06`
- SHA-256: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- Automated schema: `PAIMANA_V2`, confidence `HIGH`
- Table: `Table 6 — All Ongoing Projects`

The source is resolved through `source_manifest.csv` and its SHA is checked
before and after extraction. The July-named duplicate is not eligible.

## Table boundaries

Physical PDF pages and printed report labels are separate fields:

| Content | Physical PDF page index | Printed page label |
|---|---:|---:|
| Table 6 title | 58 | 57 |
| First data page | 59 | 58 |
| Representative middle page | 109 | 108 |
| Final data page | 159 | 158 |
| Following notes section | 160 | 159 |

Physical pages 59–159 contain the data table. Physical page 160 contains a
note about unpublished projects and is not part of the table.

## Exact visible columns

Each data page exposes one table with eight cells per row:

1. `Sl.No`
2. `Project Name (Agency) (Project Code) (Legacy OCMS Code) (PMGID)`
3. `State`
4. `Date of Approval (Start Date) MM/YYYY`
5. `Orignal/Target DoC (Revised DoC) MM/YYYY`
6. `Orignal Cost Revised Cost in Rs. Crore`
7. `Cumulative Expenditure in Rs. Crore`
8. `Physical Progress (%)`

Spelling such as `Orignal` is reproduced from the source header and is not
silently corrected in raw source-cell metadata.

## Row and page behavior

- The eight-column header repeats on every data page and is rejected.
- Project rows are identified conservatively by a decimal serial number in
  column 1 and exactly eight table cells.
- Serial numbers naturally cover 1–1847 exactly once.
- Project names and agencies frequently wrap across visual lines but remain in
  one table cell; no cross-page project row was observed.
- The compound identity cell is parsed from the bottom: the final line contains
  `(Legacy OCMS Code) (PMGID)`, the preceding line contains `(Project Code)`,
  the preceding parenthesized line is the agency, and earlier lines are the
  project name. All 1847 rows satisfy this structure.
- Agency text may itself contain nested parentheses (for example an acronym);
  the parser removes only the verified outer agency parentheses.
- Legacy OCMS Code and PMGID columns exist, but their values are `-` for all
  rows in this report. They remain explicit raw missing markers.
- Approval/start, target/revised DoC, and original/revised cost each occupy one
  cell with exactly two lines. Parentheses indicate the second value.
- State may wrap to multiple lines and is preserved as source cell text.
- Blank structural rows, repeated headers, ministry/sector headings, and
  `Total (N)` rows are rejected as non-project rows.
- Ministry and sector are section headings, not project-row columns. They are
  intentionally not assigned to observations because doing so would require
  interpretive carry-forward logic not needed for this loss-minimized extract.
- Physical page 160 is a note/footnote section and is excluded.

## Missing-value conventions and ambiguities

- `-` inside parentheses is a source-reported missing marker and is preserved.
- Business fields are not required to be non-missing.
- No numeric, date, cost, state, agency, or identity normalization is performed.
- Whitespace at cell boundaries is trimmed; embedded line breaks are retained
  in raw source-cell fields.
- Any row that has a numeric serial but fails the verified eight-cell or
  compound-cell structure is written to the unresolved review output rather
  than guessed.

## Extraction method and fields

Method: `pdfplumber_table`, using `page.extract_tables()` on physical pages
59–159.

Verified extracted fields:

- serial number
- project name, agency, Project Code, Legacy OCMS Code, PMGID
- state
- approval date and start date
- original/target DoC and revised DoC
- original and revised cost
- cumulative expenditure
- physical progress
- original compound source cells for loss minimization
- mandatory source provenance, physical page, printed page, and row locator

Fields intentionally not interpreted: ministry, sector, normalized dates,
normalized costs, normalized progress, cross-month identity, labels, features,
and risk values.
