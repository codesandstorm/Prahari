# PRAHARI LLM Prototype Selection

**Decision status:** engineering prototype selection, not universal model ranking  
**Selected local model:** `llama3:8b` through Ollama

## Decision

PRAHARI Candidate Benchmark V1 compared four frozen candidates: Llama 3 8B, Qwen 3 8B, Gemma 3 4B and Gemma 3 12B. Gemma 3 12B remains the provisional automatic-quality leader with 182/201 automatic checks passed (90.55%). Llama 3 8B passed 180/201 (89.55%), approximately one percentage point behind.

Llama achieved 65/65 strict response-schema compliance, no frozen prompt-injection failures, no provenance failures and no runtime failures. Its measured median local latency was 17.82 seconds, compared with 53.63 seconds for Gemma 3 12B on the same benchmark hardware and protocol. PRAHARI therefore selects Llama 3 8B for the SIH engineering prototype based on combined quality, latency and structured-output practicality. This does not rewrite the benchmark winner.

The blinded human benchmark review was not completed. Automatic failures can include literal-detector false positives, so neither model has passed a production model-selection gate. Stronger production hardware or a later deployment environment may justify a frozen rebenchmark.

## Integration boundary

The LLM does not predict risk. It receives an already validated evidence object. The ML/statistical layer owns target, horizon, probability, risk band, calibration, abstention and model contributors. Llama may explain that supplied evidence, distinguish reliability from risk, identify unavailable information and recommend administrative verification.

The service flow is:

`validated evidence → delimited prompt → local Ollama → strict schema parse → grounding/safety validation → accepted response or deterministic fallback`

Model name, endpoint and generation settings are configuration-driven. The frozen `system_prompt_v1.txt`, evidence schema, response schema, Ollama client, boundary contract and fallback contract are reused rather than duplicated.

## Frozen prototype configuration

- Model: `llama3:8b`
- Endpoint: `http://127.0.0.1:11434`
- Temperature: 0
- Seed: 42
- Maximum generated tokens: 350
- Structured JSON requested
- Timeout: 90 seconds
- No API credential

## Safety behavior

Generated output is rejected when it fails the strict response schema, invents a probability during abstention, omits the reliability distinction, converts an agency into a contractor, introduces unsupported causal or misconduct assertions, or cites provenance unsupported by the evidence object. A rejected response is not repaired through another model call; the deterministic fallback is returned.

When prediction status is `ABSTAIN` or `WITHHELD`, the input schema requires null probability and null risk band. Both the validator and fallback prohibit inventing a percentage. Unsupported contractor, land, ministry, blame, fraud or causal questions are marked unsupported and answered with an explicit evidence-unavailable limitation.

## Integration smoke result

A five-case synthetic live suite exercised flag explanation, reliability, provenance, unsupported causality/contractor and abstention. It did not reuse or modify the 65-case selection benchmark.

- Cases: 5
- Median warmed local latency: 9.11 seconds
- Maximum: 13.12 seconds
- Valid generated responses accepted: 4
- Safety rejection with deterministic fallback: 1
- Ollama transport failures: 0

The unsupported “Which contractor caused this?” answer triggered the causal-claim validator and safely fell back. This is correct fail-closed behavior, not a successful generated answer.

## Prototype scope

Ready for controlled backend prototyping: validated evidence input, bounded local generation, strict parsing, deterministic fallback, safety rejection and auditable latency metadata.

Not production-ready: model quality selection, human-reviewed safety, production calibration, concurrency/load behavior, multilingual behavior, monitoring, user-interface integration, or operational authorization. No RAG, embeddings, vector database, fine-tuning, SQL agent, autonomous action or document retrieval has been implemented.

## Claim boundary

PRAHARI may state that Llama 3 8B was selected as the local SIH explanation prototype because its automatic benchmark performance was close to the provisional quality leader while its median latency was substantially lower.

PRAHARI must not state that Llama was the highest-scoring model, that the benchmark received completed human review, that the LLM predicts project risk, that generated explanations establish causes, or that the service is production-safe.

## Next gate

Freeze representative integration cases and have independent reviewers adjudicate every generated response and fallback. Only after the safety/grounding acceptance criteria pass should the service receive a versioned backend API wrapper. RAG and document retrieval remain later, separate gates.
