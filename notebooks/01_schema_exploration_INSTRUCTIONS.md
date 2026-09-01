# Notebook: 01 — Schema Exploration

**Purpose:** Manual exploration of Flash Report PDF structure across eras.

**Status:** NOT STARTED — requires PDFs in `data/raw/`.

## Instructions

1. Place at least one PDF from each target era into the appropriate `data/raw/<year>/` directory.
2. Run `pdf_inspector` on each PDF to get page count and text extractability.
3. Run `schema_detector` on each PDF to get initial schema classification.
4. In this notebook: examine raw text and table structure page by page.
5. Document the exact column headers found in each era.
6. Update `docs/SCHEMA_EVOLUTION.md` with verified findings.

## What to record

- First page with tabular project data
- Exact column headers (copy-paste from extracted text)
- Number of rows detected
- Whether project code / OCMS code / PMGID appear
- Any merged cells or multi-row headers that complicate extraction
- Any footnotes or caveats printed near the table

## Outputs

- Update to `docs/SCHEMA_EVOLUTION.md`
- Entry in `docs/DECISION_LOG.md` recording schema classification
- Update to `data/metadata/source_manifest.csv` (schema_version column)
