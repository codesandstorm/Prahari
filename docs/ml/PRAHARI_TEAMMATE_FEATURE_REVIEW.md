# Independent review of Pavitra's advanced feature proposals

## Decision

Keep Compact V2 unchanged. None of the proposals earns promotion to the core predictive set. Expenditure changepoints are the strongest *conditional research* idea: they raised the weakest rolling fold from **0.237 to 0.253** and reduced rolling variance from **0.0650 to 0.0613**, but lowered held-out test PR-AUC from **0.697 to 0.674**. That trade-off is not confirmation of generalization.

Recovery history is useful as an explicitly qualified resilience/reliability descriptor. It is not approved as a core risk feature: the weak fold moved down to 0.235 and false positives increased from 117 to 130.

All findings are provisional. The dataset has mixed monthly coverage, short histories, pending identity validation, no authoritative contractor identity, no fund-release history, and no clean completed-project outcome corpus.

## Reproduction and evaluation

The frozen 5,982-anchor S1 three-month cohort reproduced exactly: 1,741/423 train anchors/events, 1,872/331 validation, and 2,369/663 test. Compact V2 reproduced test PR-AUC 0.696766, Brier 0.192744, precision 0.756757, recall 0.549020, and 4.9388 false alerts per 100.

| Candidate | Test PR-AUC | Brier | Precision | Recall | False alerts/100 | Rolling PR-AUC R1/R2/R3 | Minimum | Variance |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| Compact V2 | 0.6968 | 0.1927 | 0.7568 | 0.5490 | 4.94 | 0.830 / 0.237 / 0.703 | 0.2369 | 0.0650 |
| + progress changepoint | 0.6765 | 0.1925 | 0.7490 | 0.5445 | 5.11 | 0.830 / 0.214 / 0.681 | 0.2140 | 0.0689 |
| + expenditure changepoint | 0.6737 | 0.1921 | 0.7500 | 0.5520 | 5.15 | 0.830 / 0.253 / 0.703 | **0.2529** | **0.0613** |
| + recovery | 0.6889 | 0.1904 | 0.7390 | 0.5551 | 5.49 | 0.830 / 0.235 / 0.712 | 0.2351 | 0.0662 |
| + peer velocity | 0.6877 | 0.1912 | 0.7470 | 0.5566 | 5.28 | 0.830 / 0.228 / 0.704 | 0.2282 | 0.0672 |
| + expenditure lag | 0.6914 | 0.1916 | 0.7515 | 0.5520 | 5.11 | 0.830 / 0.225 / 0.707 | 0.2246 | 0.0683 |
| + all testable | 0.6597 | 0.1933 | 0.7287 | 0.5023 | 5.23 | 0.830 / 0.251 / 0.690 | 0.2515 | 0.0607 |

The combined set has slightly lower variance, but materially worse final-period discrimination and recall. Stability-first selection therefore does not justify adopting a larger 30-feature model.

## Feature-by-feature audit

### Changepoints

The implementation is deterministic, past-only and calendar-gap aware. It finds the strongest velocity mean shift with at least two observed intervals on each side and rejects shifts smaller than observed noise or 0.5 units/month. Progress timing/direction are redundant with existing velocity, stagnation and momentum signals and worsen the weak fold. Expenditure changepoints improve that fold by 0.0161, but expenditure is not funding and the gain does not transfer to test PR-AUC. Verdict: progress features `REJECT_UNSTABLE/REDUNDANT`; expenditure family `ADOPT_NOW_CONDITIONAL`, backend research only.

### Bounce-back/recovery

Only slowdown windows completely resolved before the anchor are counted. A rate is unavailable until two resolved stalls exist. This avoids turning absent history into resilience. It corrected four more test false negatives than Compact V2 but created 13 more false positives. Verdict: `ADOPT_AS_RELIABILITY_FEATURE`, not core risk.

### Peers

The only tested group uses same-month, self-excluded projects in observable cost and progress bands, with at least ten peers. It uses no agency, sector or ministry assumption. It worsened the weak fold and alert burden. Verdict: `REJECT_UNSTABLE`. Contractor peer trend is `FUTURE_CUF`; raw agency cannot substitute for contractor. Agency peer trend is `REJECT_SEMANTICALLY_UNSAFE` until identity, role, validity dates and change reasons are normalized.

### Expenditure/funding lag

The tested descriptor relates prior monthly expenditure velocity to later progress already observed by the anchor, requiring four past pairs. It is an association, not a causal or funding signal. It worsened the weak fold. Verdict: expenditure lag `REJECT_UNSTABLE`; true fund-to-progress lag `FUTURE_CUF`.

### Archetypes

The corpus contains ongoing-project histories and cannot cleanly distinguish successful recovery, permanent stall, completion, termination or reporting exit. Clustering it into outcome-labelled archetypes would be survival-biased. Verdict: `FUTURE_AFTER_COMPLETION_DATA`, potentially explanatory before predictive use.

### Risk trend and multi-horizon output

Risk trend is conditionally displayable only from consecutive predictions produced by one frozen calibrated model with a predeclared deadband; arbitrary probability movement is not a trend. Five independent T+1…T+5 models are not justified. A future discrete-time hazard design is simpler and internally coherent, but only after censoring, calibration and identity gates pass.

## Horizon review

| Horizon | Train anchors/events | Validation anchors/events | Test anchors/events | Assessment |
|---|---:|---:|---:|---|
| 3 months | 1,741 / 423 | 1,872 / 331 | 2,369 / 663 | Best current balance of lead time and evaluable support |
| 5 months | 702 / 394 | 1,843 / 403 | 846 / 269 | Defensible as sensitivity research, not a replacement target |
| 6 months | 702 / 401 | 1,827 / 447 | 322 / 55 | Test support too thin and temporally unbalanced |

Longer horizons lose eligible anchors because every intervening project-level month must be observed. The large change in cohort sizes and event rates is censoring/era composition, not evidence that a longer target is better. Retain three-month S1 as V1. Do not implement multi-horizon risk now.

## Direct answers to the 30 review questions

1. Genuinely useful: expenditure changepoint as research context; recovery as reliability context.
2. Implementable now: past-only changepoints, resolved recovery history, same-month cost/maturity peer rank, expenditure-lag descriptors—though implementation does not imply retention.
3. Future CUF: contractor/package identity, agency role history, project fund releases.
4. Completion data: outcome archetypes and archetype warnings.
5. External data: none of these core proposals is safely available externally without project linkage; event-response extensions would require authoritative geocoded sources.
6. Rejected: progress changepoints, current peer velocity, expenditure lag, agency proxy and current multi-horizon product.
7. Changepoint timing did not help reliably.
8. Direction did not add stable value beyond existing momentum.
9. Bounce-back modestly helped test Brier/recall but not temporal stability.
10. Peer velocity did not help.
11. Expenditure-to-progress lag did not help.
12. Expenditure changepoints improved the 0.237 fold to 0.253; the combined set reached 0.251.
13. Best new candidate minimum: 0.252949.
14. Its variance: 0.061296 versus 0.065016 (decrease 0.003720).
15. No; candidate test PR-AUC fell by 0.023031.
16. Recovery produced the lowest test false-negative count (295 versus 299), but with more false positives.
17. No candidate produced a net false-positive reduction; expenditure changepoints fixed 6 but introduced 11.
18. Five-month forecasting is suitable only for sensitivity research now.
19. Yes, three-month remains preferable.
20. No multi-horizon product now; research discrete-time hazard later.
21. No defensible archetype similarity now.
22. No contractor trend without authoritative contractor/package identity.
23. Bounce-back is a useful qualified resilience signal, not proven core risk signal.
24. Dashboard: recovery narrative when supported; later, deadbanded risk trend.
25. Backend-only: changepoint diagnostics, peer diagnostics and expenditure associations.
26. Strongest current idea: expenditure changepoint, conditionally.
27. Strongest future-CUF idea: contractor/package peer performance with validity-dated identity.
28. Recommended compact set: the existing 14 Compact V2 features.
29. Yes, Compact V2 remains unchanged.
30. Next: resolve identity bridges and collect a new untouched future confirmation period; preregister expenditure changepoint and recovery tests before that period arrives.

## Permitted and forbidden claims

PRAHARI may claim that these hypotheses were implemented with past-only logic and evaluated in paired rolling-origin folds; one conditional expenditure signal modestly improved the weakest fold but did not improve held-out headline PR-AUC. It must not claim production readiness, causal funding effects, contractor risk, solved temporal instability, validated archetypes, or superior five-month forecasting.
