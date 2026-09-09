from __future__ import annotations
import json, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import ROOT, get_settings
from backend.database import SessionLocal
from backend.loader import load_canonical_dataset

if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    with SessionLocal() as session:
        result=load_canonical_dataset(session,get_settings().processed_data_dir,ROOT/"data/metadata/source_manifest.csv")
    print(json.dumps(result,indent=2))
