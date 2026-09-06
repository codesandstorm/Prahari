# Mixed-Coverage ML-Readiness Audit
No model, label, target, prediction, explanation, or risk score was created. The dataset is an engineering artifact awaiting human validation.

| Problem | Why it matters | Evidence | Future ML must do | Must not do |
|---|---|---|---|---|
| Source-gap censoring | absent snapshots hide events | five aggregate-only months and February 2025 missing | calculate horizon observability from calendar coverage | call an unobserved event a negative |
| Left censoring | first appearance may follow years of prior history | window starts July 2023 with active projects | require stated history depth and flag limited history | treat first appearance as project start |
| Right censoring | future outcomes near June 2026 are unavailable | observation window ends June 2026 | exclude or censor incomplete future horizons | label incomplete horizons negative |
| Survivor bias | ongoing inventories omit completed/dropped projects | lifecycle tables are not yet normalized | add official lifecycle event data | infer completion from disappearance |
| Correlated rows | project-month rows are repeated measurements | 48,326 rows represent 3,417 canonical identities | group splits by canonical project | random row-wise train/test split |
| Identity drift | identifiers change across OCMS/PAIMANA | exact Legacy OCMS bridge exists; ambiguous bridge codes remain | use verified bridges and isolate ambiguous identities | fuzzy-link automatically |
| Schema drift | fields differ by report family | OCMS lacks physical-progress percentage; modern fields vary | include schema-availability indicators | collapse absent schema fields into ordinary nulls |
| Retrospective corrections | dates, costs, and progress may decrease/change | monthly reports can revise prior facts | preserve change direction and source provenance | silently overwrite history |
| Target leakage | revised cost/DoC can reveal the event being predicted | current reports contain revised and anticipated values | freeze feature cutoff before outcome window | use post-event revisions as predictors |
| Data quality vs risk | missingness may reflect reporting systems | partial text layers and schema gaps are explicit | model reliability separately from project risk | interpret poor reporting as project failure |
| Calibration/OOD | older OCMS differs from modern PAIMANA | two major schema families | validate temporally and by era; report reliability | assume one stationary distribution |

Future target observability must classify each anchor as `FULLY_OBSERVABLE`, `PARTIALLY_OBSERVABLE`, `CENSORED_BY_GAP`, `RIGHT_CENSORED`, or `LEFT_HISTORY_LIMITED`. For any horizon, count the project-level source months actually available in `t+1...t+H`; do not impose a final threshold until event definitions and lifecycle sources are validated.
