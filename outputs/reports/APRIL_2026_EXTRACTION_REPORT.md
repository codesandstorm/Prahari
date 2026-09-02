# April 2026 Table 6 Extraction Report

## Assessment

**AUTOMATED VALIDATION COMPLETE — HUMAN VALIDATION PENDING**

The canonical April source (`SRC-2026-04`) is a 163-page, text-extractable PAIMANA report with SHA-256 `90a6959e976da6928440efdea9c68847d1178356e4c0ebd078c51026ddb118d5`.

## Boundaries and reconciliation

- Official expected count: 1,981, physical page 4 / printed page 3.
- Table 6 title: physical page 54 / printed page 53.
- Data pages: physical 55–162 / printed 54–161.
- Raw table rows: 2,168.
- Accepted projects: 1,981.
- Repeated headers / section headings / totals / other structural: 108 / 48 / 31 / 0.
- Unresolved: 0.
- Serials: complete natural sequence 1–1981; no duplicates or gaps.
- Project Codes: complete, decimal, whitespace-clean, and unique.
- Duplicate project provenance locators: 0.

## Field audits

- Legacy OCMS: 1,184 present, 797 missing, 1,124 unique, 60 duplicate occurrences beyond first; uniqueness is not assumed.
- PMGID: 1,213 present, 768 missing, 1,213 unique, 0 duplicate occurrences.
- Approval dates: 1,970 parsed, 11 source-missing, 0 malformed.
- Start dates and original DoC: 1,981 parsed, 0 missing/malformed.
- Revised DoC: 1,627 parsed, 354 source-missing, 0 malformed.
- Cost and expenditure fields: all 1,981 parseable; 0 missing, malformed, or negative values.
- Physical progress: all 1,981 parseable; range 0–100; 0 outside range.
- Observed missing tokens: `-`, `NA`; raw values remain preserved.

These are extraction diagnostics, not financial corrections or status/risk interpretations.

## Outputs and limits

- Extraction: `data/extracted/ongoing/ongoing_2026_04.csv`
- Provisional extraction SHA-256: `55d84996925b4d5d0f2bb3bc9367a685c2ad49a14c009acddc7662b0b9ee11dd`
- Unresolved artifact: `data/extracted/review/ongoing_2026_04_unresolved_rows.csv`
- Summary: `validation/extraction_validation/april_2026/april_2026_extraction_summary.json`
- Human sample: `validation/extraction_validation/april_2026/april_2026_manual_sample.csv`

The sample contains 30 deterministic rows covering early, middle, late, and final pages; first and last projects; populated and missing identifiers; missing revised DoC; zero and high progress. Manual columns are empty.

No April–May identity analysis or three-month longitudinal dataset has been created. April is not frozen until human validation passes.
