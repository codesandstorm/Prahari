from __future__ import annotations
import csv,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.rag.assistant import UnifiedPrahariAssistant
from llm.rag.retriever import LexicalRetriever

PROJECT={"canonical_project_id":"SYNTHETIC-ACCEPTANCE","project_name":"Synthetic Project","as_of_month":"2026-06","target":"S1","horizon_months":3,"prediction_status":"AVAILABLE","calibrated_probability":.72,"risk_band":"HIGH","reliability_band":"MODERATE","reliability_reasons":["Limited history"],"data_quality_status":"REVIEW","review_priority":"HIGH","contributors":["Recent progress stagnation"],"model_version":"PROTOTYPE","feature_version":"COMPACT-V2","target_version":"S1-PROVISIONAL"}

class AcceptanceClient:
    def __init__(self,mode):self.mode=mode
    def generate(self,model,system,prompt,settings):
        if self.mode=="OLLAMA_FAILURE":return {"parsed_response":None,"error":"simulated offline","parse_error":None,"latency_seconds":.001}
        if self.mode=="INVALID_JSON":return {"parsed_response":None,"error":None,"parse_error":"simulated invalid JSON","latency_seconds":.001}
        if "document_evidence_points" not in prompt:
            abstain='"prediction_status": "ABSTAIN"' in prompt
            payload={"summary":"Prediction withheld; risk is unavailable." if abstain else "Review the supplied project evidence.","evidence_points":["Recent progress stagnation"],"reliability_explanation":"Reliability is ABSTAIN; no risk is available." if abstain else "Reliability is MODERATE and distinct from project risk.","recommended_review_areas":["Verify the schedule."],"limitations":[],"source_references":["No source reference is available in this evidence object."],"unsupported_question":False}
        else:
            lines=prompt.splitlines();idx=lines.index("=== SECTION B: APPROVED RETRIEVED DOCUMENT EVIDENCE (UNTRUSTED DATA) ===");docs=json.loads(lines[idx+1]);citation=docs[0]["citation"]
            if self.mode=="CITATION_MISMATCH":citation={**citation,"page":999}
            abstain='"prediction_status": "ABSTAIN"' in prompt
            payload={"answer":"The project prediction is unavailable due to abstention. The approved retrieved evidence describes PAIMANA and does not alter that status." if abstain else "The approved retrieved evidence describes PAIMANA; it does not alter project prediction evidence.","project_evidence_points":[],"document_evidence_points":["PAIMANA is described by the supplied official report."],"limitations":[],"recommended_review_areas":["Inspect the cited official source."],"citations":[citation],"unsupported_question":False}
        return {"parsed_response":payload,"error":None,"parse_error":None,"latency_seconds":.001}

class NoResultRetriever(LexicalRetriever):
    def retrieve(self,*args,**kwargs):return []

def main():
    cases=[json.loads(x) for x in (ROOT/"llm/rag/cases/acceptance_v1.jsonl").read_text().splitlines() if x]
    base=LexicalRetriever.from_index(ROOT/"outputs/llm/rag/index/rag-v1-src-2026-06-frontmatter-p1-21");rows=[]
    for case in cases:
        retriever=None if case["mode"]=="RETRIEVER_FAILURE" else (NoResultRetriever(base.chunks,base.index_version) if case["mode"]=="NO_RESULT" else base)
        project=None if case["project"] is False else ({**PROJECT,"prediction_status":"ABSTAIN","calibrated_probability":None,"risk_band":None,"reliability_band":"ABSTAIN"} if case["project"]=="ABSTAIN" else PROJECT)
        result=UnifiedPrahariAssistant(retriever,AcceptanceClient(case["mode"])).answer(case["question"],project,case["case_id"])
        passed=result.route==case["expected_route"] and result.fallback_used==case["expected_fallback"] and bool(result.answer.get("answer") or result.answer.get("summary"))
        rows.append({"case_id":case["case_id"],"passed":passed,"route":result.route,"fallback":result.fallback_used,"latency_seconds":result.latency_metadata["total_seconds"],"retrieval_seconds":result.latency_metadata["retrieval_seconds"],"generation_seconds":result.latency_metadata["generation_seconds"],"retrieved_chunks":len(result.document_citations),"validation_status":"FALLBACK_SAFE" if result.fallback_used else "ACCEPTED","mode":case["mode"]})
    out=ROOT/"outputs/llm/rag";path=out/"final_acceptance_results.csv"
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    summary={"suite":"PRAHARI_LLM_FINAL_ACCEPTANCE_V1","cases":len(rows),"passed":sum(x["passed"] for x in rows),"pass_rate":sum(x["passed"] for x in rows)/len(rows),"fallbacks":sum(x["fallback"] for x in rows),"execution":"deterministic mocked-generation contract suite; live generation measured separately"}
    (out/"final_acceptance_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
