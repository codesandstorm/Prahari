# PRAHARI Implementation Watch V1

Implementation Watch answers one bounded question: what observable implementation pressure is visible now? It is a deterministic evidence layer, not a supervised predictor, causal engine, probability, risk score, or alert generator.

Inputs use the versioned `prahari-cuf-input-v1.0` schema. The engine evaluates execution, financial, milestone, land, ROW, clearance, procurement, reporting and data-quality families independently. Every signal carries its source, raw and normalized values, formula, threshold, availability, explanation, data-quality state and `causal_claim=false`.

Top-level policy `implementation-watch-v1.0` is:

- `ELEVATED`: at least one detected high-severity operational signal, or at least three detected operational signals.
- `WATCH`: one or two detected operational signals without the Elevated condition.
- `CLEAR`: at least one operational family was validly evaluated and no operational signal was detected.
- `DATA_INSUFFICIENT`: source trust failed or no operational family could be evaluated.
- `NOT_APPLICABLE`: reserved for a governed project context in which Watch does not apply.

Reporting and data-quality signals do not create project-risk claims. They route to verification. Predictions remain `WITHHELD`; Watch may independently be `ELEVATED`.
