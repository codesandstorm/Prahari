# GATE 2 — Dataset Status

**Document Purpose:** Living status tracker for Gate 2 milestones.  
**Last Updated:** [YYYY-MM-DD] [Author]  
**Status Classification System:** VERIFIED | PLAUSIBLE | UNKNOWN | REJECTED

---

## Milestone Status

| # | Milestone | Status | Evidence | Notes |
|---|---|---|---|---|
| 1 | July 2026 ongoing table extracted | UNKNOWN | — | Not yet attempted |
| 2 | Row count reconciled (~1,775) | UNKNOWN | — | Pending extraction |
| 3 | Source page recorded per row | UNKNOWN | — | Pending extraction |
| 4 | 20–30 sample rows manually verified | UNKNOWN | — | Pending extraction |
| 5 | June 2026 extracted | UNKNOWN | — | Pending |
| 6 | May 2026 extracted | UNKNOWN | — | Pending |
| 7 | Project IDs linked across three months | UNKNOWN | — | Pending |
| 8 | Missingness quantified | UNKNOWN | — | Pending |
| 9 | Identifier coverage measured | UNKNOWN | — | Pending |
| 10 | `project_month.csv` created (3 months) | UNKNOWN | — | Pending |
| 11 | `project_master.csv` created | UNKNOWN | — | Pending |
| 12 | Full provenance preserved | UNKNOWN | — | Pending |

---

## Source Inventory

| File | Year | Month | Schema (Detected) | Extraction Status | Notes |
|---|---|---|---|---|---|
| mospy_flash_2026_07.pdf | 2026 | July | UNKNOWN | NOT STARTED | Primary target |
| mospy_flash_2026_06.pdf | 2026 | June | UNKNOWN | NOT STARTED | — |
| mospy_flash_2026_05.pdf | 2026 | May | UNKNOWN | NOT STARTED | — |
| mospy_flash_2025_07.pdf | 2025 | July | UNKNOWN | NOT STARTED | — |
| mospy_flash_2025_06.pdf | 2025 | June | UNKNOWN | NOT STARTED | — |
| mospy_flash_2025_05.pdf | 2025 | May | UNKNOWN | NOT STARTED | — |
| mospy_flash_2024_07.pdf | 2024 | July | UNKNOWN | NOT STARTED | — |
| mospy_flash_2024_06.pdf | 2024 | June | UNKNOWN | NOT STARTED | — |
| mospy_flash_2024_05.pdf | 2024 | May | UNKNOWN | NOT STARTED | — |
| mospy_flash_2023_07.pdf | 2023 | July | UNKNOWN | NOT STARTED | Schema reference only |
| mospy_flash_2020_07.pdf | 2020 | July | UNKNOWN | NOT STARTED | Schema reference only |
| mospy_flash_2015_06.pdf | 2015 | June | UNKNOWN | NOT STARTED | Schema reference only |
| mospy_flash_2005_06.pdf | 2005 | June | UNKNOWN | NOT STARTED | Schema reference only |

> **Note:** Filenames above are the intended naming convention. Actual filenames should match when placed in `data/raw/<year>/`.

---

## Blocking Issues

*None recorded yet. Update this section as issues arise.*

---

## Decision Log Reference

See `docs/DECISION_LOG.md` for all technical decisions made during Gate 2.

---

## Gate 2 → Gate 3 Transition Criteria

Gate 3 (feature engineering and model design) MUST NOT start until all 12 milestones above are `VERIFIED`.

Gate 3 is NOT approved by the existence of a CSV file alone.  
Gate 3 is approved when extraction accuracy has been independently confirmed via manual sample validation.
