# PRAHARI Peer Group Policy V1

**Owner:** PRAHARI Benchmarking
**Status:** APPROVED
**Last Updated:** 2026-09-13

Policy version: `peer-benchmark-v1.0`.

Selection proceeds in this exact order:

1. sector + cost band + lifecycle band;
2. sector + cost band;
3. sector;
4. portfolio-wide.

The subject project is excluded. A group is accepted at 15 peers; 30 is preferred and smaller supported groups carry a limitation. Fewer than 15 produces `BENCHMARK_INSUFFICIENT_PEERS`; percentiles are not computed.

Verified real cost distribution informed the transparent crore bands: below 150, 150–500, 500–1,000, 1,000–5,000, and 5,000+. Lifecycle is relative to approval and current approved completion: early ≤25%, mid ≤75%, late ≤100%, and overdue >100%. Missing or invalid dates produce `UNKNOWN` rather than an inferred stage.

The machine-readable source of truth is `config/benchmark_policy.json`.
