"""Build the controlled April-May-June 2026 longitudinal pilot."""

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.pipeline.build_three_month_pilot import build_three_month_pilot

if __name__ == "__main__":
    print(json.dumps(build_three_month_pilot(ROOT),indent=2,ensure_ascii=False))
