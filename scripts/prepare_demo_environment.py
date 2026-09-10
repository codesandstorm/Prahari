"""Read-only PRAHARI demo readiness and llama3:8b warm-up."""
from __future__ import annotations
import json,sys,time
from pathlib import Path
from sqlalchemy import text
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.config import get_settings
from backend.database import make_engine
from llm.service.ollama_client import GenerationSettings,OllamaClient
def main():
    result={};settings=get_settings()
    try:
        with make_engine().connect() as db:result['postgresql']={'status':'PASS','projects':db.execute(text('select count(*) from projects')).scalar_one(),'alerts':db.execute(text('select count(*) from alerts')).scalar_one()}
    except Exception as exc:result['postgresql']={'status':'FAIL','reason':type(exc).__name__}
    result['rag_index']={'status':'PASS' if (settings.rag_index_dir/'index_metadata.json').is_file() else 'FAIL','path':str(settings.rag_index_dir)}
    client=OllamaClient(timeout_seconds=30);started=time.perf_counter()
    try:
        names={x['name'] for x in client.list_models()};available=any(x.split(':')[0]=='llama3' for x in names)
        warmed=client.generate('llama3:8b','Return JSON only.','Return {"ready":true}.',GenerationSettings(num_predict=12,temperature=0,seed=42,top_p=.9)) if available else {'error':'model unavailable'}
        result['ollama']={'status':'PASS' if available and not warmed.get('error') else 'FAIL','model':'llama3:8b','warmup_seconds':round(time.perf_counter()-started,3)}
    except Exception as exc:result['ollama']={'status':'FAIL','reason':type(exc).__name__}
    result['model_release']='WITHHELD';result['writes_performed']=False;print(json.dumps(result,indent=2));return 0 if all(v.get('status')=='PASS' for v in (result['postgresql'],result['rag_index'],result['ollama'])) else 1
if __name__=='__main__':raise SystemExit(main())
