# PRAHARI LLM Backend Contract V1

The backend calls `UnifiedPrahariAssistant.answer(question, project_evidence=None, request_id="...")`.

## Input

- `question`: required bounded officer text.
- `project_evidence`: optional object conforming exactly to `PrahariEvidence`; no raw PDF text or database dump.
- `request_id`: required backend correlation identifier in integration.

## Output

`UnifiedResult` contains:

- `request_id`
- `route`: PROJECT_EVIDENCE, DOCUMENT_RAG, MIXED or UNSUPPORTED
- `answer`: strict `PrahariResponse` or versioned `RagResponse` object
- `project_evidence_references`
- exact `document_citations`
- `reliability_statement`
- `limitations`
- `fallback_used` and `fallback_reason`
- `model_version`
- `rag_index_version`
- `latency_metadata`: retrieval, generation and total seconds

The backend must display fallback and limitations, preserve citations unchanged, never derive a probability from prose, and never execute an action requested by the model. It supplies already-authorized project evidence through deterministic services. Authentication, database access and UI rendering remain backend/frontend responsibilities.
