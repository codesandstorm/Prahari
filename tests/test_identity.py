"""
PRAHARI — tests/test_identity.py

Unit test skeletons for identity modules.

Most meaningful identity tests require multi-month extraction data.
These are structural/contract tests for the module interfaces.

Full integration tests will be added after Gate 2 extraction is complete.
"""

from __future__ import annotations

import pytest


class TestProjectLinker:

    def test_link_monthly_not_implemented(self):
        """project_linker.link_monthly_extractions must raise NotImplementedError until implemented."""
        from src.identity.project_linker import link_monthly_extractions
        with pytest.raises(NotImplementedError):
            link_monthly_extractions([])


class TestIdentityAudit:

    def test_identity_audit_not_implemented(self):
        """identity_audit.run_identity_audit must raise NotImplementedError until implemented."""
        from src.identity.identity_audit import run_identity_audit
        with pytest.raises(NotImplementedError):
            run_identity_audit(None)
