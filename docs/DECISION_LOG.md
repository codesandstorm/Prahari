# Decision Log

**Document Purpose:** Record all significant technical decisions made during Gate 2.  
**Format:** Append-only. Decisions are NEVER deleted; only superseded by new entries.

---

## Decision Template

```
## DEC-NNN — [Short Title]
Date: YYYY-MM-DD
Author: [name]
Context: What situation required a decision?
Options Considered: What alternatives were evaluated?
Decision: What was decided?
Rationale: Why was this option chosen?
Consequences: What does this imply going forward?
Status: ACTIVE | SUPERSEDED by DEC-NNN
```

---

## DEC-001 — Repository Structure Initialisation

**Date:** 2026-09-01  
**Author:** PRAHARI Setup  
**Context:** Gate 2 requires a clean, disciplined repository with separation of concerns.  
**Options Considered:**
- Single flat directory of scripts
- Modular `src/` layout with extraction, normalization, identity, validation, pipeline
**Decision:** Modular `src/` layout as specified in the SIH project brief.  
**Rationale:** Each phase (extraction → normalization → identity → validation) is
distinct enough to warrant its own module. Future contributors can work in isolation.  
**Consequences:** All scripts must use `config.yaml` for paths; no hard-coded absolute paths.  
**Status:** ACTIVE

---

## DEC-002 — PDF Extraction Library Choice

**Date:** 2026-09-01  
**Author:** PRAHARI Setup  
**Context:** Two candidate libraries exist for PDF table extraction.  
**Options Considered:**
- `pdfplumber` — good for structured tables, explicit table detection
- `PyMuPDF` — lower level, good for raw text blocks and page structure
- `camelot` — table-focused but requires Ghostscript dependency
- OCR (Tesseract) — for scanned/image PDFs
**Decision:** Use `pdfplumber` as primary; `PyMuPDF` as fallback and for metadata/integrity checks. No OCR unless normal extraction fails.  
**Rationale:** Flash Reports are digitally typeset PDFs (not scanned). Text extraction should work without OCR. `pdfplumber` has strong table detection. `PyMuPDF` is useful for SHA-256, page count, and cross-validation.  
**Consequences:** If any reports are scanned/image-based, this decision must be revisited.  
**Status:** ACTIVE

---

## DEC-003 — No Uncontrolled Fuzzy Matching

**Date:** 2026-09-01  
**Author:** PRAHARI Setup  
**Context:** Project identity across eras may require name matching as a fallback.  
**Options Considered:**
- Automatic fuzzy name matching (e.g., RapidFuzz, difflib)
- Supervised candidate matching with human review
**Decision:** Fuzzy matching may only be used to surface **candidates** for human review, never as automatic record linkage.  
**Rationale:** Automatic fuzzy matching can silently merge distinct projects or miss true matches. In government data, false merges are worse than unresolved identities.  
**Consequences:** Any unresolvable identity is marked `UNRESOLVED`, not silently assumed.  
**Status:** ACTIVE

---

## DEC-004 — Raw Extraction Files Are Immutable

**Date:** 2026-09-01  
**Author:** PRAHARI Setup  
**Context:** Normalization may alter values from raw extraction.  
**Options Considered:**
- Normalize in-place on extracted CSV
- Create separate normalized copies
**Decision:** Raw extracted CSVs in `data/extracted/` are NEVER overwritten. Normalization creates separate files in `data/normalized/`.  
**Rationale:** If normalization logic has a bug, we can always return to the raw extraction without re-running the PDF extractor.  
**Consequences:** Disk space doubles, but data integrity is guaranteed.  
**Status:** ACTIVE

---

## DEC-005 — No ML Until Gate 2 Is VERIFIED

**Date:** 2026-09-01  
**Author:** PRAHARI Setup  
**Context:** SIH teams may be tempted to start building models before data quality is confirmed.  
**Options Considered:**
- Begin feature engineering concurrently with extraction
- Strict gate: no ML until all 12 Gate 2 milestones are VERIFIED
**Decision:** Strict gate enforced. No ML libraries, no feature engineering, no risk scores until Gate 2 is complete.  
**Rationale:** A model trained on unvalidated data produces unvalidated results. In a government decision-support context, this is dangerous.  
**Consequences:** Slower time-to-demo, but higher confidence in eventual results.  
**Status:** ACTIVE

---

*Add new decisions below this line, incrementing DEC-NNN.*

---

## DEC-006 — Filename Convention Corrected to FlashReport_YYYY_MM.pdf

**Date:** 2026-09-01  
**Author:** PRAHARI Audit Pipeline  
**Context:** Session 1 assumed files would be named `mospy_flash_YYYY_MM.pdf`. Real files placed in `data/raw/` by the team use a different convention.  
**Options Considered:**
- Rename files to match the assumed convention
- Update the convention to match actual files
**Decision:** Update the documented convention. Do NOT rename source files. Actual convention: `FlashReport_YYYY_MM.pdf`.  
**Rationale:** Source files must not be modified. The naming convention in code and config is updated to match reality.  
**Consequences:** All scripts, config, and documentation now use `FlashReport_YYYY_MM.pdf`. Any code using the old convention must be corrected.  
**Status:** ACTIVE

---

## DEC-007 — FlashReport_2026_07.pdf Contains June 2026 Data — July 2026 Not Obtained

**Date:** 2026-09-01  
**Author:** PRAHARI Audit Pipeline  
**Context:** SHA-256 audit revealed `FlashReport_2026_07.pdf` and `FlashReport_2026_06.pdf` are byte-for-byte identical. Page-level text inspection confirmed both files state "JUNE 2026" on pages 1 and 4.  
**Options Considered:**
- Treat `_07` as July 2026 (REJECTED — contradicted by content)
- Mark both as June 2026, flag July 2026 as missing
- Delete one file
**Decision:** Both files are recorded in the manifest as June 2026 reports. The July 2026 report is recorded as NOT OBTAINED. The primary extraction milestone shifts to June 2026.  
**Rationale:** Content provenance rule: the file's internal content determines the report period, not its filename. Extraction on an incorrectly dated file would silently corrupt the temporal chain.  
**Consequences:** (a) July 2026 milestone requires obtaining the actual July 2026 PDF from MoSPI/PAIMANA portal. (b) The project brief's expected row count of 1,775 was for July 2026 — the June 2026 file shows 1,847. These are DIFFERENT months.  
**Status:** ACTIVE — action required

---

## DEC-008 — New Schema Era Defined: PAIMANA_V2_CANDIDATE

**Date:** 2026-09-01  
**Author:** PRAHARI Audit Pipeline  
**Context:** The original schema detection config defined PAIMANA_V2 with keywords "Legacy OCMS Code" and "PMGID". Neither keyword appears in any currently held PDF. The 2025-Jul, 2026-May, and 2026-Jun reports show a new structure: web-generated from the PAIMANA portal, Project Code embedded inline in rows.  
**Options Considered:**
- Force-classify 2026 reports as PAIMANA_V2 (REJECTED — unsupported by content)
- Classify as UNKNOWN (REJECTED — we know it is PAIMANA but the sub-version is unclear)
- Create an interim category PAIMANA_V2_CANDIDATE
**Decision:** New schema class `PAIMANA_V2_CANDIDATE` added to config. This represents the confirmed modern PAIMANA web-generated structure. The original PAIMANA_V2 definition remains but is marked PLAUSIBLE/NOT YET OBSERVED.  
**Rationale:** Accurate schema labelling is critical — the extractor code branches on schema version. Using an incorrect label would cause the wrong extractor to be invoked.  
**Consequences:** A new extractor for PAIMANA_V2_CANDIDATE must be written. The column structure is: Sl.No | Project Name (Agency) (Project Code) | State | Date of Approval | DoC | Original Cost | Revised Cost | Cumulative Expenditure | Physical Progress.  
**Status:** ACTIVE

---

## DEC-009 — Three Partial/Excerpt Files Flagged as Not Full Reports

**Date:** 2026-09-01  
**Author:** PRAHARI Audit Pipeline  
**Context:** Three files have anomalously low page counts compared to their era peers:  
- `FlashReport_2024_05(01).pdf`: 5 pages (peers: 267–309 pages)  
- `FlashReport_July_2025 (1).pdf`: 67 pages (peers: 212–234 pages)  
**Options Considered:**
- Proceed with extraction assuming they are representative samples
- Flag as excerpts and defer extraction pending full files
**Decision:** Both files flagged in manifest as LIKELY EXCERPT — NOT FULL REPORT. Extraction deferred. `FlashReport_2024_07(02).pdf` (267 pages) is accepted as a plausible full report despite the suffix.  
**Rationale:** Extracting a partial file and treating its row count as the complete monthly picture would introduce silent undercount bias.  
**Consequences:** May 2024 and July 2025 monthly data unavailable until full reports are obtained.  
**Status:** ACTIVE — action required

---

## DEC-010 — OCR Ruled Out for All Currently Held Files

**Date:** 2026-09-01  
**Author:** PRAHARI Audit Pipeline  
**Context:** Task 2 required assessing whether OCR was necessary for any held PDF.  
**Options Considered:** N/A — binary assessment
**Decision:** OCR is NOT required. All 13 files are digitally typeset and yield extractable text via pdfplumber.  
**Rationale:** Text character counts confirmed >200 chars/page across all sampled pages for all files. No zero-character pages observed.  
**Consequences:** Do NOT add Tesseract or OCR dependencies at this stage. Reassess only if pre-2005 files are obtained.  
**Status:** ACTIVE

---

## DEC-011 -- Multipart Source Naming Convention Adopted: FlashReport_YYYY_MM_partXX.pdf

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Three files had non-standard names with parenthetical suffixes: (01), (02), (1). The meaning was ambiguous.
**Decision:** Files renamed to FlashReport_YYYY_MM_partXX.pdf. source_manifest extended with source_group_id and source_part columns.
**Consequences:** FR-2024-05 has part01 only; FR-2024-07 has part02 only (part01 not yet obtained); FR-2025-07 has part01 only.
**Status:** ACTIVE

---

## DEC-012 -- REJECTED_DUPLICATE Status Added; FlashReport_2026_07.pdf Permanently Excluded

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Codex review required formal enforcement that the misfiled June 2026 file never generates a July observation.
**Decision:** file_status=REJECTED_DUPLICATE added to manifest. The audit script load_eligible_manifest_rows() hard-excludes REJECTED_DUPLICATE entries. A MISSING sentinel row added for July 2026.
**Consequences:** No extraction pipeline will ever process FlashReport_2026_07.pdf as a source.
**Status:** ACTIVE -- July 2026 PDF must be obtained separately.

---

## DEC-013 -- Schema Detector Refactored to all_of/any_of/min_hits Rules

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Single-keyword-match schema detection was identified as insufficient by Codex review.
**Decision:** schema_versions in config.yaml now uses a rules list with all_of, any_of, min_hits. DOC and DOA alone cannot establish LEGACY; both are required. OCMS requires at least one structural marker alongside the keyword.
**Consequences:** Schema detection is more conservative. Some files previously classified as OCMS (MEDIUM) may drop to UNKNOWN_SCHEMA if only the bare keyword appears. Must re-run audit.
**Status:** ACTIVE

---

## DEC-014 -- Three Error States Now Distinct: UNKNOWN_SCHEMA / INSPECTION_FAILED / DEPENDENCY_MISSING

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Codex review required distinguishing parser failure, dependency failure, and genuine unknown schema.
**Decision:** SchemaEvidence.detected_schema can be: a schema code, UNKNOWN_SCHEMA, INSPECTION_FAILED, or DEPENDENCY_MISSING. Each has different handling in downstream code.
**Status:** ACTIVE

---

## DEC-015 -- Raw-Path Write Guard Implemented

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Codex review required a programmatic guard preventing writes to data/raw/.
**Decision:** _assert_not_raw_path() implemented in pdf_inspector.py. All audit output writes call this guard before opening any output file. All PDFs in data/raw/ also set to read-only at OS level.
**Status:** ACTIVE

---

## DEC-016 -- PAIMANA_V2_CANDIDATE Is Not a Detector-Produced Schema

**Date:** 2026-09-01
**Author:** Codex Review Response
**Context:** Codex review required that manual human hypotheses not be silently merged into automated detector output.
**Decision:** The automated detector returns UNKNOWN_SCHEMA for 2026-era files. The human assessment (PAIMANA_V2_CANDIDATE, PLAUSIBLE) is stored in SchemaEvidence.manual_schema_assessment separately. These fields are never conflated.
**Status:** ACTIVE
