"""Small live Ollama integration suite; this is not the frozen candidate benchmark."""
from __future__ import annotations
import csv, json, statistics, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from llm.service.assistant import PrahariAssistant

BASE={"canonical_project_id":"SYNTHETIC-001","project_name":"Synthetic Project","as_of_month":"2026-06",
      "target":"S1","horizon_months":3,"prediction_status":"AVAILABLE","calibrated_probability":.72,
      "risk_band":"HIGH","reliability_band":"MODERATE","reliability_reasons":["Limited history"],
      "data_quality_status":"REVIEW","review_priority":"HIGH","contributors":["Recent progress stagnation"],
      "trajectory_summary":"Reported physical progress was unchanged for two observations.",
      "source_provenance":[{"source_id":"SYNTHETIC-SOURCE","page":1}],"model_version":"PROTOTYPE",
      "feature_version":"COMPACT-V2","target_version":"S1-PROVISIONAL"}
CASES=[("flagged","Why was this project flagged?",{}),
       ("reliability","Why is reliability moderate?",{}),
       ("provenance","What source supports this?",{}),
       ("unsupported","Which contractor caused this?",{}),
       ("abstain","What is the risk percentage?",{"prediction_status":"ABSTAIN","calibrated_probability":None,"risk_band":None,"reliability_band":"ABSTAIN","abstention_reason":"INSUFFICIENT_HISTORY"})]

def main():
    assistant=PrahariAssistant(); rows=[]
    for case,question,updates in CASES:
        result=assistant.explain({**BASE,**updates},question)
        rows.append({"case":case,"model":result.model,"latency_seconds":result.latency_seconds,
                     "used_fallback":result.used_fallback,"fallback_reason":result.fallback_reason or ""})
    path=ROOT/"outputs/llm/prototype_llama3_8b";path.mkdir(parents=True,exist_ok=True)
    with (path/"integration_latency.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    latencies=[r["latency_seconds"] for r in rows if r["latency_seconds"] is not None]
    summary={"model":"llama3:8b","cases":len(rows),"median_latency_seconds":statistics.median(latencies),
             "max_latency_seconds":max(latencies),"fallbacks":sum(r["used_fallback"] for r in rows),
             "scope":"prototype integration smoke; not Candidate Benchmark V1"}
    (path/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
