from __future__ import annotations
import csv,json,time
from pathlib import Path
from .retriever import LexicalRetriever

def run_retrieval_benchmark(root:Path,index:Path)->dict:
    cases=[json.loads(x) for x in (root/"llm/rag/cases/retrieval_v1.jsonl").read_text(encoding="utf-8").splitlines() if x]
    retriever=LexicalRetriever.from_index(index);rows=[];reciprocal=[]
    for case in cases:
        start=time.perf_counter();hits=retriever.retrieve(case["question"],5);latency=time.perf_counter()-start
        rank=next((i for i,(_,c) in enumerate(hits,1) if c.document_id==case["expected_document_id"] and c.page_start==case["expected_page"]),None)
        reciprocal.append(1/rank if rank else 0)
        rows.append({"case_id":case["case_id"],"expected_document_id":case["expected_document_id"],"expected_page":case["expected_page"],"rank":rank or "","recall_at_1":bool(rank and rank<=1),"recall_at_3":bool(rank and rank<=3),"recall_at_5":bool(rank and rank<=5),"no_result":not hits,"wrong_document_top1":bool(hits and hits[0][1].document_id!=case["expected_document_id"]),"wrong_page_top1":bool(hits and hits[0][1].page_start!=case["expected_page"]),"latency_seconds":latency,"retrieved_chunk_ids":"|".join(c.chunk_id for _,c in hits)})
    out=root/"outputs/llm/rag/retrieval_benchmark.csv"
    with out.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    summary={"cases":len(rows),"recall_at_1":sum(x["recall_at_1"] for x in rows)/len(rows),"recall_at_3":sum(x["recall_at_3"] for x in rows)/len(rows),"recall_at_5":sum(x["recall_at_5"] for x in rows)/len(rows),"mrr":sum(reciprocal)/len(rows),"no_result_cases":sum(x["no_result"] for x in rows),"wrong_document_top1":sum(x["wrong_document_top1"] for x in rows),"wrong_page_top1":sum(x["wrong_page_top1"] for x in rows),"median_retrieval_seconds":sorted(x["latency_seconds"] for x in rows)[len(rows)//2]}
    (root/"outputs/llm/rag/retrieval_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");return summary
