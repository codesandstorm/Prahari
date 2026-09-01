# Extraction Review — [Source ID] — [YYYY-MM]

**Owner:** [Reviewer name]
**Area:** Extraction
**Document Type:** AUDIT
**Status:** COMPLETE / IN PROGRESS
**Last Updated:** YYYY-MM-DD

---

## Source

| Field | Value |
|---|---|
| Source ID | SRC-YYYY-MM |
| File | FlashReport_YYYY_MM.pdf |
| SHA-256 | [hash] |
| Reporting month | YYYY-MM |
| Table | Table N — [Table name] |

## Schema

Detected schema: [PAIMANA_V2 / PAIMANA_V1 / OCMS / LEGACY]  
Confidence: HIGH / MEDIUM / LOW  
Manual assessment: [if different from detected]

## Table Boundaries

| Content | Physical PDF page | Printed page |
|---|---|---|
| Table title | [N] | [N] |
| First data page | [N] | [N] |
| Final data page | [N] | [N] |

## Expected vs Extracted Count

| Source | Count |
|---|---|
| Official report row count (from PDF) | [N] |
| Extracted row count | [N] |
| Difference | [N] |
| Reconciliation | [Explanation] |

## Manual Audit

| Check | Rows Sampled | Issues Found | Status |
|---|---|---|---|
| Serial number continuity | [N] | [N] | PASS / FAIL |
| Project name parsing | [N] | [N] | PASS / FAIL |
| Date parsing | [N] | [N] | PASS / FAIL |
| Cost parsing | [N] | [N] | PASS / FAIL |
| Provenance | [N] | [N] | PASS / FAIL |

Manual review CSV: `validation/extraction_validation/[filename]_manual_sample.csv`

## Provenance

Every extracted row includes:
- [ ] source_id (bound to source_manifest.csv)
- [ ] source_sha256
- [ ] pdf_page_index (physical)
- [ ] printed_page_number
- [ ] source_table
- [ ] extraction_method
- [ ] extractor_version
- [ ] raw_row_locator

## Known Limitations

*What edge cases, structural anomalies, or missing fields exist in this extraction?*

## Final Status

**VERIFIED** — extraction meets provenance and accuracy requirements.
/ **QUALIFIED** — extraction complete with noted limitations.
/ **REJECTED** — [reason].
