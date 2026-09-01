"""
tests/conftest.py — pytest configuration for PRAHARI tests.
Adds repository root to sys.path so src/ and scripts/ are importable.
"""
import sys
from pathlib import Path

# Insert repo root at front of path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
