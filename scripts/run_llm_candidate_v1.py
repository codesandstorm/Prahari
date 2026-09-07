import argparse
import json
from pathlib import Path

from llm.benchmark.candidate_v1 import aggregate, execute_candidate

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
group=parser.add_mutually_exclusive_group(required=True)
group.add_argument("--model")
group.add_argument("--aggregate",action="store_true")
args=parser.parse_args()
result=aggregate(ROOT) if args.aggregate else execute_candidate(ROOT,args.model)
print(json.dumps(result,indent=2))
