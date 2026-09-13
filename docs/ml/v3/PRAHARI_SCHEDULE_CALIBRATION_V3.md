---
title: PRAHARI Schedule Calibration V3
status: CURRENT
---

# PRAHARI Schedule Calibration V3

Learned-model probabilities are calibrated with Platt scaling fitted only on temporally prior validation predictions. Raw and calibrated Brier values, ECE, slope and intercept are reported per fold. Calibration does not transform probability into system reliability or officer priority.

Two operating points are recorded separately: a past-validation F1 threshold and a 10% review-capacity threshold. Neither is a production alert policy. The test period never selects calibration or thresholds.
