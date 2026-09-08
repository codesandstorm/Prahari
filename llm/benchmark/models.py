"""Model registry is data, so later candidates require no code changes."""

from __future__ import annotations

import json
from pathlib import Path


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
