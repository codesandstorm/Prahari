# Mixed-Coverage Feature Availability
This is an availability audit, not feature selection.

| Candidate field/family | Availability | Safety | Likely future role | Additional need |
|---|---|---|---|---|
| project identifier | 30 project-level months; format changes by era | identity-only | grouping and joins | exact bridge validation |
| project name, agency, state | broadly present, extraction/schema missingness varies | conditional | static/context | normalization and human QA |
| ministry, sector | incomplete and not consistently separated | conditional | peer groups | CUF/official master data |
| original cost and target DoC | broadly present | conditional | static baseline | retrospective-change controls |
| revised/anticipated cost and DoC | schema-dependent | leakage-sensitive | current state/event research | feature cutoff policy |
| cumulative expenditure | 30 project-level months | conditional | current state/velocity | interval-aware calculation |
| physical progress | PAIMANA months; not OCMS inventory | conditional | current state/velocity | schema-availability flag |
| milestones achieved/total | OCMS months only | conditional | current state | CUF milestone detail |
| temporal deltas | derivable only between observed snapshots | conditional | temporal | elapsed-month and gap flags |
| peer-relative measures | partly supportable after normalization | conditional | peer comparison | official ministry/sector mapping |
| missingness/reporting gaps | supported | safe as reliability data | confidence/data quality | keep separate from risk |
| completion/status/issues/clearances | not consistently available here | unavailable | outcome/event context | CUF and lifecycle extraction |
| rainfall/flood/cyclone/commodity/legal/labour | absent | unavailable | external-shock context | external time-aligned datasets |

No forward fill, backward fill, interpolation, zero imputation, or synthetic project-month creation is permitted. A later feature such as progress change must be named and encoded as change over an observed interval, accompanied by interval length and gap status.
