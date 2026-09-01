"""
PRAHARI — src/identity/identity_audit.py

Analyse and report on project identity resolution quality.

CURRENT STATUS: SKELETON — NOT YET IMPLEMENTED.

Planned responsibilities:
  - For each project in the extraction set, record:
    * whether project_code is present and non-null
    * whether legacy_ocms_code is present and non-null
    * whether pmgid is present and non-null
    * whether the project appears in all expected months
    * whether the project name is consistent across months
    * identity_status: RESOLVED | UNRESOLVED | AMBIGUOUS
  - Output: data/validation/identity_audit.csv
  - Output: summary statistics for docs/PROJECT_IDENTITY_ANALYSIS.md
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_identity_audit(project_month_path, output_path=None, config=None) -> None:
    """Run a full identity audit on the project_month dataset.

    NOT YET IMPLEMENTED.

    Args:
        project_month_path: Path to project_month.csv.
        output_path: Path to write identity_audit.csv.
        config: Parsed config.yaml.
    """
    raise NotImplementedError(
        "identity_audit.run_identity_audit is not yet implemented. "
        "Requires project_month.csv from at least 3 months of extraction."
    )
