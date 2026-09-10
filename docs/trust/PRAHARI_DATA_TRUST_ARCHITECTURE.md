# PRAHARI Data Trust Architecture

**Owner:** PRAHARI data and ML team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** IMPLEMENTATION

Data Trust V1 sits between canonical data and target/model inference. It is deterministic and can be reproduced from project history, requested as-of month, source manifest, coverage register, Compact V2 and `data-trust-v1` policy.

It never reads model probability. It emits categorical dimension decisions, explicit evidence summaries and reason codes. Target eligibility and feature eligibility are evaluated before a model can run. Human target validation and calibration confirmation remain release gates.

The historical CSV audit is canonical for full trust evaluation. The backend adapter applies the same evaluator to stored snapshots; fields not persisted by Backend V1 are reported unavailable rather than invented.

The prediction-provider and assistant-evidence boundaries enforce the result after inference: when eligibility is false, status is `WITHHELD`, probability and risk are null, and deterministic reason codes replace any model-derived release signal. The LLM receives this state as evidence and cannot modify it.
