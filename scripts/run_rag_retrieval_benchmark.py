import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.rag.benchmark import run_retrieval_benchmark
if __name__=="__main__":print(json.dumps(run_retrieval_benchmark(ROOT,ROOT/"outputs/llm/rag/index/rag-v1-src-2026-06-frontmatter-p1-21"),indent=2))
