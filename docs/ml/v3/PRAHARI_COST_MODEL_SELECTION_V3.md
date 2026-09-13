# PRAHARI Cost Model Selection V3

Decision: **no C1 or C2 research candidate is admitted**.

C1 now has strong cohort and fold support, but model utility remains inadequate. Logistic regression produces the best mean PR-AUC, yet recall is only 2.24% at the past-validation threshold. The rule recalls more events but generates roughly 22.5 false alerts per 100 non-events and is poorly calibrated. Tree models and equal voting do not deliver a stable, material improvement that satisfies the predeclared selection order.

C2 remains scientifically unsupported for selection because no temporal fold meets admission requirements. Six-month C1 is evaluated as research, C2 six-month is unsupported, and twelve-month results remain support-check only.

Consequences:

- no `pipeline.joblib` is created;
- model cards explicitly say `NO_RESEARCH_CANDIDATE_ADMITTED`;
- backend `cost_intelligence` remains `WITHHELD`;
- Data Trust, prediction eligibility and Officer Decision semantics are unchanged;
- no `COST_RISK_SIGNAL` or `MULTI_RISK_SIGNAL` is emitted from fabricated probabilities;
- July 2026 remains untouched prospective evidence.

The next scientific priority is human validation of machine cost events and richer verified approved-revision history, particularly repeated revisions for C2—not metric tuning against these test folds.
