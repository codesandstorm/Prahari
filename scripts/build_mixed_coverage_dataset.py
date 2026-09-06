"""CLI for the Gate 2 mixed-coverage dataset builder."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.build_mixed_coverage_dataset import build

if __name__ == "__main__":
    print(json.dumps(build(ROOT), indent=2, default=str))
