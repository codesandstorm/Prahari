#!/usr/bin/env python3
"""
PRAHARI Documentation Validator
================================
Checks the documentation structure for consistency, metadata completeness,
and link integrity.

Usage:
    python scripts/validate_docs.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed

No external dependencies required (stdlib only).
"""
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

VALID_STATUSES = {
    "ACTIVE",
    "APPROVED",
    "APPROVED WITH LIMITATIONS",
    "RESEARCH IN PROGRESS",
    "REVIEW REQUIRED",
    "NOT STARTED",
    "BLOCKED",
    "SUPERSEDED",
    "PROVISIONAL",
    "COMPLETE",
    "IN PROGRESS",
    "NOT IMPLEMENTED",
    "OPEN",
    "PARTIALLY ANSWERED",
    "PENDING",
    "FUTURE",
    "RESEARCH ONLY",
    "VERIFIED",
    "PLAUSIBLE",
    "UNKNOWN",
    "REJECTED",
}

VALID_DOC_TYPES = {
    "RESEARCH",
    "PROPOSAL",
    "APPROVED",
    "REFERENCE",
    "AUDIT",
    "IMPLEMENTATION",
    "SUPERSEDED",
    "INDEX",
}

# Files that MUST exist
REQUIRED_FILES = [
    "docs/README.md",
    "docs/shared/PROJECT_OVERVIEW.md",
    "docs/shared/CURRENT_TECHNICAL_HYPOTHESIS.md",
    "docs/shared/DATA_CONTRACT.md",
    "docs/shared/API_DATA_HANDOFF.md",
    "docs/shared/TEAM_DEPENDENCIES.md",
    "docs/shared/DECISION_LOG.md",
    "docs/shared/OPEN_QUESTIONS.md",
    "docs/shared/GATE_STATUS.md",
    "docs/shared/REVIEW_WORKFLOW.md",
    "docs/shared/TERMINOLOGY_AND_CONVENTIONS.md",
    "docs/reference/CUF_RESEARCH_STATUS.md",
    "docs/reference/RESEARCH_EVIDENCE_GUIDELINES.md",
    "docs/reference/DATA_SOURCE_REGISTER.md",
    "docs/extraction/README.md",
    "docs/extraction/PAIMANA_V2_EXTRACTION_SPEC.md",
    "docs/audits/INDEX.md",
    "docs/team/sandarbh/README.md",
    "docs/team/sandarbh/SCHEMA_EVOLUTION.md",
    "docs/team/sandarbh/PROJECT_IDENTITY_ANALYSIS.md",
    "docs/team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md",
    "docs/team/sandarbh/DATA_DICTIONARY_NOTES.md",
    "docs/team/pavitra/README.md",
    "docs/team/akshita/README.md",
    "docs/team/jashan/README.md",
    "docs/team/sanskaar/README.md",
    "docs/templates/TEAM_RESEARCH_TEMPLATE.md",
    "docs/templates/TECHNICAL_DECISION_TEMPLATE.md",
    "docs/templates/AUDIT_TEMPLATE.md",
    "docs/templates/HANDOFF_TEMPLATE.md",
    "docs/templates/EXTRACTION_REVIEW_TEMPLATE.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/CODEOWNERS",
    ".github/workflows/quality-checks.yml",
]

# Files that should have metadata headers (Owner + Status at minimum)
METADATA_REQUIRED = [
    "docs/shared/PROJECT_OVERVIEW.md",
    "docs/shared/CURRENT_TECHNICAL_HYPOTHESIS.md",
    "docs/shared/DATA_CONTRACT.md",
    "docs/shared/API_DATA_HANDOFF.md",
    "docs/shared/TEAM_DEPENDENCIES.md",
    "docs/shared/DECISION_LOG.md",
    "docs/shared/OPEN_QUESTIONS.md",
    "docs/shared/GATE_STATUS.md",
    "docs/shared/REVIEW_WORKFLOW.md",
    "docs/shared/TERMINOLOGY_AND_CONVENTIONS.md",
    "docs/reference/CUF_RESEARCH_STATUS.md",
    "docs/reference/RESEARCH_EVIDENCE_GUIDELINES.md",
    "docs/reference/DATA_SOURCE_REGISTER.md",
    "docs/extraction/PAIMANA_V2_EXTRACTION_SPEC.md",
    "docs/team/sandarbh/SCHEMA_EVOLUTION.md",
    "docs/team/sandarbh/PROJECT_IDENTITY_ANALYSIS.md",
    "docs/team/sandarbh/TEMPORAL_LEAKAGE_NOTES.md",
    "docs/team/sandarbh/DATA_DICTIONARY_NOTES.md",
]

# Raw data paths that must NEVER have docs linked into them
PROTECTED_DATA_PATHS = [
    "data/raw/",
]


def check_required_files(errors: list) -> int:
    """Check that all required files exist."""
    fail = 0
    for rel_path in REQUIRED_FILES:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"MISSING FILE: {rel_path}")
            fail += 1
    return fail


def check_metadata(errors: list) -> int:
    """Check that required metadata fields are present in key documents."""
    fail = 0
    for rel_path in METADATA_REQUIRED:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            continue  # Already caught by check_required_files
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            errors.append(f"UNREADABLE: {rel_path} — {e}")
            fail += 1
            continue
        missing_fields = []
        if "**Owner:**" not in content and "**Owner :**" not in content:
            missing_fields.append("**Owner:**")
        if "**Status:**" not in content and "**Status :**" not in content:
            missing_fields.append("**Status:**")
        if "**Last Updated:**" not in content and "**Last Updated :**" not in content:
            missing_fields.append("**Last Updated:**")
        if missing_fields:
            errors.append(
                f"MISSING METADATA in {rel_path}: {', '.join(missing_fields)}"
            )
            fail += 1
    return fail


def check_superseded(errors: list) -> int:
    """Check that SUPERSEDED documents contain a 'Superseded by:' link."""
    fail = 0
    for md_file in DOCS_ROOT.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "**Status:** SUPERSEDED" in content or "Status: SUPERSEDED" in content:
            if "Superseded by:" not in content and "superseded by:" not in content.lower():
                rel = md_file.relative_to(REPO_ROOT)
                errors.append(
                    f"SUPERSEDED without replacement link: {rel}"
                )
                fail += 1
    return fail


def extract_md_links(content: str):
    """Extract all relative Markdown links from content."""
    # Matches [text](path) where path does not start with http or #
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    links = []
    for match in pattern.finditer(content):
        href = match.group(2).strip()
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
            continue
        # Strip anchors like file.md#section
        href_clean = href.split("#")[0]
        if href_clean:
            links.append((href_clean, match.group(0)))
    return links


def check_relative_links(errors: list) -> int:
    """Check that relative Markdown links in docs/ resolve to existing files."""
    fail = 0
    for md_file in DOCS_ROOT.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for href, raw_link in extract_md_links(content):
            # Resolve relative to the document's directory
            target = (md_file.parent / href).resolve()
            if not target.exists():
                rel_doc = md_file.relative_to(REPO_ROOT)
                errors.append(
                    f"BROKEN LINK in {rel_doc}: {raw_link} → {href} (not found)"
                )
                fail += 1
    return fail


def check_no_raw_path_in_docs(errors: list) -> int:
    """Check that docs/ files don't contain paths that write to data/raw/."""
    fail = 0
    # This is a soft check — just warn if docs link to data/raw/ paths
    for md_file in DOCS_ROOT.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Check for write-related mentions pointing to data/raw
        for protected in PROTECTED_DATA_PATHS:
            if f"write to {protected}" in content.lower() or \
               f"output to {protected}" in content.lower():
                rel = md_file.relative_to(REPO_ROOT)
                errors.append(
                    f"SUSPICIOUS RAW WRITE REFERENCE in {rel}: mentions writing to {protected}"
                )
                fail += 1
    return fail


def main():
    print("=" * 60)
    print("PRAHARI Documentation Validator")
    print("=" * 60)

    errors = []
    total_fail = 0

    print("\n[1/5] Checking required files exist...")
    n = check_required_files(errors)
    total_fail += n
    print(f"      {'PASS' if n == 0 else f'FAIL — {n} missing'}")

    print("[2/5] Checking metadata headers...")
    n = check_metadata(errors)
    total_fail += n
    print(f"      {'PASS' if n == 0 else f'FAIL — {n} documents missing metadata'}")

    print("[3/5] Checking SUPERSEDED documents have replacement links...")
    n = check_superseded(errors)
    total_fail += n
    print(f"      {'PASS' if n == 0 else f'FAIL — {n} SUPERSEDED docs without replacement link'}")

    print("[4/5] Checking relative Markdown links resolve...")
    n = check_relative_links(errors)
    total_fail += n
    print(f"      {'PASS' if n == 0 else f'FAIL — {n} broken links'}")

    print("[5/5] Checking for suspicious raw-path write references...")
    n = check_no_raw_path_in_docs(errors)
    total_fail += n
    print(f"      {'PASS' if n == 0 else f'WARNING — {n} suspicious references'}")

    print()
    if errors:
        print("ERRORS / WARNINGS:")
        for e in errors:
            print(f'  - {e}'.encode('ascii', 'replace').decode('ascii'))
        print()

    if total_fail == 0:
        print("RESULT: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print(f"RESULT: {total_fail} CHECK(S) FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

