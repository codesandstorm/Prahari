# PRAHARI Data Trust Architecture

**Owner:** PRAHARI data and ML team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** IMPLEMENTATION

Data Trust V1 sits between canonical data and target/model inference. It is deterministic and can be reproduced from project history, requested as-of month, source manifest, coverage register, Compact V2 and `data-trust-v1` policy.

It never reads model probability. It emits categorical intrinsic-evidence decisions and reason codes. Human target validation, calibration confirmation and model approval belong to the separate Model Release contract and never make project data appear untrustworthy.

The historical CSV audit is canonical for full trust evaluation. The backend adapter applies the same evaluator to stored snapshots; fields not persisted by Backend V1 are reported unavailable rather than invented.

Prediction eligibility combines intrinsic Data Trust with model release, target, completion and artifact gates. At the provider and assistant boundaries, ineligibility forces `WITHHELD` with null probability and risk. The LLM receives these separate states and cannot modify them.
