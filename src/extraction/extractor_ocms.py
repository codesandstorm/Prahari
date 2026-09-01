"""
PRAHARI — src/extraction/extractor_ocms.py

Skeleton extractor for OCMS-era Flash Reports (approx. 2010–2023).

CURRENT STATUS: SKELETON — NOT YET IMPLEMENTED.

This module will be implemented after:
  1. At least one OCMS-era PDF has been placed in data/raw/<year>/
  2. pdf_inspector.py has been run and confirmed text-extractable
  3. schema_detector.py has confirmed OCMS schema
  4. Manual inspection has identified project-table structure in that era

OCMS-era reports differ from PAIMANA reports in at least the following ways
(PLAUSIBLE — not yet verified):
  - No "Project Code" column (or different identifier)
  - Different column headers for cost and date fields
  - Different section/table labels
  - May include report-level aggregates as prominent tables

Planned responsibilities mirror extractor_paimana.py but adapted for OCMS schema.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OcmsExtractor:
    """Extractor for OCMS-era Flash Reports. NOT YET IMPLEMENTED."""

    def __init__(self, pdf_path: Path, reporting_month: str, config: dict | None = None):
        raise NotImplementedError(
            "OcmsExtractor is not yet implemented. "
            "OCMS-era schema must be verified against actual PDFs first."
        )

    def extract_ongoing(self):
        raise NotImplementedError

    def extract_completed(self):
        raise NotImplementedError
