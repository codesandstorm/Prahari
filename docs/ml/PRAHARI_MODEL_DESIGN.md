# PRAHARI Predictive Model Design

**Research question:** does point-in-time temporal behaviour improve prediction of first approved schedule deterioration beyond current-state CUF-equivalent fields?

## Comparison

1. Auditable rule: stagnation or low progress late in the original plan.
2. Statistical baseline: class-weighted regularized logistic regression.
3. ML candidate: shallow histogram gradient boosting.
4. Model A: six current-state features.
5. Model B: Model A plus six temporal/quality features.
6. Model C: data contract only; no additional data and therefore no fabricated score.

The split is chronological: training anchors through May 2025, validation June–November 2025, and test December 2025 onward. The exact realized anchor months are recorded in run metadata. Preprocessing is fit only on training. Seed is `26103`. The review threshold is fitted on validation to approximate a 10% review capacity, not an arbitrary probability of 0.5.

The selection order is target validity, leakage safety, event sufficiency, operational lead time, calibration, precision/recall, subgroup robustness, temporal stability, explainability, and simplicity. Current probabilities are not displayable because event adjudication and calibration validation are incomplete.

The experiment is intentionally diagnostic: observed performance degradation from train to future periods is evidence of schema/era instability. It is not a license to tune on the test period.
