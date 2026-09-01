"""
PRAHARI — src/extraction/schema_detector.py

Schema detector for MoSPI Flash Report PDFs.

DESIGN PRINCIPLES (updated after Codex review 2026-09-01):

1. Rules use structured evidence: all_of / any_of / min_hits
2. Generic terms (e.g. DOC) CANNOT alone establish a schema.
3. Detection scans the FULL document or up to a configurable limit, not just the
   first N pages.
4. The detector always returns a structured SchemaEvidence object, never a bare string.
5. detected_schema is the AUTOMATED result. Human hypotheses (e.g. PAIMANA_V2_CANDIDATE
   for 2026 era) must be stored in manual_schema_assessment separately and NEVER
   silently merged into detected_schema.
6. Distinct error states: UNKNOWN_SCHEMA, INSPECTION_FAILED, DEPENDENCY_MISSING.

OUTPUTS (all runs):
    detected_schema      : str  — LEGACY | OCMS | PAIMANA_V1 | PAIMANA_V2 |
                                  UNKNOWN_SCHEMA | INSPECTION_FAILED | DEPENDENCY_MISSING
    confidence           : str  — HIGH | MEDIUM | LOW | NONE
    matched_evidence     : list[str]
    evidence_pages       : list[int]
    rule_used            : str  — the rule name that produced the classification
    unmatched_all_of     : list[str]  — required terms that were NOT found
    conflicting_schemas  : list[str]  — other schemas whose partial evidence was also seen
    error_detail         : str | None
    pages_sampled        : list[int]
    pages_total          : int
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema evidence result object
# ---------------------------------------------------------------------------

@dataclass
class SchemaEvidence:
    """Structured output of one schema detection run."""

    # Primary automated result
    detected_schema: str = "UNKNOWN_SCHEMA"
    confidence: str = "NONE"
    candidate_schema: str | None = None
    candidate_confidence: str = "NONE"
    candidate_evidence: list[str] = field(default_factory=list)
    matched_evidence: list[str] = field(default_factory=list)
    evidence_pages: list[int] = field(default_factory=list)
    rule_used: str = ""

    # Diagnostics
    unmatched_all_of: list[str] = field(default_factory=list)
    conflicting_schemas: list[str] = field(default_factory=list)
    error_detail: str | None = None
    pages_sampled: list[int] = field(default_factory=list)
    pages_total: int = 0
    table_contexts: list[dict[str, Any]] = field(default_factory=list)

    # Human-override fields (populated EXTERNALLY — NOT by the detector)
    manual_schema_assessment: str | None = None
    manual_assessment_status: str | None = None  # PLAUSIBLE | VERIFIED | REJECTED
    manual_evidence_pages: list[int] = field(default_factory=list)
    manual_reviewer: str | None = None
    manual_reviewed_at: str | None = None  # ISO 8601

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_schema": self.detected_schema,
            "confidence": self.confidence,
            "candidate_schema": self.candidate_schema,
            "candidate_confidence": self.candidate_confidence,
            "candidate_evidence": self.candidate_evidence,
            "matched_evidence": self.matched_evidence,
            "evidence_pages": self.evidence_pages,
            "rule_used": self.rule_used,
            "unmatched_all_of": self.unmatched_all_of,
            "conflicting_schemas": self.conflicting_schemas,
            "error_detail": self.error_detail,
            "pages_sampled": self.pages_sampled,
            "pages_total": self.pages_total,
            "table_contexts": self.table_contexts,
            "manual_schema_assessment": self.manual_schema_assessment,
            "manual_assessment_status": self.manual_assessment_status,
            "manual_evidence_pages": self.manual_evidence_pages,
            "manual_reviewer": self.manual_reviewer,
            "manual_reviewed_at": self.manual_reviewed_at,
        }


# ---------------------------------------------------------------------------
# Rule evaluation helpers
# ---------------------------------------------------------------------------

def _pages_containing(keyword: str, page_texts: list[tuple[int, str]]) -> list[int]:
    """Return 1-indexed page numbers where keyword appears (case-sensitive)."""
    def contains(text: str) -> bool:
        if keyword == "OCMS":
            text = text.replace("Legacy OCMS Code", "")
        return keyword in text
    return [pnum for pnum, txt in page_texts if contains(txt)]


def _pages_containing_ci(keyword: str, page_texts: list[tuple[int, str]]) -> list[int]:
    """Case-insensitive variant."""
    kw_lower = keyword.lower()
    return [pnum for pnum, txt in page_texts if kw_lower in txt.lower()]


def _evaluate_rule(
    rule: dict,
    page_texts: list[tuple[int, str]],
) -> tuple[bool, list[str], list[int], list[str]]:
    """
    Evaluate a single schema rule against extracted page texts.

    Returns:
        passed           : bool
        matched_terms    : list[str]
        matched_pages    : list[int]
        unmatched_all_of : list[str]
    """
    matched_terms: list[str] = []
    matched_pages: set[int] = set()
    unmatched_all_of: list[str] = []
    all_of_page_sets: list[set[int]] = []

    # --- all_of: EVERY term must appear ---
    for kw in rule.get("all_of", []):
        pages = _pages_containing(kw, page_texts)
        if not pages:
            unmatched_all_of.append(kw)
        else:
            matched_terms.append(kw)
            matched_pages.update(pages)
            all_of_page_sets.append(set(pages))

    if unmatched_all_of:
        return False, matched_terms, sorted(matched_pages), unmatched_all_of
    # Required markers must coexist on at least one relevant page. Arbitrary
    # full-document co-occurrence is not production evidence.
    common_required_pages = set.intersection(*all_of_page_sets) if all_of_page_sets else set()
    if all_of_page_sets and not common_required_pages:
        return False, matched_terms, sorted(matched_pages), []
    if common_required_pages:
        matched_pages = set(common_required_pages)

    # --- any_of: at least ONE term must appear ---
    any_of_terms = rule.get("any_of", [])
    if any_of_terms:
        any_matched = []
        for kw in any_of_terms:
            pages = _pages_containing(kw, page_texts)
            eligible_pages = set(pages)
            if common_required_pages:
                eligible_pages &= common_required_pages
            if eligible_pages:
                any_matched.append(kw)
                matched_pages.update(eligible_pages)
        if not any_matched:
            return False, matched_terms, sorted(matched_pages), []
        matched_terms.extend(any_matched)

    # --- min_hits: number of distinct matched terms must reach threshold ---
    min_hits = rule.get("min_hits", 0)
    if len(matched_terms) < min_hits:
        return False, matched_terms, sorted(matched_pages), []

    return True, matched_terms, sorted(matched_pages), []


# ---------------------------------------------------------------------------
# Detection priority ordering
# ---------------------------------------------------------------------------

# These are checked in order; first match wins.
DETECTION_PRIORITY = ["PAIMANA_V2", "PAIMANA_V1", "OCMS", "LEGACY"]


def _build_rules(config: dict) -> dict[str, list[dict]]:
    """
    Parse schema_versions from config into evaluation-ready rule dicts.

    Config schema rule format (in config.yaml):

        schema_versions:
          PAIMANA_V2:
            rules:
              - name: "paimana_v2_identity_fields"
                all_of:
                  - "Legacy OCMS Code"
                  - "PMGID"
                confidence: HIGH
            ...

    Falls back to legacy keyword list format for backwards compatibility.
    """
    rules_by_schema: dict[str, list[dict]] = {}
    for schema_code, schema_def in config.get("schema_versions", {}).items():
        if "rules" in schema_def:
            rules_by_schema[schema_code] = schema_def["rules"]
        elif "keywords" in schema_def:
            # Legacy: treat list of keywords as a single all_of rule
            kws = schema_def["keywords"]
            if kws:
                rules_by_schema[schema_code] = [
                    {
                        "name": f"{schema_code}_legacy_keyword_rule",
                        "all_of": kws,
                        "confidence": "MEDIUM",
                    }
                ]
    return rules_by_schema


# ---------------------------------------------------------------------------
# Text extractor (injectable for testing)
# ---------------------------------------------------------------------------

def extract_text_from_pages(
    path: Path,
    max_pages: int | None = None,
) -> list[tuple[int, str]]:
    """
    Extract text from PDF pages using pdfplumber.

    Returns list of (1-indexed-page-number, page_text).
    max_pages=None means all pages (up to library limits).
    Raises ImportError if pdfplumber is unavailable.
    """
    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError("pdfplumber is required for schema detection") from exc

    result: list[tuple[int, str]] = []
    with pdfplumber.open(str(path)) as pdf:
        pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
        for i, page in enumerate(pages):
            txt = page.extract_text() or ""
            result.append((i + 1, txt))
    return result


def _find_table_of_contents_pages(page_texts: list[tuple[int, str]]) -> list[int]:
    """Return page numbers that appear to contain a table of contents."""
    toc_markers = ["CONTENTS", "Table of Contents", "List of Tables", "Appendix : List"]
    return [
        pnum for pnum, txt in page_texts
        if any(m.lower() in txt.lower() for m in toc_markers)
    ]


def _find_project_table_pages(page_texts: list[tuple[int, str]]) -> list[int]:
    """Return pages that appear to contain project-level table rows."""
    table_markers = [
        "All Ongoing Projects",
        "Project Code",
        "Project Name",
        "Ongoing Projects",
        "Completed Projects",
    ]


def discover_table_contexts(
    page_texts: list[tuple[int, str]],
    heading: str = "All Ongoing Projects",
) -> list[dict[str, Any]]:
    """Discover actual table pages and keep physical and printed pages separate.

    A contents-only occurrence is recorded but never used as production schema
    evidence. Data pages must contain the heading plus structural project-table
    markers. ``pdf_page_index`` is one-based physical PDF order.
    """
    toc_pages = set(_find_table_of_contents_pages(page_texts))
    contexts: list[dict[str, Any]] = []
    for pdf_index, text in page_texts:
        if heading.lower() not in text.lower():
            continue
        lowered = text.lower()
        is_toc = pdf_index in toc_pages or "table of contents" in lowered or "list of tables" in lowered
        markers = [
            marker for marker in ("Project Name", "Sl.No", "Project Code", "Legacy OCMS Code", "PMGID")
            if marker in text
        ]
        is_data_page = not is_toc and len(markers) >= 2
        printed_match = re.search(r"\bPage\s+(\d+)\b", text, flags=re.IGNORECASE)
        contexts.append({
            "pdf_page_index": pdf_index,
            "printed_page_number": int(printed_match.group(1)) if printed_match else None,
            "heading_matched": heading,
            "context_type": "TOC" if is_toc else ("TABLE_DATA" if is_data_page else "TABLE_HEADING"),
            "structural_markers": markers,
            "char_count": len(text),
        })

    data = [c for c in contexts if c["context_type"] == "TABLE_DATA"]
    if data:
        representatives = {0, len(data) // 2, len(data) - 1}
        for index, context in enumerate(data):
            context["representative_role"] = (
                "FIRST" if index == 0 else
                "MIDDLE" if index == len(data) // 2 else
                "NEAR_FINAL" if index == len(data) - 1 else None
            )
            context["representative"] = index in representatives
    return contexts
    return [
        pnum for pnum, txt in page_texts
        if any(m in txt for m in table_markers)
    ]


# ---------------------------------------------------------------------------
# Page sampling strategy
# ---------------------------------------------------------------------------

def _build_sample_page_indices(total_pages: int, detected_table_pages: list[int]) -> list[int]:
    """
    Build a deterministic sampling set covering:
    - cover / early pages (1–5)
    - representative middle pages
    - detected project-table pages
    - last 5 pages

    Returns sorted list of 0-indexed page numbers to read.
    """
    indices: set[int] = set()

    # Early pages
    for i in range(min(5, total_pages)):
        indices.add(i)

    # Middle pages
    if total_pages > 10:
        mid = total_pages // 2
        for i in range(max(0, mid - 2), min(total_pages, mid + 3)):
            indices.add(i)

    # Late pages
    for i in range(max(0, total_pages - 5), total_pages):
        indices.add(i)

    # Project table pages (0-indexed = page_num - 1)
    for p in detected_table_pages:
        indices.add(p - 1)

    return sorted(indices)


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def detect_schema(
    path: Path,
    config: dict,
    max_pages: int | None = None,
    _extract_fn=None,  # injectable for tests
) -> SchemaEvidence:
    """
    Detect the schema version of a MoSPI Flash Report PDF.

    Args:
        path        : Path to PDF file.
        config      : Loaded config.yaml as dict.
        max_pages   : If set, limits page text extraction to first N pages.
                      None = all pages (recommended; required for correctness).
        _extract_fn : Override for text extraction (testing only).

    Returns:
        SchemaEvidence dataclass. Never raises; errors captured in error_detail.
    """
    evidence = SchemaEvidence()

    # --- Dependency check ---
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        evidence.detected_schema = "DEPENDENCY_MISSING"
        evidence.error_detail = "pdfplumber not installed"
        evidence.confidence = "NONE"
        return evidence

    # --- Extract text ---
    extract_fn = _extract_fn or extract_text_from_pages
    try:
        page_texts = extract_fn(path, max_pages)
    except ImportError as exc:
        evidence.detected_schema = "DEPENDENCY_MISSING"
        evidence.error_detail = f"{type(exc).__name__}: {exc}"
        evidence.confidence = "NONE"
        logger.exception("Failed to extract text from %s", path)
        return evidence
    except OSError as exc:
        evidence.detected_schema = "CORRUPT_PDF"
        evidence.error_detail = f"{type(exc).__name__}: {exc}"
        evidence.confidence = "NONE"
        logger.exception("PDF could not be read: %s", path)
        return evidence
    except Exception as exc:
        if type(exc).__module__.startswith(("pdfminer", "pdfplumber", "pypdf")):
            evidence.detected_schema = "CORRUPT_PDF"
            evidence.error_detail = f"{type(exc).__name__}: {exc}"
            evidence.confidence = "NONE"
            logger.exception("PDF parser rejected %s", path)
            return evidence
        logger.exception("Unexpected schema-detector failure for %s", path)
        raise

    if not page_texts:
        evidence.detected_schema = "INSPECTION_FAILED"
        evidence.error_detail = "No pages extracted — file may be empty or corrupt"
        evidence.confidence = "NONE"
        return evidence

    evidence.pages_total = len(page_texts)
    evidence.pages_sampled = [pnum for pnum, _ in page_texts]

    if not isinstance(config.get("schema_versions"), dict):
        evidence.detected_schema = "CONFIG_ERROR"
        evidence.error_detail = "schema_versions must be a mapping"
        return evidence

    evidence.table_contexts = discover_table_contexts(page_texts)
    table_page_numbers = {
        context["pdf_page_index"] for context in evidence.table_contexts
        if context["context_type"] == "TABLE_DATA"
    }
    table_texts = [(pnum, text) for pnum, text in page_texts if pnum in table_page_numbers]
    rules_by_schema = _build_rules(config)

    # Production rules are evaluated only in relevant project-table context.
    # Full-document text is used solely to report weak candidate evidence.
    production_hits: list[tuple[str, list[str], list[int], str, str]] = []
    if table_texts:
        for schema_code in DETECTION_PRIORITY:
            for rule in rules_by_schema.get(schema_code, []):
                passed, terms, pages, _ = _evaluate_rule(rule, table_texts)
                if passed:
                    production_hits.append((
                        schema_code, terms, pages,
                        rule.get("name", f"{schema_code}_rule"),
                        rule.get("confidence", "MEDIUM"),
                    ))

    matched_schemas = list(dict.fromkeys(hit[0] for hit in production_hits))
    # V1's Project Code is a strict subset of V2 identity evidence, not a
    # conflict. Other cross-family matches remain blocking conflicts.
    if "PAIMANA_V2" in matched_schemas and "PAIMANA_V1" in matched_schemas:
        matched_schemas.remove("PAIMANA_V1")
        production_hits = [hit for hit in production_hits if hit[0] != "PAIMANA_V1"]
    if len(matched_schemas) > 1:
        evidence.detected_schema = "CONFLICTING_SCHEMA"
        evidence.confidence = "NONE"
        evidence.conflicting_schemas = matched_schemas
        evidence.rule_used = "conflicting_table_context_rules"
    elif production_hits:
        schema, terms, pages, rule_name, confidence = production_hits[0]
        evidence.detected_schema = schema
        evidence.confidence = confidence
        evidence.matched_evidence = terms
        evidence.evidence_pages = pages
        evidence.rule_used = rule_name
    else:
        evidence.detected_schema = "UNKNOWN_SCHEMA"
        evidence.confidence = "NONE"
        evidence.rule_used = "no_table_context_rule_matched"

    # Candidate evidence never selects a production adapter.
    candidate_terms: dict[str, list[str]] = {
        "PAIMANA_V2": ["Legacy OCMS Code", "PMGID"],
        "PAIMANA_V1": ["Project Code"],
        "OCMS": ["OCMS", "Online Computerised Monitoring System"],
        "LEGACY": ["DOA", "DOC"],
    }
    full_text = "\n".join(text for _, text in page_texts)
    candidates: list[tuple[str, list[str]]] = []
    for schema, terms in candidate_terms.items():
        hits = [term for term in terms if term in full_text]
        if hits:
            candidates.append((schema, hits))
    if evidence.detected_schema in {"UNKNOWN_SCHEMA", "CONFLICTING_SCHEMA"} and candidates:
        evidence.candidate_schema = candidates[0][0]
        evidence.candidate_confidence = "LOW"
        evidence.candidate_evidence = candidates[0][1]

    return evidence


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    import yaml

    parser = argparse.ArgumentParser(description="Detect schema version of a PAIMANA Flash Report PDF.")
    parser.add_argument("--file", required=True, help="Path to PDF file")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit pages scanned (default: all)")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    result = detect_schema(Path(args.file), cfg, max_pages=args.max_pages)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
