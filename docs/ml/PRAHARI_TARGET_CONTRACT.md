# PRAHARI Target Contract

**Version:** `S1-v0.1-provisional`

**Status:** PROVISIONAL — NOT FINAL SIH CLAIM

## Frozen target families

| ID | Cohort | Event | Current disposition |
|---|---|---|---|
| S1 | No approved schedule deterioration observed through t | first future approved completion date later than the original approved date | provisional 3-month hero research target |
| S2 | approved schedule already later than original at t | later approved completion date increases again | secondary; event sufficiency not yet validated |
| C1 | no approved upward cost revision through t | first future approved cost above original cost | secondary; semantics and human validation pending |
| C2 | approved cost already above original at t | later approved cost increases again | secondary; final-cost evidence unavailable |

An event is evaluated only in `t+1 ... t+H`. Values at or before t may establish eligibility; values after t may never enter features.

## S1 3-month eligibility

An anchor is eligible only when: the project has an exact resolved identity; original completion date parses; no prior observation contains a revised completion later than original; at least two observations exist through t with the last interval exactly one calendar month; every calendar month in the three-month outcome window is `PROJECT_LEVEL`; and the same project is observed in every outcome month.

Failure of any condition means censored or ineligible—not negative. Disappearance is never completion. Aggregate-only and missing months always censor a crossing horizon. Improvements and downward corrections do not count as deterioration but remain data-quality events.

## Negative definition

A negative requires complete project-level observation in all three future months and no approved schedule deterioration. Right-censored, gap-crossing, identity-ambiguous, or disappearing projects cannot be negatives.

## 6- and 12-month status

Six months remains a candidate after event adjudication. Twelve months is rejected for V1 because only five calendar anchors are fully observable and the usable cohort is too sensitive to era and survivor selection.

## Validation gate

The derived event counts are machine-observed changes in published fields, not yet adjudicated administrative approvals. Human review must distinguish genuine approval, correction, schema representation change, and extraction error before metrics become claimable.
