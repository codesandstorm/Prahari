# PRAHARI RAG Design V1

## Corpus and indexing

The bounded index contains one page-level-approved official source: the canonical June 2026 MoSPI Flash Report (`SRC-2026-06`, SHA-256 `d26872ac9336b451d311e823646560d29d8a6c2fbc9fdca9fd78fc22fd08ca15`). Only physical pages 1-21 are indexed: title, report note, overview, HML summaries and ministry summaries. The remaining 140 project-table pages are explicitly out of RAG scope because project facts belong to deterministic Domain A.

Text is extracted locally with PyMuPDF. Empty/unreadable pages are recorded and never indexed. Chunks are page-bounded, paragraph/text-flow aware, target 450 words with 40-word overlap only when a page exceeds that size. Each ID includes document, physical page, part number and a content-hash prefix. Every chunk records the complete source hash.

Index `rag-v1-src-2026-06-frontmatter-p1-21` contains 21 chunks. Artifacts include source manifest, chunks, extraction status, index metadata, embedding metadata and retrieval configuration. The build refuses to overwrite an existing version.

## Retrieval

V1 uses transparent local BM25-style lexical scoring, English stopword removal and three documented definition-query expansions. Top three chunks are supplied to generation. No embeddings, remote API, FAISS, LangChain or LlamaIndex are used.

The frozen 25-case retrieval benchmark reports Recall@1 0.68, Recall@3 0.96, Recall@5 1.00 and MRR 0.808. There were no wrong-document top results and eight wrong-page top results. Exact page ranking therefore remains a known weakness even though the correct page always appears by rank five.

## Grounding and citations

Every material document evidence point requires at least one citation. Citation document ID, title, physical page, chunk ID and source hash must exactly match a chunk supplied to the model. Invalid or absent citations fail closed; unsupported prose is not repaired by another model call.
