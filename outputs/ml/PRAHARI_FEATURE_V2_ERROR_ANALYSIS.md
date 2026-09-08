# Feature V2 Error Analysis

**Status:** provisional machine-label analysis; human adjudication pending.

The deterministic error sample contains the 20 highest-scored false positives and 20 highest-scored false negatives for Compact V2. Each row retains project ID, anchor month, history span, progress, time remaining, required pace, stagnation and cost-revision state.

False positives can reflect successful intervention, a conservative alert, revised-date correction, schema-era effects, or missing recovery-plan evidence. They must not be called model mistakes until the target event is manually confirmed.

False negatives frequently remain observationally indistinguishable from healthy projects when contractor failure, land/clearance blockage, funding interruption, issue escalation, scope change or sudden weather/legal events are absent. The current table cannot determine which mechanism applied. This is the evidence gap—not permission to impute it.

The compact threshold is based on 10% validation review capacity. On the exploratory test period it produces precision 0.757, recall 0.549 and 4.94 false alerts per 100 anchors. Error rows are in `PRAHARI_FEATURE_V2_ERROR_CASES.csv`.

In the deterministic 40-case sample, false negatives average 54.78% reported progress and seven have some trailing stagnation; false positives average 39.32% progress and fourteen show stagnation. Thus low progress/stagnation separates some cases but is not a sufficient event explanation. None of the sampled cases is missing progress or required-velocity evidence, so the remaining error cannot be solved merely by numeric imputation.
