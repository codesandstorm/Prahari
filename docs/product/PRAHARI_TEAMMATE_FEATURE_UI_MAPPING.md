# Teammate-feature UI contract

No newly tested feature is approved as a new core risk tile. Compact V2 remains the prototype risk input.

| Signal | Officer-facing wording | Display gate |
|---|---|---|
| Recovery history | “2 of 3 previously observed slowdowns recovered within two months.” | Reliability panel only; at least two fully resolved stalls |
| Expenditure changepoint | “The reported expenditure pattern shifted N months ago.” | Research detail only; never call it a funding change |
| Risk trend | “Risk is increasing / stable / decreasing.” | Only after consecutive predictions from one frozen calibrated model with a predeclared deadband |
| Peer velocity | Not displayed | Current grouping is too coarse and did not improve stability |
| Progress changepoint | Not displayed | Redundant/unstable against existing momentum features |
| Expenditure lag | Not displayed | Sparse association is not causal evidence |

`UNKNOWN` must be displayed when history or group size is insufficient. It must never be converted to “no risk.”
