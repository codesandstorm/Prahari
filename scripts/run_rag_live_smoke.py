from __future__ import annotations
import csv,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.rag.assistant import UnifiedPrahariAssistant
from llm.rag.retriever import LexicalRetriever

PROJECT={"canonical_project_id":"SYNTHETIC-RAG","project_name":"Synthetic Project","as_of_month":"2026-06","target":"S1","horizon_months":3,"prediction_status":"AVAILABLE","calibrated_probability":.72,"risk_band":"HIGH","reliability_band":"MODERATE","reliability_reasons":["Limited history"],"data_quality_status":"REVIEW","review_priority":"HIGH","contributors":["Recent progress stagnation"],"model_version":"PROTOTYPE","feature_version":"COMPACT-V2","target_version":"S1-PROVISIONAL"}
CASES=[("document_definition","What does PAIMANA stand for?",None),("document_threshold","What project cost threshold does the official Flash Report cover?",None),("mixed","Why is this project risky and what is PAIMANA?",PROJECT),("missing_cuf","What is the official CUF field schema?",None),("unsupported","Who should be punished?",PROJECT)]
def main():
    index=ROOT/"outputs/llm/rag/index/rag-v1-src-2026-06-frontmatter-p1-21";service=UnifiedPrahariAssistant(LexicalRetriever.from_index(index));rows=[]
    for case,question,project in CASES:
        result=service.answer(question,project,case);rows.append({"case_id":case,"route":result.route,"fallback":result.fallback_used,"fallback_reason":result.fallback_reason or "","retrieval_seconds":result.latency_metadata["retrieval_seconds"],"generation_seconds":result.latency_metadata["generation_seconds"],"total_seconds":result.latency_metadata["total_seconds"],"retrieved_citations":len(result.document_citations)})
    out=ROOT/"outputs/llm/rag";
    with (out/"live_smoke_results.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    med=lambda key:statistics.median([x[key] for x in rows])
    summary={"model":"llama3:8b","cases":len(rows),"fallbacks":sum(x["fallback"] for x in rows),"median_retrieval_seconds":med("retrieval_seconds"),"median_generation_seconds":med("generation_seconds"),"median_total_seconds":med("total_seconds"),"scope":"warmed local RAG smoke; prototype hardware only"}
    (out/"live_smoke_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
