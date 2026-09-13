# PRAHARI Implementation Watch V1 Integration

`ImplementationWatchEngine` is the domain boundary. `backend/implementation_watch.py` maps current database history into the typed input without inventing CUF values. The project-detail API returns `implementation_watch` beside current state, Data Trust, model release, prediction eligibility and Officer Decision.

Data Trust remains intrinsic source/data quality. A source failure makes evidence-driven operational signals unreliable and the top state data-insufficient. Structural absence is reported as a schema limitation; it is not a project failure.

Officer Decision accepts the Watch payload as optional evidence. `WATCH` or `ELEVATED` with usable data can yield `REVIEW_RECOMMENDED` and `IMPLEMENTATION_PRESSURE_SIGNAL`; it never makes an alert eligible. Reporting/data insufficiency yields `DATA_VERIFICATION_REQUIRED` where appropriate. Existing prediction-release gates remain in force.

Ask PRAHARI receives a deterministic evidence view. The LLM may explain fired signals, source values, unavailable families and review reasons. It may not calculate facts, invent fields/probabilities/causes, or override Watch or Officer Decision.

Future real CUF and synthetic sandbox inputs use explicit `data_origin` values: `PAIMANA_CUF` and `SYNTHETIC_CUF_PROTOTYPE`. Synthetic sample payloads are stored with synthetic IDs and provenance. They are tests/demonstrations only and cannot be reported as historical evidence.

Reproduce the machine-readable audit with `python scripts/audit_cuf_implementation_watch_v1.py`. It writes field availability, feature readiness, family coverage, four synthetic state examples and a fingerprinted status record without modifying canonical data.
