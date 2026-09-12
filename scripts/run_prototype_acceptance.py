"""Non-destructive PRAHARI prototype acceptance checks; never trains or writes predictions."""
from __future__ import annotations
import json,sys
from pathlib import Path
from sqlalchemy import text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.config import get_settings
from backend.database import make_engine
from backend.main import create_app
def main():
    settings=get_settings();checks={'model_release':'WITHHELD','operational_prediction_release':False}
    required=[ROOT/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv',settings.rag_index_dir/'index_metadata.json',ROOT/'outputs/decision/officer_review_queue_summary.json']
    checks['required_artifacts']={'status':'PASS' if all(x.is_file() for x in required) else 'FAIL','missing':[str(x) for x in required if not x.is_file()]}
    try:
        with make_engine().connect() as db:checks['database']={'status':'PASS','projects':db.execute(text('select count(*) from projects')).scalar_one(),'alerts':db.execute(text('select count(*) from alerts')).scalar_one()}
    except Exception as exc:checks['database']={'status':'NOT_EXECUTED','reason':type(exc).__name__}
    paths={route.path for route in create_app(None).routes};expected={'/api/v1/health','/api/v1/projects','/api/v1/review-queue','/api/v1/assistant/query'};checks['api_contract']={'status':'PASS' if expected<=paths else 'FAIL','missing':sorted(expected-paths)}
    checks['assistant_config']={'status':'PASS' if settings.llm_enabled else 'DISABLED','rag_index':str(settings.rag_index_dir)}
    print(json.dumps(checks,indent=2));return 0 if all(x.get('status')!='FAIL' for x in checks.values() if isinstance(x,dict)) else 1
if __name__=='__main__':raise SystemExit(main())
