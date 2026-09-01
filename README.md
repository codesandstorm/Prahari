# PRAHARI

**Predictive Risk Assessment for HIgh-value Infrastructure**  
*Smart India Hackathon 2026 — Problem Statement SIH26103*  
*Ministry of Statistics and Programme Implementation (MoSPI)*  
*Infrastructure & Project Monitoring Division*

---

## Current Status: GATE 2 — Dataset Truth and Historical Dataset Reconstruction

> **Do not advance to ML, backend, frontend, or risk scoring.**  
> Gate 2 must be fully validated before any downstream work begins.

---

## What is PRAHARI?

PRAHARI is an explainable, confidence-aware predictive decision-intelligence layer intended to sit on top of PAIMANA (Project Assessment, Infrastructure Monitoring and Analytics for Nation-building), MoSPI's infrastructure project monitoring platform.

**PRAHARI is NOT:**
- A project-entry portal
- A replacement for PAIMANA
- An ML dashboard built before the data is understood

**PRAHARI WILL eventually become:**
- A system that can predict cost and schedule overruns before they formally materialise
- A risk-scoring and early-warning engine
- A benchmarking and prioritisation tool
- An evidence-grounded decision-intelligence layer

---

## The Core Research Principle

```
PROBLEM → EVIDENCE → DATA → VALIDATION → MODEL → PRODUCT
```

Not:

```
IDEA → RANDOM ML MODEL → DASHBOARD
```

Every technical capability must be supported by actual data.

---

## Gate 2 Objective

Gate 2 produces a trusted, longitudinal, provenance-preserved dataset from official MoSPI Flash Reports.

The fundamental data model is:

```
PROJECT × REPORTING MONTH
```

One row in `project_month.csv` = one observation of one project in one reporting month.  
One row in `project_master.csv` = one unique infrastructure project.  
One row in `project_completion_events.csv` = one completed-project outcome record.

### Gate 2 Milestone Checklist

- [ ] July 2026 ongoing table extracted
- [ ] Row count reconciled with official report (~1,775)
- [ ] Source page recorded for every row
- [ ] 20–30 sample rows manually verified
- [ ] June 2026 extracted using same schema adapter
- [ ] May 2026 extracted
- [ ] Same project IDs linked across three months
- [ ] Missingness quantified per field
- [ ] Identifier coverage measured (Project Code / Legacy OCMS / PMGID)
- [ ] `project_month.csv` created for three months
- [ ] `project_master.csv` created without uncontrolled duplication
- [ ] Full provenance preserved (row → PDF → page → table)

---

## Repository Structure

```
PRAHARI/
├── README.md
├── requirements.txt
├── .gitignore
├── config.yaml
│
├── docs/                          # Research documentation
│   ├── GATE2_DATASET_STATUS.md
│   ├── DATASET_README.md
│   ├── DATA_DICTIONARY_NOTES.md
│   ├── SCHEMA_EVOLUTION.md
│   ├── PROJECT_IDENTITY_ANALYSIS.md
│   ├── TEMPORAL_LEAKAGE_NOTES.md
│   ├── TEAM_LEAD_TECHNICAL_UNDERSTANDING.md
│   ├── CUF_RESEARCH_STATUS.md
│   └── DECISION_LOG.md
│
├── data/
│   ├── raw/                       # Source PDFs (NOT committed to Git)
│   │   ├── 2005/ … 2026/
│   ├── extracted/                 # Per-report raw CSV extractions
│   │   ├── ongoing/
│   │   ├── completed/
│   │   └── added/
│   ├── normalized/                # Normalized copies of extracted CSVs
│   ├── interim/                   # Intermediate join / merge artefacts
│   ├── processed/                 # Final analytical tables
│   │   ├── project_master.csv
│   │   ├── project_month.csv
│   │   └── project_completion_events.csv
│   ├── validation/                # Quality-assurance outputs
│   └── metadata/                  # Manifest, provenance, data dictionary
│
├── src/
│   ├── extraction/                # PDF → raw CSV
│   ├── normalization/             # Raw CSV → normalized CSV
│   ├── identity/                  # Cross-report project linking
│   ├── validation/                # Row validation & anomaly detection
│   └── pipeline/                  # End-to-end orchestration
│
├── notebooks/                     # Exploratory analysis
├── tests/                         # Unit test skeletons
└── outputs/                       # Reports and figures
```

---

## Data Sources

Official MoSPI monthly Flash Reports (PDF).

| Report | Year | Use |
|---|---|---|
| June 2005 | 2005 | Schema reference — LEGACY era |
| June 2015 | 2015 | Schema reference — OCMS era |
| July 2020 | 2020 | Schema reference — OCMS era |
| July 2023 | 2023 | Schema reference — OCMS / transition era |
| June 2024 | 2024 | Schema reference — PAIMANA V1/V2 transition |
| May–July 2024 | 2024 | Initial extraction test set |
| May–July 2025 | 2025 | Initial extraction test set |
| May–July 2026 | 2026 | **Primary extraction target** |

Raw PDFs are tracked in `data/metadata/source_manifest.csv` and are **not committed to Git**.

---

## Provenance Requirement

Every extracted project observation must be traceable to:

```
dataset row → source PDF → page number → original table / section
```

No data lineage = the observation is **not trusted**.

---

## Key Research Questions (Do Not Answer with Assumptions)

These questions motivate architecture but do **not** permit premature implementation:

- **RQ1** — Can cost/schedule overruns be predicted before formal revision?
- **RQ2** — How early can they be predicted?
- **RQ3** — Which CUF fields contribute most to prediction?
- **RQ4** — Do engineered temporal features add value?
- **RQ5** — Do external variables improve CUF-only prediction?
- **RQ6** — Does ML outperform conventional statistical baselines?
- **RQ7** — Can predictions be calibrated and interpretable for administrative use?

---

## Quick Start (Gate 2)

```bash
# 1. Clone repository
git clone <repo-url>
cd PRAHARI

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place source PDFs
#    Copy Flash Reports into data/raw/<year>/
#    File naming convention: mospy_flash_<YYYY>_<MM>.pdf

# 5. Inspect a report
python -m src.extraction.pdf_inspector --file data/raw/2026/mospy_flash_2026_07.pdf

# 6. Detect schema
python -m src.extraction.schema_detector --file data/raw/2026/mospy_flash_2026_07.pdf
```

---

## Contributing

All empirical claims must be classified as one of:

| Status | Meaning |
|---|---|
| `VERIFIED` | Directly demonstrated by source/data/code |
| `PLAUSIBLE` | Reasonable but not yet demonstrated |
| `UNKNOWN` | Insufficient evidence |
| `REJECTED` | Tested and found invalid |

Never promote `PLAUSIBLE` to `VERIFIED` without evidence.

---

*PRAHARI — SIH26103 — MoSPI Infrastructure & Project Monitoring Division*
