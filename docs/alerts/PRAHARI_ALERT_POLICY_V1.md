# PRAHARI Alert Policy V1

Policy version: `alert-policy-v1.0` in `config/alert_policy_v1.json`.

## Eligibility

An alert candidate is eligible only when Officer Decision is `REVIEW_RECOMMENDED` or `DATA_VERIFICATION_REQUIRED` and the corresponding governed evidence state is supported. Raw probability, raw Watch signals and benchmark ranking are explicitly disabled as direct triggers.

## Types and severity

- `IMPLEMENTATION_PRESSURE`: an authoritative review recommendation supported by Watch `WATCH` or `ELEVATED`.
- `DATA_VERIFICATION`, `REPORTING_GAP`, `SOURCE_QUALITY`: evidence-quality workflows that must not be described as project deterioration.
- `MODEL_SCHEDULE_WARNING` and `MODEL_COST_WARNING`: registered but inactive until prediction release governance authorizes them.

Watch maps to `ATTENTION`; Elevated maps to `HIGH`. Data-insufficient cases map to `ATTENTION`. Severity is administrative attention, not probability or predicted risk.

## Episode rules

- Deduplication scope: project, origin, type, reason family and policy version.
- Persistence: three distinct valid reporting cycles with equivalent governed evidence.
- Escalation: governed severity increases; no escalation is based on probability.
- Resolution: valid/evaluable evidence is `CLEAR`, or a data issue is explicitly verified/corrected.
- Missing evidence never proves resolution.
- Reopen: a closed episode receives newer equivalent governed evidence.
- Dismissal: actor and governed reason are mandatory.
