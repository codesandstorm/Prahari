# PRAHARI LLM Final Architecture

PRAHARI keeps two evidence domains separate. Domain A is validated project prediction evidence; only deterministic ML/statistical services own target, horizon, probability, risk band, reliability, data quality, review priority, contributors and abstention. Domain B is approved official-document evidence; retrieval may explain policy and domain context but cannot alter Domain A.

The unified flow is `validate question -> deterministic route -> retrieve approved chunks when required -> construct delimited context -> local llama3:8b -> strict schema and citation validation -> accepted answer or deterministic fallback`. Routes are PROJECT_EVIDENCE, DOCUMENT_RAG, MIXED and UNSUPPORTED. The system exposes no arbitrary tools, SQL or actions.

Project-only requests reuse `PrahariAssistant`. Document and mixed routes use the versioned `RagResponse` contract. Mixed prompts physically separate Section A project evidence and Section B approved document evidence. Retrieved text and officer questions are explicitly untrusted data.

This subsystem is ready for a backend adapter, not production deployment. The deterministic control suite passes 24/24; live RAG generation still triggers strict citation fallbacks and needs human acceptance review.
