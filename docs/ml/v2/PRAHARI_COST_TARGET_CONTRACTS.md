# PRAHARI Cost Target Contracts

**Status:** MACHINE_PROVISIONAL
**Versions:** `C1-v1-machine-provisional`, `C2-v1-machine-provisional`

## C1 — first approved upward deterioration

At anchor T, the project must have exact identity, be ongoing, have known original approved cost, have no observed approved revised cost above original, have sufficient contiguous history, and have every required project-level future report and project observation. A first revised-cost value strictly above the frozen original baseline in the horizon is positive. Complete evidence with no increase is negative.

## C2 — further approved upward deterioration

At T, the project must already have approved revised cost above original. That revised value is frozen as the comparison baseline. A strictly higher approved revised cost in the horizon is positive. The baseline is never updated using future information.

## Fail-closed policy

Unknown identity, source gaps, project disappearance without completion evidence, original-cost changes in the outcome window and reversal/correction-like sequences are censored. Completed-at-T projects are excluded. Downward revisions are not positive events. Anticipated-cost-only increases and expenditure increases are not events.

All ledgers retain source ID, page, table, schema, raw/normalized cost state, coverage, event month, change magnitude, correction flags and reasons. Human adjudication has not been completed, so all labels remain machine-provisional.
