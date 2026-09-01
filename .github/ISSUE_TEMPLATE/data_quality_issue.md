---
name: Data Quality Issue
about: Report a data quality problem in extracted or processed data
title: '[DATA] '
labels: data-quality
assignees: ''
---

## Source

| Field | Value |
|---|---|
| Source ID | SRC-YYYY-MM |
| File | FlashReport_YYYY_MM.pdf |
| Reporting month | YYYY-MM |
| Source page | Page [N] (physical PDF page index) |
| Table | Table [N] — [Table name] |

## Field Affected

*Which field has the problem?*

## Observed Value

*What was extracted.*

## Expected / Source Value

*What the PDF actually shows (paste exact text from PDF).*

## Severity

- [ ] **CRITICAL** — affects row count or project identity
- [ ] **HIGH** — affects a key business field (cost, date, progress)
- [ ] **MEDIUM** — affects a secondary field
- [ ] **LOW** — cosmetic / whitespace / formatting

## Provenance

Row locator (raw_row_locator field): [value]
CSV file: [e.g., data/extracted/ongoing/ongoing_2026_06.csv]
Row number in CSV: [N]

## Reproduction Steps

```python
# How to find the problem row programmatically
```

## Proposed Fix

*How should the extractor or normalization handle this case?*

---

*If this indicates a systemic issue, add a DECISION_LOG entry (DEC-NNN).*
