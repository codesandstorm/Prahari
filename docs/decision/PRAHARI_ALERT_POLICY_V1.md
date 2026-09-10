# PRAHARI Alert Policy V1

**Owner:** PRAHARI governance team
**Status:** DORMANT
**Document type:** REFERENCE

Alert states are `NOT_ELIGIBLE`, `ELIGIBLE_NOT_CREATED`, `OPEN`, `ACKNOWLEDGED` and `RESOLVED`. V1 evaluates only the first two and never creates a database alert.

Future eligibility requires an available released prediction, usable Data Trust, acceptable reliability, a review recommendation and an independently satisfied alert rule. `HIGH` risk alone is insufficient.

The deterministic deduplication key combines project, target, model version, alert type and reporting window. A matching unresolved key prevents another alert for the same administrative situation. Lifecycle transitions remain future governed work.
