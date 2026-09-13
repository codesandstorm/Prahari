# PRAHARI Peer Benchmarking V1

**Owner:** PRAHARI Product Intelligence
**Status:** COMPLETE
**Last Updated:** 2026-09-13

Peer Benchmarking answers “How unusual is this project among a supported comparison group?” It does not predict failure, identify a cause, or determine an officer decision.

The service returns the project value, median, mean, p25, p75, mid-rank percentile, metric-specific peer count, selected group, mode, origin, directionality, interpretation, and limitations. It only evaluates metrics with observed values. Context-dependent metrics keep an uninterpreted raw percentile. “Higher worse” and “lower worse” semantics are applied only where the policy is unambiguous.

Modes are `REAL_CURRENT`, `REAL_HISTORICAL_AS_OF`, and `SYNTHETIC_SANDBOX`. Historical mode removes future records and selects each peer’s last-known record at or before the anchor. Real and synthetic origins are fail-closed and never combined.

The current real sector taxonomy is sparse, so the service preserves `UNKNOWN` and may transparently fall back to a broader supported group. This limits sector-specific claims but does not justify fabricated normalization.
