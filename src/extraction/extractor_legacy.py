"""
PRAHARI — src/extraction/extractor_legacy.py

Skeleton extractor for LEGACY-era Flash Reports (pre-OCMS / early OCMS, ≈ pre-2010).

CURRENT STATUS: SKELETON — NOT YET IMPLEMENTED.

This module will be implemented after:
  1. June 2005 PDF (or other LEGACY-era report) has been placed in data/raw/2005/
  2. pdf_inspector.py has been run
  3. schema_detector.py has confirmed LEGACY schema
  4. Manual inspection has characterised the table structure

LEGACY-era reports are likely the most structurally different from modern reports.
They may use different abbreviations (DOA, DOC), may lack physical progress fields,
and almost certainly lack Project Code / PMGID identifiers.

These reports are SCHEMA REFERENCE ONLY in the initial phase.
Do not attempt automatic extraction until schema is understood.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LegacyExtractor:
    """Extractor for LEGACY-era Flash Reports. NOT YET IMPLEMENTED."""

    def __init__(self, pdf_path: Path, reporting_month: str, config: dict | None = None):
        raise NotImplementedError(
            "LegacyExtractor is not yet implemented. "
            "LEGACY-era schema must be manually characterised first."
        )

    def extract_ongoing(self):
        raise NotImplementedError
