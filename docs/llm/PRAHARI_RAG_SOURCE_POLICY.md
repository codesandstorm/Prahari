# PRAHARI RAG Source Policy

Candidate sources are classified as APPROVED_OFFICIAL, PROJECT_INTERNAL, UNVERIFIED or EXCLUDE. Only explicitly `approved_for_rag=true` sources can be indexed.

- APPROVED_OFFICIAL: authoritative document, locally preserved, hash-matched to the source manifest, and page-level approved for this use.
- PROJECT_INTERNAL: team notes, designs, research hypotheses and generated summaries. Never official evidence.
- UNVERIFIED: apparently official source lacking explicit page-level RAG approval or validation for this index.
- EXCLUDE: missing, duplicate, rejected, generated, unreadable or otherwise ineligible material.

The repository contains many MoSPI Flash Reports, but V1 approves only validated `SRC-2026-06`. Other canonical reports remain UNVERIFIED for RAG—not declared unofficial. The rejected July duplicate and missing records are excluded. Internal CUF documents are excluded because repository research explicitly states that the official CUF schema has not been obtained. PRAHARI must answer CUF-schema questions as insufficient evidence.

No arbitrary internet page, team note, model-generated summary or unapproved external source may enter the index. Adding a source requires a new immutable index version, stable document ID, organization/title/type/date, source path, SHA-256, page count, language and written approval reason.
