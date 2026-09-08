import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.rag.indexer import build_index
if __name__=="__main__":print(build_index(ROOT))
