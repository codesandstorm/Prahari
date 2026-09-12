# PRAHARI Post-Adjudication Activation Checklist

**Owner:** PRAHARI scientific release team
**Status:** BLOCKED PENDING ADJUDICATION
**Document type:** RUNBOOK

Complete in order, retaining evidence at every gate:

1. Validate human adjudication and reviewer agreement.
2. Freeze and hash the adjudication version.
3. Rebuild S1 and S2 without changing frozen definitions silently.
4. Rerun the fixed model comparison.
5. Rerun weak-regime analysis.
6. Rerun short-history analysis.
7. Rerun event-level lead-time analysis.
8. Refit and evaluate calibration using the governed split.
9. Select a model only if evidence supports selection.
10. Refreeze versioned model, feature, target and calibration artifacts.
11. Approve `ModelReleaseStatus=RELEASED` only through scientific sign-off.
12. Run batch inference without mutating canonical observations.
13. Persist versioned predictions transactionally and idempotently.
14. Smoke-test the prediction API and withheld/available invariants.
15. Smoke-test review-queue policy and zero unintended alerts.
16. Smoke-test assistant grounding and safety explanations.
17. Smoke-test dashboard states and provenance links.
