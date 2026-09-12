"""Validate V2 human review completeness and immutable evidence fields."""
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.ml.prediction_research_v2 import read_csv,validate_transfer_rows

base=ROOT/"validation/historical_target_transfer_v2"
rows=read_csv(base/"historical_target_transfer_v2.csv")
manifest=json.loads((base/"manifest.json").read_text(encoding="utf-8"))
errors=validate_transfer_rows(rows,manifest)
reviewed=sum(bool(row.get("manual_label","").strip()) for row in rows)
if errors:
    print("FAIL"); print("\n".join(errors)); raise SystemExit(1)
print(f"PASS — evidence intact; {reviewed}/{len(rows)} human reviews complete")
