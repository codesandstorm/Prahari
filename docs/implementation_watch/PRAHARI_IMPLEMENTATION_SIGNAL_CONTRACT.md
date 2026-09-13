# PRAHARI Implementation Signal Contract

Per-signal states are `DETECTED`, `NOT_DETECTED`, `NOT_AVAILABLE`, `NOT_APPLICABLE`, `DATA_INSUFFICIENT`, and `UNRELIABLE`. The stable registry is `config/implementation_watch_reason_codes.json`.

Each serialized signal contains `code`, `family`, `status`, `severity`, `value`, `unit`, `as_of`, plain-language explanation, technical explanation, source availability, source references, availability, data-quality state, policy version, and `causal_claim=false`.

The technical view includes raw fields, normalized value, formula, threshold or policy, availability and semantic notes. The plain-language template states only the observation. “Physical progress is 17 percentage points behind plan” is valid. “Land caused the delay,” “the contractor caused the slowdown,” and allegations of misuse, fraud or corruption are prohibited without separate explicit authoritative evidence.

Trend states are `NEW`, `PERSISTENT`, `WORSENING`, `IMPROVING`, `RESOLVED`, and `NOT_AVAILABLE`. One observation cannot establish a trend. Source gaps, incompatible schema periods and missing values cannot be bridged or interpreted as improvement.
