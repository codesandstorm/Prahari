# Research Evidence Guidelines

**Owner:** Sandarbh + Team
**Area:** Reference / Standards
**Document Type:** REFERENCE
**Status:** APPROVED
**Last Updated:** 2026-09-01
**Depends On:** NONE
**Used By:** Entire team, Codex/Antigravity agents
**Canonical:** YES

---

## Evidence Classification System

Every empirical claim in PRAHARI documentation must carry one of:

### VERIFIED
A finding is VERIFIED when:
- It is directly demonstrated by source material, extracted data, or running code
- The evidence is reproducible by another team member following the same steps
- The source is cited (PDF name + page, or CSV path + column)

Example: *"June 2026 has 1,847 ongoing project rows. VERIFIED — ongoing_2026_06.csv row count = 1847, source FlashReport_2026_06.pdf SHA d26872...."*

### PLAUSIBLE
A finding is PLAUSIBLE when:
- It is a reasonable hypothesis consistent with available evidence
- It has not yet been directly tested or confirmed
- It may become VERIFIED after specific empirical steps are taken

Example: *"Project Code appears to be stable month-to-month. PLAUSIBLE — based on observation that May and June codes overlap significantly, but 3-month linkage not yet done."*

### UNKNOWN
A finding is UNKNOWN when:
- There is insufficient evidence to make any judgment
- The information required has not been obtained

Example: *"Legacy OCMS Code population in July 2026 report. UNKNOWN — July PDF not obtained."*

### REJECTED
A finding is REJECTED when:
- It has been directly tested and found invalid
- Evidence explicitly contradicts the assumption

Example: *"FlashReport_2026_07.pdf contains July 2026 data. REJECTED — SHA-256 comparison and page text confirm it is byte-for-byte identical to the June 2026 report."*

---

## Strict Rules

### No Silent Assumptions

Do not state something as fact without classifying it.

**Wrong:**
> "The Project Code is stable across months."

**Right:**
> "The Project Code appears stable across months. PLAUSIBLE — confirmed for May/June overlap, pending July linkage."

---

### No Fabricated CUF Fields

Do not invent or assume which CUF fields exist. CUF documentation has not been
obtained. All CUF field claims are UNKNOWN until the actual CUF schema is reviewed.

---

### No Arbitrary Model or Score Claims

Do not state expected model performance, accuracy, AUC, or risk scores without:
- A trained model on validated data
- A held-out test set with appropriate temporal splitting
- Calibration evaluation

---

### No Causal Claims from SHAP

SHAP values quantify feature contribution to a model's prediction.
They do NOT establish that a feature causes an outcome.

**Wrong:**
> "High physical progress SHAP value proves that physical progress drives cost overruns."

**Right:**
> "High physical progress SHAP value indicates the model gives this feature high weight for this prediction. Causal interpretation requires additional research."

---

### No Historical Identity Mapping Without Evidence

Do not silently map old OCMS project IDs to modern Project Codes without:
- Verifying that Legacy OCMS Code is populated in the modern report
- Confirming the mapping is correct for a sample of records
- Logging the mapping method and uncertainty in PROJECT_IDENTITY_ANALYSIS.md

---

## Document Self-Audit Checklist

Before marking a research document as REVIEW REQUIRED, verify:

- [ ] Every empirical claim has an evidence label
- [ ] VERIFIED claims cite a specific source (file + row/page)
- [ ] PLAUSIBLE claims describe what would make them VERIFIED
- [ ] No UNKNOWN is treated as PLAUSIBLE in downstream logic
- [ ] No REJECTED assumption is used anywhere in code or decisions
- [ ] CUF fields are not fabricated
- [ ] Model performance is not stated without evidence
- [ ] SHAP / feature importance claims are not stated as causal
