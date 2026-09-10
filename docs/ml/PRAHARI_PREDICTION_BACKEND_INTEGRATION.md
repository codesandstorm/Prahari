# PRAHARI Prediction Backend Integration V1

**Status:** PROVISIONAL

`FrozenModelPredictionProvider` is a thin adapter over `FrozenPredictionService`. It does not redesign the backend and does not create alerts. S1 and S2 are returned as distinct target records with horizon, feature, target and model versions.

The deterministic batch command scores projects observed at an as-of month and records available/abstained/withheld counts. Current V1 results are withheld, so the batch intentionally creates no PostgreSQL prediction rows. Once scientific gates pass, a separately reviewed transactional loader may persist versioned records under the existing unique prediction contract.

Assistant evidence must read authoritative stored prediction records. The LLM may explain the supplied result but may not recompute probability, change risk, infer contractors or claim causality.
