# PRAHARI Terminology and Conventions

**Owner:** Sandarbh
**Area:** Shared / Reference
**Document Type:** REFERENCE
**Status:** ACTIVE
**Last Updated:** 2026-09-01
**Depends On:** DATA_CONTRACT.md
**Used By:** Entire team, Codex/Antigravity agents
**Canonical:** YES

---

## Project / System Terminology

| Term | Definition |
|---|---|
| PRAHARI | Predictive Risk Assessment for HIgh-value Infrastructure. The PRAHARI system, not PAIMANA. |
| PAIMANA | Project Assessment, Infrastructure Monitoring and Analytics for Nation-building. MoSPI's infrastructure project monitoring platform. PRAHARI sits on top of PAIMANA. |
| OCMS | Online Computer Monitoring System — predecessor to PAIMANA. |
| Flash Report | Monthly official MoSPI PDF publication summarising ongoing and completed infrastructure project status. |
| CUF | Common Upload Form — the data submission mechanism used by implementing agencies to report to PAIMANA. |
| Gate | A defined checkpoint. Work beyond the gate requires the prior gate to be VERIFIED. |

---

## Data Terminology

| Term | Definition |
|---|---|
| Observation | One project's reported state at one reporting month. The fundamental unit. |
| Reporting month | The month a Flash Report covers, in YYYY-MM format. |
| Project Code | The modern PAIMANA project identifier, embedded in the compound identity cell. |
| Legacy OCMS Code | The historical OCMS identifier in modern reports, used for cross-era bridging. |
| PMGID | Another identifier field in modern reports. Population rate varies. |
| project_master | The table of unique infrastructure projects (one row per project). |
| project_month | The table of monthly project observations (one row per project per month). |
| project_completion_events | The table of completed-project outcome records. |
| Provenance | The traceability chain from dataset row → source PDF → page → table. |
| Source manifest | `data/metadata/source_manifest.csv` — registry of all source PDFs. |

---

## Evidence Classification

Every empirical claim in PRAHARI documentation must carry one of:

| Label | Meaning |
|---|---|
| `VERIFIED` | Directly demonstrated by source, data, or code. Reproducible. |
| `PLAUSIBLE` | Reasonable hypothesis. Not yet demonstrated. |
| `UNKNOWN` | Insufficient evidence. Not assumed either way. |
| `REJECTED` | Tested and found invalid. Evidence contradicts assumption. |

**Do not promote PLAUSIBLE to VERIFIED without evidence.**  
**Do not use UNKNOWN as an excuse to delay a decision indefinitely.**

---

## Document Status Values

| Status | Meaning |
|---|---|
| RESEARCH IN PROGRESS | Active research; conclusions not yet reviewed |
| REVIEW REQUIRED | Research complete; needs team review |
| APPROVED | Team has accepted this as the current position |
| APPROVED WITH LIMITATIONS | Accepted with stated caveats |
| BLOCKED | Cannot progress without external input |
| SUPERSEDED | Replaced by a newer document. Links to replacement. |
| NOT STARTED | Document created as a placeholder; no research yet |

---

## Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Source PDF files | `FlashReport_YYYY_MM.pdf` | `FlashReport_2026_06.pdf` |
| Multi-part PDFs | `FlashReport_YYYY_MM_partNN.pdf` | `FlashReport_2024_07_part02.pdf` |
| Extracted CSV | `ongoing_YYYY_MM.csv` | `ongoing_2026_06.csv` |
| Reporting month | `YYYY-MM` | `2026-06` |
| Dates in data | ISO 8601 (`YYYY-MM-DD`) | `2026-06-01` |
| Monetary values | ₹ crore (float) | `1234.56` |
| Decision ID | `DEC-NNN` | `DEC-016` |
| Open question ID | `OQ-NNN` | `OQ-005` |
| Source ID | `SRC-YYYY-MM` | `SRC-2026-06` |

---

## File Path Conventions

| Path | Contents |
|---|---|
| `data/raw/<year>/` | Source PDFs (NOT committed to Git) |
| `data/extracted/ongoing/` | Raw extractions, ongoing project tables |
| `data/extracted/completed/` | Raw extractions, completed project tables |
| `data/normalized/` | Normalized copies of extractions |
| `data/processed/` | Final analytical tables |
| `data/metadata/` | Source manifest, data dictionary, provenance |
| `docs/shared/` | Canonical team-wide decisions |
| `docs/team/<name>/` | Individual research notes |
| `docs/extraction/` | Extraction specifications |
| `docs/reference/` | Source and domain reference material |
| `docs/audits/` | Audit reports and findings |
| `docs/templates/` | Document templates |
