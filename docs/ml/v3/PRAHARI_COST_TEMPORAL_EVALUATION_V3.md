# PRAHARI Cost Temporal Evaluation V3

V3 uses ten predeclared expanding-origin era folds from pre-COVID through recent PAIMANA reporting. Training outcomes must mature before validation/test; preprocessing, Platt calibration and thresholds are fit only on earlier data. A fold requires at least 1,000 anchors, 300 projects and 30 positive events, plus adequate training and inner-validation support. Failed folds are descriptive only.

C1 3-month Basic admits nine folds. The late-OCMS fold contains no eligible anchors because its outcome window crosses quarantined June 2022 and missing July 2022; this is correct censoring. Compact V2 admits only one fold and cannot support a superiority claim. C2 admits zero folds.

For C1 Basic, logistic regression has the highest mean PR-AUC (0.0415 versus 0.0296 for the rule) and low false-alert burden, but only 2.24% mean recall at validation-derived thresholds. No model satisfies the full admission policy. No lead-time, bootstrap-final-candidate or deployable serialization claim is therefore made.

Recent-history windows of 24, 36 and 48 months are evaluated separately. They are sensitivity analyses, not test-selected replacements for the full-history contract.
