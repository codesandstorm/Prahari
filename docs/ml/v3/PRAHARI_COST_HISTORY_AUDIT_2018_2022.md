# PRAHARI Cost History Audit: January 2018–June 2022

Status: **research source audit complete; three months quarantined**

The external MoSPI/IPMD raw archive was inspected without changing or copying any PDF. All 54 expected canonical filenames exist, open as PDFs, contain native extractable text, identify the expected reporting month internally, and have unique SHA-256 hashes. Historical download timestamps and source URLs are not available for every file, so provenance is `SOURCE_PROVENANCE_PARTIAL` even though byte identity, archive path, document identity, page count and row provenance are retained.

## Admission result

- 51 months: `ADMIT_COST_TARGET`
- March 2019: quarantined because the report states 1,405 projects but contains 1,406 distinct project rows and duplicates printed serial 1400.
- April 2022: quarantined because the report states 1,559 projects but its complete table lists only 1,557.
- June 2022: quarantined because the report exposes status-specific annexures rather than one proven complete, non-overlapping project universe.

The unusually short February 2019 PDF is admitted: it contains the complete relevant table and accounts for all 1,423 stated projects.

## Parser scope

Two evidenced OCMS layouts are supported: the older 10-column table and the 7-column compound table. Exact-shape repairs handle page splits, printed serial corruption and diagonal `FLASH REPORT` vector overlays. Original source cells and printed serials are retained where recovery occurs. There is no fuzzy project matching and no permissive fallback.

Authoritative details are in `outputs/ml/cost_prediction_v3/source_inventory.csv`, `source_admission_ledger.csv`, `row_accounting.csv`, and `parser_repairs.csv`.
