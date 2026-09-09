# PRAHARI Backend Limitations

**Owner:** PRAHARI Team
**Area:** Backend
**Document Type:** CANONICAL
**Status:** APPROVED PROTOTYPE
**Last Updated:** 2026-09-09
**Canonical:** YES

- No scientifically confirmed final ML model or production prediction artifact is loaded. Prediction endpoints may return null; assistant project evidence then states `WITHHELD`.
- Review priority has no approved policy and is unavailable. No alert is inferred from a risk band.
- Authentication is an explicit future adapter boundary; this local SIH prototype does not claim production authorization or tenant isolation.
- Source page/table provenance is exposed only where the approved artifacts contain it; it is never invented.
- SQLite is for local demonstration and isolated tests. PostgreSQL is the deployment database.
- The assistant is bounded by the accepted local Llama/RAG subsystem. Ollama or RAG failure degrades the assistant but not project APIs.
- Historical aggregate-only and missing-source months remain unavailable; no project observations are synthesized across them.
- Export, record mutation, arbitrary SQL, raw-PDF upload, and LLM-driven writes are intentionally unsupported.
