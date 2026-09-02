"""Run the controlled April 2026 Table 6 extraction."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.extractor_paimana_april import extract_april_2026_table6

if __name__ == "__main__":
    print(json.dumps(extract_april_2026_table6(ROOT), indent=2, ensure_ascii=False))
