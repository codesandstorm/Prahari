# PRAHARI Feature Discovery V2

**Status:** PROVISIONAL — NOT FINAL SIH CLAIM

## Baseline reproduction

The frozen dataset SHA-256 remains `75cac968e7f62fffdb55b5fd7376ccbc402836a0ea139a87ddf93c4815e34c5d`. V1 reproduced exactly: Rule 0.278, Logistic A 0.526, Logistic B 0.378 and Histogram Gradient Boosting B 0.577 test PR-AUC.

## Scope

Forty-six new as-of-time derived features were implemented and tested across momentum, schedule feasibility, financial/physical alignment, cost revision history, change point, observability, maturity proxy, scale interactions and seasonality. No contractor, milestone, land, clearance, funding, manpower, weather or synthetic peer value was created.

## Controlled family results

| Variant | Tree test PR-AUC | Delta vs tree Base A | Finding |
|---|---:|---:|---|
| Tree Base A | 0.582 | — | reconstructed six-feature comparison |
| momentum | 0.557 | -0.025 | weak alone; small conditional contribution in full model |
| schedule feasibility | 0.526 | -0.056 | weak alone but important in combined remove-family test |
| financial/physical | 0.504 | -0.078 | harmful; removing it slightly improves all-feature result |
| cost revision | 0.604 | +0.022 | modest signal; semantics remain conditional |
| change point | 0.596 | +0.014 | largely redundant in combined model |
| maturity proxy | 0.636 | +0.054 | strongest isolated family |
| seasonality | 0.570 | -0.013 | inconsistent and high-alert; rejected |
| all derived | 0.735 | +0.153 | strongest exploratory discrimination; 52 features is excessive |
| compact V2 | 0.697 | +0.115 | preferred 14-feature research set |

Removing observability from the full model reduces test PR-AUC from 0.735 to 0.640, the largest remove-family loss. This could represent genuine history sufficiency or era/selection structure; it belongs partly to reliability and requires confirmation.

## Compact V2

Six frozen Model A features plus history span, remaining schedule, required future velocity, progress-versus-elapsed gap, low progress near deadline, consecutive stagnation, cumulative cost revision percentage and expenditure velocity.

Tree test results: PR-AUC 0.697, Brier 0.193 before calibration and 0.137 after validation-fit provisional Platt calibration, precision 0.757, recall 0.549 and 4.94 false alerts per 100 anchors. Logistic compact PR-AUC is 0.596. Compact V2 was reduced after exploratory inspection and therefore requires a genuinely later confirmation period; its test result is not an untouched confirmatory estimate.

## Interpretation

The clearest current evidence is a component view of schedule feasibility: work remaining, time remaining, pace required and recent/stagnant progress. This supports “apparently healthy but fragile” review, but cannot predict an unknowable sudden shock. No arbitrary resilience score is justified.

## Rolling-origin stability

Compact V2 is not temporally stable enough for a final claim. Tree PR-AUC is 0.830 in the sparse early-to-2025 fold, 0.237 for July--November 2025, and 0.703 for December 2025--March 2026. Event prevalence and schema availability also shift sharply; early OCMS lacks physical progress entirely. The apparent overall improvement therefore does **not** persist uniformly. This is a research finding and a deployment blocker, not a reason to tune against the weak fold.
