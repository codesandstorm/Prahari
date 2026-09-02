#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.build_twelve_month_dataset import build

if __name__ == "__main__":
    print(json.dumps(build(ROOT), indent=2, ensure_ascii=False))
