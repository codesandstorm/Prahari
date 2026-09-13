# PRAHARI Implementation Watch V1 Adversarial Self Audit

**Audit date:** 2026-09-13  
**Scope:** CUF registry, deterministic features, Watch policy, Data Trust, Officer Decision, backend, LLM evidence, tests and generated artifacts

## Resolved findings

SEVERITY: High  
FILE: `src/implementation_watch/engine.py`  
FUNCTION / LINE: `_explanation`  
PROBLEM: The first implementation eagerly formatted every template, so a non-numeric schema-limitation value crashed numeric templates.  
WHY IT MATTERS: A valid unavailable-family response could fail the whole API request.  
MINIMAL FIX: Make templates lazy and evaluate only the selected template; add state-specific wording.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: High  
FILE: `src/implementation_watch/features.py`  
FUNCTION / LINE: `milestone_metrics`, `tender_metrics`  
PROBLEM: Future actual dates supplied in a payload could have entered an earlier as-of evaluation.  
WHY IT MATTERS: This violates the as-of boundary and could turn future facts into present evidence.  
MINIMAL FIX: Ignore actual milestone/tender dates later than `as_of`; add regression tests.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: High  
FILE: `src/implementation_watch/features.py`  
FUNCTION / LINE: milestone, clearance and tender availability functions  
PROBLEM: An empty structured list was initially treated as not applicable.  
WHY IT MATTERS: Empty or unreported evidence is not proof that a requirement does not apply.  
MINIMAL FIX: Treat empty lists as `UNREPORTED`; require explicit `applicable=false` for `NOT_APPLICABLE`.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Medium  
FILE: `backend/decision_service.py`  
FUNCTION / LINE: `_build_items`, `_cache_key`  
PROBLEM: Initial integration risked a source lookup per project and did not include Watch policy version in the review-queue cache key.  
WHY IT MATTERS: It could regress queue latency or serve a stale policy result within a process.  
MINIMAL FIX: Reuse preloaded histories/sources and include Watch policy version in the cache key.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Medium  
FILE: `llm/service/fallback.py`  
FUNCTION / LINE: `deterministic_fallback`  
PROBLEM: The legacy fallback treated every land-acquisition question as unsupported even when deterministic land evidence exists.  
WHY IT MATTERS: It would hide valid Implementation Watch evidence from an officer.  
MINIMAL FIX: Permit land questions only when a detected, source-backed LAND signal exists; retain the causal/blame block.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Low  
FILE: `tests/test_longitudinal_pilot.py`  
FUNCTION / LINE: `test_source_pdf_hashes_are_unchanged`  
PROBLEM: The integration test ignored the repository's portable raw-root environment contract.  
WHY IT MATTERS: A correct external immutable archive failed in a linked worktree.  
MINIMAL FIX: Resolve PDFs from `PRAHARI_RAW_ROOT`, with the repository path as fallback.  
ARCHITECTURAL CHANGE REQUIRED? No

## Open limitations

SEVERITY: Medium  
FILE: `data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv`  
FUNCTION / LINE: `milestones_raw`  
PROBLEM: Historical milestone content is unstructured text and cannot safely populate Annexure III records.  
WHY IT MATTERS: Milestone, land, clearance and tender Watch families cannot be claimed from current history.  
MINIMAL FIX: Ingest governed structured PAIMANA/CUF records or complete a separately reviewed source parser; do not infer values now.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Medium  
FILE: `config/cuf_field_registry.json`  
FUNCTION / LINE: Current availability fields  
PROBLEM: Several Annexure I screen-only profile/contact subfields are grouped because the CUF document supplies form labels but not a downloadable data dictionary, enum values, null semantics or API schema.  
WHY IT MATTERS: A production ingestion mapping cannot yet guarantee field-by-field wire compatibility with PAIMANA.  
MINIMAL FIX: Obtain and version the governed PAIMANA API/database schema before implementing persistence; keep current typed fields optional and strict.  
ARCHITECTURAL CHANGE REQUIRED? No

SEVERITY: Low  
FILE: `src/implementation_watch/policy.py`  
FUNCTION / LINE: `CRITICAL_CLEARANCE_CATEGORIES`  
PROBLEM: The critical category set is a transparent PRAHARI review policy, not an official CUF severity definition.  
WHY IT MATTERS: It must not be presented as a MoSPI risk classification.  
MINIMAL FIX: Obtain domain-owner approval before operational deployment; retain versioning and explanatory caveat.  
ARCHITECTURAL CHANGE REQUIRED? No

No Critical or unresolved High finding remains.
