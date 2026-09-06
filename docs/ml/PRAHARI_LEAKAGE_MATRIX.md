# PRAHARI Leakage Matrix

| Information | Status | Guardrail |
|---|---|---|
| values reported through t | SAFE | immutable as-of snapshot |
| future revised completion/cost | LEAKAGE | label only |
| actual completion/final cost | LEAKAGE | outcome only |
| anticipated date at t | CONDITIONAL | validate timestamp and administrative semantics |
| post-event shock fields | LEAKAGE for pre-event model | use only after `first_known_timestamp` |
| peer statistics | CONDITIONAL | fit within training fold and as of t |
| category encoding | CONDITIONAL | fit on training partition only |
| imputation | CONDITIONAL | training-fold statistics only |
| project rows split randomly | LEAKAGE | temporal split; audit repeated identity overlap |
| missing future project | UNKNOWN OUTCOME | censor; never label negative |
| aggregate/missing calendar month | UNKNOWN OUTCOME | censor crossing horizon |
| revised-date improvement | DATA CORRECTION/IMPROVEMENT | never convert to deterioration |

The test suite mutates future progress and confirms that the anchor features remain unchanged.
