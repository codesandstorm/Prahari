# PRAHARI LLM Limitations

- The approved RAG corpus is one report and does not contain the official CUF schema, a PAIMANA concept note or a complete IPMD methodology.
- Retrieval is English lexical BM25; semantic paraphrases may rank poorly. Recall@1 is 0.68 and exact top-page ranking is imperfect.
- Live local generation is hardware-specific. In the five-case smoke test, median retrieval was 0.000075 seconds, generation 31.66 seconds and total latency 31.66 seconds.
- Four of five live cases used fallback: two expected bounded failures (missing CUF evidence and unsupported punishment), and two strict citation rejections. The mixed answer passed. This confirms fail-closed safety but not mature answer quality.
- The 24-case 100% acceptance result is a deterministic mocked-generation contract/control-path suite, not proof of Llama semantic quality.
- Candidate human review and final RAG answer-quality human review remain incomplete.
- The LLM cannot predict risk, change deterministic evidence, infer contractor or cause, allege misconduct, browse the web, execute SQL, modify records or take administrative action.
- No production authentication, concurrency/load qualification, multilingual evaluation, monitoring or UI integration exists.
