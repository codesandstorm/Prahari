# PRAHARI deterministic explanation fallback

Use this fallback when Ollama is unavailable, the response is invalid JSON, grounding checks fail, or a safety check fails. It uses only validated evidence fields and performs no generation.

```text
Project is flagged for {review_priority or "review"}.

Observed evidence:
- {each supplied contributor, or "No validated contributors are available."}

Project risk:
{risk_band and supplied calibrated probability, or "Prediction withheld."}

Reliability:
{reliability_band}. {supplied reliability reasons}

Data quality:
{data_quality_status}

Recommended review:
Verify the current schedule, reported trajectory and available source evidence.

Sources:
{supplied provenance only, or "No source reference is available in this evidence object."}
```

Rules: never fill a placeholder from general knowledge; never show a probability when null; never transform absence into “low risk”; never name a contractor from agency; use “supporting signal,” not “cause.”
