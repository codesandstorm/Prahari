"""
PRAHARI — src/identity/project_linker.py

Link project records across monthly reports using available identifiers.

CURRENT STATUS: SKELETON — NOT YET IMPLEMENTED.

This module will be implemented after:
  1. At least three months of extracted data exist (May, June, July 2026).
  2. Project Code stability has been verified (see docs/PROJECT_IDENTITY_ANALYSIS.md Q1).
  3. Legacy OCMS Code completeness has been measured (Q4).
  4. PMGID completeness has been measured (Q5).

Planned approach (subject to evidence):
  Step 1: Use Project Code as primary identity key where present.
  Step 2: Use Legacy OCMS Code to bridge OCMS-era records where Project Code absent.
  Step 3: Mark all unresolvable identities as UNRESOLVED — do NOT auto-merge.

IMPORTANT CONSTRAINTS:
  - Do NOT perform uncontrolled fuzzy name matching.
  - Do NOT silently merge records with ambiguous identity.
  - Every resolution decision must be logged with rationale.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def link_monthly_extractions(
    extraction_paths: list[Path],
    config: dict | None = None,
) -> None:
    """Link project records across multiple monthly extraction CSVs.

    NOT YET IMPLEMENTED.

    Args:
        extraction_paths: List of paths to monthly extraction CSVs.
        config: Parsed config.yaml dict.
    """
    raise NotImplementedError(
        "project_linker.link_monthly_extractions is not yet implemented. "
        "Prerequisites: at least 3 months of extracted data + identity Q1–Q5 answered. "
        "See docs/PROJECT_IDENTITY_ANALYSIS.md"
    )
