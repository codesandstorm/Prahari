# PRAHARI Provisional Model Evaluation

**Status:** PROVISIONAL — NOT FINAL SIH CLAIM

**Dataset:** 36-month calendar window; 30 project-level snapshots

**Target:** S1 first observed approved schedule deterioration within 3 months

**Target version:** `S1-v0.1-provisional`

## Eligibility and split

Strict eligibility produced 5,982 anchors: 1,741 train (423 machine-observed events), 1,872 validation (331), and 2,369 test (663). Complete future project observations are required; source gaps and disappearance are censored. These event counts require PDF-level human adjudication and may include reporting corrections or semantic changes.

## Future-test results

| Model | Features | PR-AUC | ROC-AUC | Brier | Precision | Recall | False alerts / 100 |
|---|---|---:|---:|---:|---:|---:|---:|
| Rule | transparent stagnation/plan rule | 0.278 | 0.496 | 0.526 | 0.277 | 0.544 | 39.81 |
| Logistic A | six current-state fields | 0.526 | 0.757 | 0.317 | 0.615 | 0.335 | 5.87 |
| Logistic B | A plus six temporal/quality fields | 0.378 | 0.677 | 0.319 | 0.405 | 0.259 | 10.68 |
| Histogram gradient boosting B | A plus temporal/quality | 0.577 | 0.710 | 0.201 | 0.686 | 0.383 | 4.90 |
| Histogram gradient boosting B + provisional Platt calibration | same ranking; validation-fit calibration | 0.577 | 0.710 | 0.175 | 0.686 | 0.383 | 4.90 |

Thresholds were selected on validation to approximate a 10% review capacity. They are not red/amber/green policy thresholds.

## Scientific interpretation

ML beats the current rule on provisional future-test discrimination and false-alert burden. Gradient boosting exceeds Logistic A PR-AUC by about 0.050, but Logistic A has stronger ROC-AUC and is substantially simpler. Temporal features do **not** consistently improve logistic regression: Logistic B is worse than A on future-test PR-AUC by 0.148. The tree model’s gain cannot be attributed solely to temporal data because no tree Model A was included in this frozen minimal experiment.

Train-to-future degradation is material. Validation-fit Platt scaling improves the provisional test Brier score from 0.201 to 0.175, but event adjudication and independent calibration evidence remain incomplete. No probability should be displayed. The responsible selection is therefore **no operational model yet**; Logistic A is the preferred interpretable baseline, while histogram gradient boosting B remains the provisional research candidate.

## Model C

Not evaluated. Milestones, land, clearances, contractor/package state, issue duration, project-level funding, and timestamped external events are unavailable. Reporting a Model C metric would be fabrication.

## Subgroups and lead time

Authoritative ministry and sector fields are not populated across the frozen modern period, so ministry/sector performance is not defensibly estimable. Lead time awaits event-date adjudication. No demo case was cherry-picked.

## Error analysis

False positives may reflect successful intervention, conservative rules, later correction, missing issue context, or model error. False negatives may reflect sudden shocks, contractor/funding/land/clearance information absent from Flash Reports, insufficient history, or schema drift. These hypotheses motivate the proposed CUF fields but are not causal findings.
