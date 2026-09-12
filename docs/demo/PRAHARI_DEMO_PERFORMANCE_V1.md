# PRAHARI Demo Performance V1

**Owner:** PRAHARI integration team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** REFERENCE

Measured bottlenecks were an N+1 review-queue implementation and unnecessary LLM generation for already-withheld project explanations. The queue now batch-loads projects, histories, sources and predictions. Its process-local immutable result cache is keyed by hidden-password database identity, completed ingestion fingerprint, prediction count/latest timestamp and decision-policy version. Any governed data, prediction or policy change invalidates it.

| Path | Before | After |
|---|---:|---:|
| Review queue | 7,234 ms sample | 2,407 ms cold; 6.67 ms warm median; 8.70 ms warm max |
| Withheld project assistant | 21,109 ms sample | 8.53 ms median; 195.91 ms cold max |
| Unsupported query | 11.58 ms | 8.14 ms median; 8.45 ms max |
| Document RAG | 66,741 ms cold sample | remains approximately 67 seconds at the validated 600-token contract |

An attempted 300-token RAG output budget produced 45.6-second responses but failed validation and citations, so it was rejected. Retrieval corpus, top-k, safety prompt, citation validator and selected `llama3:8b` remain unchanged. Demo startup warms the model with a minimal JSON request; observed warm-up was 6.712 seconds.

Review queue pagination defaults to 25 and caps at 100. Filters support review state, reason code and model-release state. The first cold queue request remains around 2.4 seconds; run it once during demo preparation. Document RAG remains the principal latency risk.
