# PRAHARI Alert System V1

Alert System V1 turns an eligible, governed Officer Decision into a persistent operational alert episode. It does not infer project risk and cannot be triggered by a raw model probability, raw Implementation Watch signal, or peer percentile.

## Authority chain

`source evidence -> Data Trust / release governance -> Implementation Watch or released prediction -> Officer Decision -> Alert Policy -> alert episode -> Officer Review`

Schedule and cost predictions remain `WITHHELD`. In the current system, a valid Implementation Watch result can support `REVIEW_RECOMMENDED`, and that Officer Decision can open an implementation-pressure alert. Data insufficiency is represented as a verification alert, never as deterioration.

Each alert preserves immutable opening evidence and refreshable current evidence. A deterministic deduplication key identifies one episode per project, data origin, alert type, reason family and policy version. Re-evaluating unchanged evidence is idempotent.

Alert states are `NEW`, `ACKNOWLEDGED`, `IN_REVIEW`, `MONITORING`, `PERSISTENT`, `ESCALATED`, `RESOLVED`, `DISMISSED`, and `REOPENED`. Every mutation produces append-only history containing the actor, time, reason, transition, evidence reference and safe metadata.

Real and synthetic alerts are persisted and queried in separate data-origin partitions. Synthetic results are demonstrations, not government evidence.
