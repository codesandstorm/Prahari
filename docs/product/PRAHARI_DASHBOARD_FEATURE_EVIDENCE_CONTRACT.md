# Dashboard Feature Evidence Contract

Officers see six evidence groups—not 14 raw model columns.

| Evidence group | Display | Underlying features |
|---|---|---|
| Schedule Feasibility | “Needs X progress points/month; Y months remain.” | remaining schedule, required velocity, progress-vs-elapsed gap |
| Recent Momentum | “Progress was unchanged for N observed intervals.” | consecutive stagnation, physical progress |
| Financial/Physical Alignment | paired trajectories without accusation | expenditure/cost and expenditure velocity |
| Revision History | current cost revision context | cumulative cost revision percentage |
| Project Context | scale, planned duration and age | log cost, duration, age |
| Data Reliability | history depth and missing progress | history span, schema/missing indicator |

Backend-only: transformed cost, imputation indicators, model encodings, raw thresholds, uncalibrated probability and diagnostic observability fields. Never show a raw feature as a cause, blame an agency, identify a contractor from agency, or label financial/physical mismatch as corruption.

For low evidence quality, show `PREDICTION WITHHELD` and the reliability reason. A partial resilience panel may show work remaining, time remaining, required pace and observed momentum. It must not collapse these components into an arbitrary resilience score.
