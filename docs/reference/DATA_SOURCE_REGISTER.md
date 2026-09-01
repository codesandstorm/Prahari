# Data Source Register

**Owner:** Sandarbh
**Area:** Reference / Data Sources
**Document Type:** REFERENCE
**Status:** ACTIVE
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Data Engineering, Backend, ML
**Canonical:** YES

---

## Overview

This document registers all data sources used or considered for PRAHARI.
The machine-readable source manifest is: `data/metadata/source_manifest.csv`.

---

## Primary Sources (Official)

| Source | Description | Format | Status |
|---|---|---|---|
| MoSPI Flash Reports | Monthly PDF publications of ongoing and completed infrastructure project data | PDF | PRIMARY — active extraction |
| PAIMANA Portal | Web-based version of project data; source of Flash Reports | Web/PDF | REFERENCE only |
| PAIMANA CUF | Common Upload Form data — may contain richer fields than Flash Reports | Unknown | NOT OBTAINED |

### Flash Reports Held

See `data/metadata/source_manifest.csv` for complete manifest with SHA-256 hashes.

Key reports for Gate 2:
- `FlashReport_2026_06.pdf` — June 2026 — EXTRACTED AND VALIDATED
- `FlashReport_2026_05.pdf` — May 2026 — EXTRACTED
- `FlashReport_2026_07.pdf` — **REJECTED_DUPLICATE** (contains June 2026 data)
- July 2026 actual report — NOT YET OBTAINED

---

## Schema Reference Sources

| Source ID | File | Era | Purpose |
|---|---|---|---|
| SRC-REF-2005 | FlashReport_2005_06.pdf | LEGACY | Schema reference |
| SRC-REF-2015 | FlashReport_2015_06.pdf | OCMS | Schema reference |
| SRC-REF-2020 | FlashReport_2020_07.pdf | OCMS | Schema reference |
| SRC-REF-2023 | FlashReport_2023_07.pdf | OCMS/transition | Schema reference |
| SRC-REF-2024 | FlashReport_2024_06.pdf | PAIMANA V1 | Schema reference |

---

## Candidate External Sources (All PLAUSIBLE — not approved)

| Source | Variables | Relevance | Status |
|---|---|---|---|
| MoSPI / CMI | Steel/cement price indices | RQ5 — external variables | PLAUSIBLE |
| IMD | Extreme weather data | Construction delay proxy | PLAUSIBLE |
| MoEF | Environmental clearance records | Regulatory delay proxy | UNKNOWN |
| Flash Reports (historical) | Agency performance history | Agency-level features | PLAUSIBLE |

> [!WARNING]
> No external data source will be incorporated before Gate 2 is complete and
> CUF field availability is understood.

---

## Source Integrity Policy

- All source PDFs are stored in `data/raw/` and are NOT committed to Git.
- SHA-256 hashes are recorded in `data/metadata/source_manifest.csv`.
- Pre-extraction hashes are in `validation/source_audit/raw_hashes_pre_extraction.csv`.
- No extraction pipeline may write to `data/raw/`.
- Source files are set to read-only at the OS level.

See DEC-004 and DEC-015 in [`docs/shared/DECISION_LOG.md`](../shared/DECISION_LOG.md).
