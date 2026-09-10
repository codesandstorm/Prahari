# PRAHARI Post-Adjudication Refreeze Plan

**Owner:** PRAHARI ML validation team  
**Status:** PENDING  
**Document type:** REFERENCE

After human review:

1. Validate and ingest completed adjudications without overwriting originals.
2. Freeze an adjudication dataset version and fingerprints.
3. Revise target rules only where reviewed evidence supports a general rule.
4. Rebuild S1 and S2 cohorts; censor unresolved evidence.
5. Rerun the same Rule, Logistic, HistGB, Random Forest and XGBoost configurations.
6. Rerun temporal folds.
7. Rerun event-level lead time.
8. Rerun validation-only calibration.
9. Rerun short-history analysis.
10. Rerun weak-regime analysis.
11. Select final models or withhold unsupported targets.
12. Refreeze all artifacts and fingerprints.
13. Integrate only approved artifacts through `PredictionProvider`.
14. Generate operational prototype predictions.

No new algorithm family is introduced during refreeze. Test outcomes must not be used for tuning, and unresolved review cases must not be forced into negative labels.
