# SCHEMA AUDIT REPORT — PRAHARI Gate 2

**Generated:** 2026-09-01  
**Tool:** `scripts/audit_all_pdfs.py` + manual deep inspection  
**Auditor:** PRAHARI automated pipeline + manual review  
**Classification:** VERIFIED findings only — based on actual PDF content

---

## 1. Source Inventory — All Files Found in `data/raw/`

| # | Filename | Year | Month | Pages | Size (KB) | SHA-256 (first 16) |
|---|---|---|---|---|---|---|
| 1 | `FlashReport_2005_06.pdf` | 2005 | June | 25 | 434 | `99af6f51d444c4f5` |
| 2 | `FlashReport_2015_06.pdf` | 2015 | June | 301 | 4,181 | `0c4e78b5d974e0bc` |
| 3 | `FlashReport_2020_07.pdf` | 2020 | July | 609 | 66,494 | `fea04b6659906ba2` |
| 4 | `FlashReport_2023_07.pdf` | 2023 | July | 640 | 9,964 | `8594dbcc2dfaeb53` |
| 5 | `FlashReport_2024_05(01).pdf` | 2024 | May | 5 | 592 | `3db1c6f6b822b9dc` |
| 6 | `FlashReport_2024_06.pdf` | 2024 | June | 309 | 1,070 | `7823bd3479b62d31` |
| 7 | `FlashReport_2024_07(02).pdf` | 2024 | July | 267 | 1,018 | `20eba591ed463174` |
| 8 | `FlashReport_2025_05.pdf` | 2025 | May | 212 | 9,761 | `1326fc47d272e8f2` |
| 9 | `FlashReport_2025_06.pdf` | 2025 | June | 234 | 13,674 | `7f37c63abe9f92d8` |
| 10 | `FlashReport_July_2025 (1).pdf` | 2025 | July | 67 | 5,686 | `1064c963c8afacf9` |
| 11 | `FlashReport_2026_05.pdf` | 2026 | May | 163 | 3,142 | `480d98632cd1b1d4` |
| 12 | `FlashReport_2026_06.pdf` | 2026 | June | 161 | 6,386 | `d26872ac9336b451` |
| 13 | `FlashReport_2026_07.pdf` | 2026 | July(?) | 161 | 6,386 | `d26872ac9336b451` |

**Total files found:** 13  
**Files in manifest (original):** 13  
**Manifest rows with no matching file:** 0  
**Files not in manifest (unexpected):** 0

---

## 2. File Integrity Status

| Filename | Opens OK | Text Extractable | OCR Required | Errors |
|---|---|---|---|---|
| FlashReport_2005_06.pdf | YES | YES | NO | None |
| FlashReport_2015_06.pdf | YES | YES | NO | None |
| FlashReport_2020_07.pdf | YES | YES | NO | None |
| FlashReport_2023_07.pdf | YES | YES | NO | None |
| FlashReport_2024_05(01).pdf | YES | YES | NO | None |
| FlashReport_2024_06.pdf | YES | YES | NO | None |
| FlashReport_2024_07(02).pdf | YES | YES | NO | None |
| FlashReport_2025_05.pdf | YES | YES | NO | None |
| FlashReport_2025_06.pdf | YES | YES | NO | None |
| FlashReport_July_2025 (1).pdf | YES | YES | NO | None |
| FlashReport_2026_05.pdf | YES | YES | NO | None |
| FlashReport_2026_06.pdf | YES | YES | NO | None |
| FlashReport_2026_07.pdf | YES | YES | NO | None |

**Summary:** All 13 files open successfully, are digitally typeset (not scanned), and yield extractable text. **OCR is NOT required** for any currently held file.

---

## 3. Schema Classification Results

| Filename | Detected Schema | Confidence | Evidence Keywords | Evidence Pages |
|---|---|---|---|---|
| FlashReport_2005_06.pdf | `LEGACY` | HIGH | DOA, DOC | 3, 4 |
| FlashReport_2015_06.pdf | `OCMS` | MEDIUM | OCMS | 1, 5–20 |
| FlashReport_2020_07.pdf | `OCMS` | MEDIUM | OCMS | 8 |
| FlashReport_2023_07.pdf | `OCMS` | MEDIUM | OCMS | 8 |
| FlashReport_2024_05(01).pdf | `OCMS` | MEDIUM | OCMS | 4 |
| FlashReport_2024_06.pdf | `PAIMANA_V1` | HIGH | Project Code | 7–14 |
| FlashReport_2024_07(02).pdf | `PAIMANA_V1` | HIGH | Project Code | 7–20 |
| FlashReport_2025_05.pdf | `PAIMANA_V1` | HIGH | Project Code | 11–20 |
| FlashReport_2025_06.pdf | `PAIMANA_V1` | HIGH | Project Code | 11–20 |
| FlashReport_July_2025 (1).pdf | `PAIMANA_V2_CANDIDATE` | MEDIUM | PAIMANA portal URL | — |
| FlashReport_2026_05.pdf | `PAIMANA_V2_CANDIDATE` | MEDIUM | PAIMANA portal URL | — |
| FlashReport_2026_06.pdf | `PAIMANA_V2_CANDIDATE` | MEDIUM | PAIMANA portal URL | — |
| FlashReport_2026_07.pdf | `PAIMANA_V2_CANDIDATE` | MEDIUM | PAIMANA portal URL | — |

### Schema Era Summary

| Era | Schema Code | Files Confirmed |
|---|---|---|
| Pre-OCMS simplified | LEGACY | 1 (2005) |
| OCMS-era | OCMS | 4 (2015, 2020, 2023, 2024-May-excerpt) |
| Early PAIMANA with Project Code | PAIMANA_V1 | 4 (2024-Jun, 2024-Jul, 2025-May, 2025-Jun) |
| New PAIMANA web-generated | PAIMANA_V2_CANDIDATE | 4 (2025-Jul, 2026-May, 2026-Jun×2) |

---

## 4. ⚠️ CRITICAL ISSUES REQUIRING IMMEDIATE ACTION

### ISSUE-001 — DUPLICATE FILE: FlashReport_2026_07.pdf IS FlashReport_2026_06.pdf

> [!CAUTION]
> **SEVERITY: CRITICAL — BLOCKS MILESTONE**

**Evidence:**
- `FlashReport_2026_06.pdf` SHA-256: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- `FlashReport_2026_07.pdf` SHA-256: `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`
- **These are byte-for-byte identical files.**
- Page 1 content: `"488 JUNE 2026"`
- Page 4 content: `"Flash Report JUNE 2026"`
- Table of contents references: `"as of June 2026... latest by 24th July 2026"`
- Project count shown: **1,847 ongoing projects** (not 1,775 as in the brief)

**Conclusion:** Both files contain the June 2026 Flash Report. The July 2026 report has **NOT been obtained**.

**Required action:** Download the actual July 2026 Flash Report from the MoSPI/PAIMANA portal.

---

### ISSUE-002 — Non-Standard Filenames in 2024 and 2025

> [!WARNING]
> **SEVERITY: MEDIUM — Requires documentation**

Three files have non-standard names with suffixes:
- `FlashReport_2024_05(01).pdf` — only 5 pages (likely an excerpt, not a full report)
- `FlashReport_2024_07(02).pdf` — 267 pages (appears to be a full report)
- `FlashReport_July_2025 (1).pdf` — 67 pages (appears to be a partial/excerpt)

These suffixes suggest either:
- Multiple versions were downloaded
- These are excerpts from larger reports

**Required action:** Verify what the full reports look like and re-download if needed.

---

### ISSUE-003 — FlashReport_2024_05(01).pdf Is Likely Not a Full Report

> [!WARNING]

This file is only **5 pages**. All other 2024 reports are 267–309 pages. This is almost certainly a partial extract, not the full May 2024 Flash Report.

---

### ISSUE-004 — FlashReport_July_2025 (1).pdf Is Likely Not a Full Report

> [!WARNING]

This file is only **67 pages**. The corresponding month files for May 2025 (212 pages) and June 2025 (234 pages) are far larger. This may be an excerpted version of the July 2025 report.

---

## 5. Structural Differences Between Eras (VERIFIED)

### LEGACY Era (2005)
- 25 pages
- Uses abbreviations: DOA (Date of Approval), DOC (Date of Commissioning)
- Keywords DOA/DOC confirmed on pages 3–4
- No "Project Code", "PMGID", or modern field structure
- Very compact report

### OCMS Era (2015, 2020, 2023)
- 301–640 pages (very large)
- Keyword "OCMS" present (in report header/footer text)
- Includes Completed Projects sections (pages 26–45 depending on report)
- No modern Project Code column in the form it appears in PAIMANA era
- 2020 report is 68 MB — schema reference only, will be slow to process

### PAIMANA V1 Era (Jun 2024, Jul 2024, May 2025, Jun 2025)
- 212–309 pages
- Keyword "Project Code" explicitly present as a column header
- Confirmed on pages 7–20 of these reports
- Table structure: Project Code appears as a dedicated column
- Uses `{Anticipated}` brace notation for revised values in some tables

### PAIMANA V2 Candidate Era (Jul 2025 excerpt, 2026)
- **NEW STRUCTURE DISCOVERED IN AUDIT — NOT PREVIOUSLY KNOWN**
- 67–163 pages (web-generated reports are more compact)
- No "Project Code" as a standalone column header visible in keyword scan
- Project Code appears **embedded inline** within row text in parentheses: `(Project Name) (Agency) (Project Code)`
- Contains "Table 6: All Ongoing Projects" explicitly
- Web-generated from PAIMANA portal (`paimana-proj.mospi.gov.in` or `ipm.mospi.gov.in`)
- Project count dramatically different from prior era (1,847 vs potentially fewer in PAIMANA V1)
- Column structure (from page 46 of `FlashReport_2026_07.pdf`):
  - `Sl.No`
  - `Project Name (Agency) (Project Code)`
  - `State`
  - `Date of Approval (Start Date)`
  - `Original/Target DoC (Revised DoC)`
  - `Original Cost`
  - `Revised Cost`
  - `Cumulative Expenditure`
  - `Physical Progress (%)`

> [!IMPORTANT]
> The PAIMANA_V2 schema defined in the original project brief (with explicit "Legacy OCMS Code" and "PMGID" columns) has **NOT been observed in any currently held PDF**. The actual 2026 structure embeds identifiers differently. Do not assume the original PAIMANA_V2 definition is correct until a PDF containing "Legacy OCMS Code" as a column is actually found.

---

## 6. Table Location Reference (VERIFIED)

| File | Table Label | Start Page | Completed Projects Pages |
|---|---|---|---|
| FlashReport_2026_07.pdf (= June 2026) | Table 6: All Ongoing Projects | 58 | 35–42 |
| FlashReport_2026_06.pdf (= June 2026) | Table 6: All Ongoing Projects | 58 | 35–42 |
| FlashReport_2026_05.pdf (May 2026) | Table 6: All Ongoing Projects | 53 | UNKNOWN |
| FlashReport_July_2025 (1).pdf | Table 4: All Ongoing Projects | ~33 (NE region shown) | UNKNOWN |
| FlashReport_2015_06.pdf | Completed Projects (section) | 44–45 | 44–45 |
| FlashReport_2020_07.pdf | Completed Projects (section) | 26–28, 40 | 26–28, 40 |
| FlashReport_2023_07.pdf | Completed Projects (section) | 25–30 | 25–30 |

---

## 7. Files Requiring Special Handling

| File | Issue | Recommended Action |
|---|---|---|
| `FlashReport_2026_07.pdf` | Identical to _06; contains June 2026 data | Do NOT use as July 2026. Download real July 2026 report. |
| `FlashReport_2020_07.pdf` | 68 MB, 609 pages | Limit page scanning; use only for schema reference |
| `FlashReport_2023_07.pdf` | 640 pages | Similarly limit scanning |
| `FlashReport_2024_05(01).pdf` | Only 5 pages | Treat as excerpt only; obtain full May 2024 report |
| `FlashReport_July_2025 (1).pdf` | Only 67 pages; non-standard name | Likely excerpt; obtain full July 2025 report |
| `FlashReport_2024_07(02).pdf` | Non-standard suffix | Verify this is the correct full July 2024 report |

---

## 8. OCR Assessment

**All currently held files are digitally typeset PDFs with extractable text. OCR is NOT required.**

This may change if:
- Very old reports (pre-2005) are obtained
- Scanned legacy documents are needed

---

## 9. Filename/Report Month Inconsistencies

| Issue | Details |
|---|---|
| `FlashReport_2026_07.pdf` claims to be July 2026 | **REJECTED** — content is June 2026 (VERIFIED by SHA-256 and page text) |
| `FlashReport_2026_06.pdf` and `_07.pdf` are byte-identical | **VERIFIED** — same SHA-256 |
| `FlashReport_July_2025 (1).pdf` uses month name not number | Non-standard — assume July 2025 |
| Files with `(01)` and `(02)` suffixes | Unknown meaning — possible version numbers or download artifacts |

---

## 10. Unresolved Assumptions

| # | Assumption | Status |
|---|---|---|
| 1 | "Legacy OCMS Code" appears as explicit column in 2026 reports | NOT CONFIRMED — not observed in any held PDF |
| 2 | "PMGID" appears as explicit column in 2026 reports | NOT CONFIRMED — not observed in any held PDF |
| 3 | Project count for July 2026 ≈ 1,775 (from project brief) | REVISED — June 2026 shows 1,847 ongoing; July 2026 not obtained |
| 4 | Physical progress field present in all eras | VERIFIED for 2026; UNKNOWN for OCMS/LEGACY era |
| 5 | July 2026 Flash Report exists and is downloadable | UNVERIFIED — file not yet obtained |
| 6 | PAIMANA_V2_CANDIDATE structure confirmed for "All Ongoing Projects" table | PARTIALLY VERIFIED — column structure seen, inline Project Code confirmed |

---

## 11. Recommended First Extraction Target

**Recommendation: `FlashReport_2026_07.pdf` (which contains June 2026 data)**

Rationale:
- Largest of the 2026 files in terms of page density
- "All Ongoing Projects" table confirmed on pages 58–60+
- Project count verified as 1,847 from page 4 text
- Completed Projects table confirmed on pages 35–42
- Identical to `FlashReport_2026_06.pdf` — either can be used; use `_07` to match original intent

**Alongside this:** Obtain the actual July 2026 report before claiming the July 2026 milestone.

---

## 12. Discovered PAIMANA V2 Candidate Column Structure

Confirmed from page 46 of `FlashReport_2026_07.pdf` (NE Region section — same layout as Table 6):

```
Sl.No | Project Name (Agency) (Project Code) | State | Date of Approval (Start Date) |
Original/Target DoC (Revised DoC) | Original Cost | Revised Cost |
Cumulative Expenditure | Physical Progress (%)
```

All units: Rs. Crore (Revised Cost, Cumulative Expenditure)  
Date format: MM/YYYY  

**Note:** Project Code, Agency, and Project Name are encoded in a single multi-line cell, not separate columns. This requires careful parsing logic.

---

*Report generated by PRAHARI Gate 2 audit pipeline — 2026-09-01*
