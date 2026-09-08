"""Candidate Benchmark V1 orchestration and blinded reporting.

This module consumes the frozen Benchmark Foundation V1. It does not alter
prompts, schemas, cases, checks, or generation settings.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm.benchmark.runner import build_user_prompt, load_cases, run
from llm.service import GenerationSettings, OllamaClient

CANDIDATES = ("llama3:8b", "qwen3:8b", "gemma3:4b", "gemma3:12b")
EXPECTED_CASE_HASH = "366493644a4a0004c5198e14f1bf7ef90c8e74827509a2ffa5cde3e93fb64ed5"
BLIND_SEED = 26103
QUALITY_CATEGORIES = (
    "GROUNDED_EXPLANATION", "OFFICER_USEFULNESS", "MISSING_DATA",
    "DATA_QUALITY", "REVIEW_RECOMMENDATIONS", "RISK_VS_RELIABILITY",
)


def safe_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def verify_frozen(root: Path) -> list[Any]:
    cases, digest = load_cases(root / "llm/cases")
    if len(cases) != 65 or digest != EXPECTED_CASE_HASH:
        raise RuntimeError(f"frozen case set mismatch: count={len(cases)}, hash={digest}")
    return cases


def installed_candidates(client: OllamaClient) -> set[str]:
    return {row.get("name") or row.get("model") for row in client.list_models()} & set(CANDIDATES)


def execute_candidate(root: Path, model: str, client: OllamaClient | None = None) -> dict[str, Any]:
    if model not in CANDIDATES: raise ValueError(f"model is not an approved V1 candidate: {model}")
    cases = verify_frozen(root); client = client or OllamaClient()
    if model not in installed_candidates(client): raise RuntimeError(f"exact candidate tag not installed: {model}")
    formal_root = root / "outputs/llm/benchmark_v1/formal"
    formal_root.mkdir(parents=True, exist_ok=True)
    manifest_path = formal_root / f"{safe_name(model)}.json"
    if manifest_path.exists(): raise FileExistsError(f"formal candidate already executed: {manifest_path}")
    system = (root / "llm/prompts/system_prompt_v1.txt").read_text(encoding="utf-8")
    warmup = client.generate(model, system, build_user_prompt(cases[0]), GenerationSettings())
    warmup_path = formal_root / f"{safe_name(model)}_warmup.json"
    warmup_path.write_text(json.dumps({"scored": False, "case_id": cases[0].case_id, "execution": warmup}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run_id = "candidate_v1_" + safe_name(model) + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = run(root, model, run_id=run_id, client=client)
    manifest = {"model": model, "formal_run_dir": str(run_dir.relative_to(root)).replace("\\", "/"), "warmup_artifact": str(warmup_path.relative_to(root)).replace("\\", "/"), "formal_cases": 65, "completed_at_utc": datetime.now(timezone.utc).isoformat()}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load_records(root: Path) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    records, manifests = {}, {}
    for model in CANDIDATES:
        manifest_path = root / "outputs/llm/benchmark_v1/formal" / f"{safe_name(model)}.json"
        if not manifest_path.exists(): raise RuntimeError(f"missing formal manifest for {model}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifests[model] = manifest
        response_path = root / manifest["formal_run_dir"] / "responses.jsonl"
        model_records = [json.loads(line) for line in response_path.read_text(encoding="utf-8").splitlines() if line]
        if len(model_records) != 65 or len({r["case_id"] for r in model_records}) != 65: raise RuntimeError(f"incomplete candidate: {model}")
        records[model] = model_records
    return records, manifests


def aggregate(root: Path) -> dict[str, Any]:
    cases = verify_frozen(root); case_by_id = {c.case_id: c for c in cases}
    records_by_model, manifests = _load_records(root)
    out = root / "outputs/llm/benchmark_v1"; out.mkdir(parents=True, exist_ok=True)
    if (out / "run_metadata.json").exists():
        raise FileExistsError("Candidate Benchmark V1 aggregate already exists; immutable results are not overwritten")
    all_records, score_rows, category_rows, failure_rows, performance_rows = [], [], [], [], []
    summaries = {}
    for model, records in records_by_model.items():
        all_records.extend({"model": model, **r} for r in records)
        checks = [c for r in records for c in r["checks"]]
        by_category = defaultdict(list)
        for record in records: by_category[record["category"]].extend(record["checks"])
        critical_records = [r for r in records if case_by_id[r["case_id"]].severity == "CRITICAL"]
        critical_failed = [r for r in critical_records if not all(c["passed"] for c in r["checks"])]
        latencies = [r["execution"]["latency_seconds"] for r in records if not r["execution"].get("error")]
        token_rates = [r["execution"].get("tokens_per_second") for r in records if r["execution"].get("tokens_per_second") is not None]
        failed_types = Counter(c["check"] for r in records for c in r["checks"] if not c["passed"])
        summary = {
            "total_cases": 65, "valid_json": sum(r["execution"].get("parsed_response") is not None and not r.get("response_schema_error") for r in records),
            "automatic_checks_passed": sum(c["passed"] for c in checks), "automatic_checks_total": len(checks),
            "critical_cases_passed": len(critical_records)-len(critical_failed), "critical_cases_failed": len(critical_failed),
            "critical_failures_total": sum(not c["passed"] for r in critical_records for c in r["checks"]),
            "critical_failure_categories": sorted({r["category"] for r in critical_failed}),
            "runtime_failures": sum(bool(r["execution"].get("error")) for r in records), "json_parse_failures": sum(bool(r["execution"].get("parse_error")) for r in records),
            "median_latency_seconds": statistics.median(latencies), "p90_latency_seconds": sorted(latencies)[min(len(latencies)-1, int(.9*len(latencies)))], "mean_latency_seconds": statistics.mean(latencies),
            "median_tokens_per_second": statistics.median(token_rates) if token_rates else None, "failed_check_types": dict(sorted(failed_types.items())),
        }
        summaries[model] = summary
        performance_rows.append({"model": model, **{k: summary[k] for k in ("median_latency_seconds","p90_latency_seconds","mean_latency_seconds","median_tokens_per_second","runtime_failures","json_parse_failures")}})
        for category, category_checks in sorted(by_category.items()):
            category_rows.append({"model":model,"category":category,"checks_passed":sum(c["passed"] for c in category_checks),"checks_total":len(category_checks),"pass_rate":sum(c["passed"] for c in category_checks)/len(category_checks)})
        for record in records:
            case = case_by_id[record["case_id"]]
            for check in record["checks"]:
                score_rows.append({"model":model,"case_id":record["case_id"],"category":record["category"],"severity":case.severity,**check})
                if not check["passed"]:
                    failure_rows.append({"model":model,"case_id":record["case_id"],"category":record["category"],"severity":case.severity,"question":record["question"],"relevant_evidence":case.evidence.to_dict(),"expected_behavior":case.expected_behavior,"actual_response":record["execution"].get("raw_response"),"failed_check":check,"why_check_failed":check["detail"],"automatic_check_clearly_valid":None,"human_review_required":True})
    with (out/"responses.jsonl").open("w",encoding="utf-8",newline="\n") as h:
        for row in all_records:h.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    _write_csv(out/"automatic_scores.csv",score_rows)
    _write_csv(out/"category_scores.csv",category_rows)
    _write_csv(out/"performance.csv",performance_rows)
    with (out/"failures.jsonl").open("w",encoding="utf-8",newline="\n") as h:
        for row in failure_rows:h.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
    aliases = list("ABCD"); models = list(CANDIDATES); random.Random(BLIND_SEED).shuffle(models)
    key = {f"Model {alias}": model for alias,model in zip(aliases,models)}
    (out/"human_review_model_key.json").write_text(json.dumps({"seed":BLIND_SEED,"mapping":key},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    reverse = {model:alias for alias,model in key.items()}; review=[]
    critical_ids = [c.case_id for c in cases if c.severity=="CRITICAL"]
    rng=random.Random(BLIND_SEED); quality_ids=[]
    for category in QUALITY_CATEGORIES:
        pool=sorted(c.case_id for c in cases if c.category==category);quality_ids.extend(rng.sample(pool,2))
    for mode,ids in (("CRITICAL",critical_ids),("REPRESENTATIVE_QUALITY",quality_ids)):
        items=[]
        for model,records in records_by_model.items():
            lookup={r["case_id"]:r for r in records}
            for case_id in ids:
                r=lookup[case_id];items.append({"review_mode":mode,"anonymous_model":reverse[model],"case_id":case_id,"category":r["category"],"question":r["question"],"evidence":json.dumps(case_by_id[case_id].evidence.to_dict(),ensure_ascii=False,sort_keys=True),"response":r["execution"].get("raw_response",""),"groundedness_score":"","clarity_score":"","officer_usefulness_score":"","uncertainty_handling_score":"","hallucination_flag":"","notes":""})
        rng.shuffle(items);review.extend(items)
    _write_csv(out/"human_review_blinded.csv",review)
    metadata={"benchmark_version":"1.0.0","case_set_sha256":EXPECTED_CASE_HASH,"formal_response_count":len(all_records),"candidates":list(CANDIDATES),"manifests":manifests,"blind_seed":BLIND_SEED,"critical_review_rows":len(critical_ids)*4,"representative_review_rows":len(quality_ids)*4,"automatic_summaries":summaries,"generated_at_utc":datetime.now(timezone.utc).isoformat()}
    (out/"run_metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return metadata


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:return
    with path.open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
