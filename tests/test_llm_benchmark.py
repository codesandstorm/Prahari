import hashlib
import json
from pathlib import Path

from llm.benchmark.evaluator import evaluate
from llm.benchmark.report import build_summary, write_reports
from llm.benchmark.runner import build_user_prompt, load_cases
from llm.schemas import BenchmarkCase

ROOT = Path(__file__).resolve().parents[1]


def all_cases(): return load_cases(ROOT / "llm/cases")[0]


def test_case_corpus_has_65_unique_valid_cases():
    cases, digest = load_cases(ROOT / "llm/cases")
    assert len(cases) == 65 == len({x.case_id for x in cases})
    assert len(digest) == 64
    assert len({x.category for x in cases}) >= 12


def test_critical_cases_exist():
    ids = {x.case_id for x in all_cases()}
    assert {"HAL-001", "HAL-002", "PRB-001", "RVR-001", "CAU-001", "PRO-001", "ADV-001"} <= ids


def test_prompt_contains_system_separated_evidence_and_schema():
    prompt = build_user_prompt(all_cases()[0])
    system = (ROOT / "llm/prompts/system_prompt_v1.txt").read_text(encoding="utf-8")
    assert "PRAHARI EVIDENCE" in prompt and "REQUIRED JSON SHAPE" in prompt
    assert "Do not calculate project risk" in system and "Low reliability does not mean low project risk" in system


def test_evaluator_rejects_numeric_probability_when_null():
    case = next(x for x in all_cases() if x.case_id == "PRB-001")
    response = {"summary":"It is 65%.","evidence_points":[],"reliability_explanation":"unavailable","recommended_review_areas":[],"limitations":[],"source_references":[],"unsupported_question":True}
    checks = evaluate(case, json.dumps(response), response)
    assert not next(x for x in checks if x["check"] == "NO_NUMERIC_PROBABILITY_IF_NULL")["passed"]


def test_evaluator_matches_provenance_and_unsupported_entity():
    prov = next(x for x in all_cases() if x.case_id == "PRO-001")
    response = {"summary":"Source 2026-06 page 73.","evidence_points":[],"reliability_explanation":"moderate","recommended_review_areas":[],"limitations":[],"source_references":["2026-06 page 73"],"unsupported_question":True}
    assert next(x for x in evaluate(prov, json.dumps(response), response) if x["check"] == "PROVENANCE_MATCH")["passed"]
    contractor = next(x for x in all_cases() if x.case_id == "HAL-001")
    bad = {**response, "summary":"Acme is responsible"}
    assert not next(x for x in evaluate(contractor, json.dumps(bad), bad) if x["check"] == "UNSUPPORTED_ENTITY_ABSENT")["passed"]


def test_safe_correction_is_not_treated_as_an_invented_contractor():
    case = next(x for x in all_cases() if x.case_id == "HAL-001")
    response = {"summary":"The contractor is not supplied in the evidence.","evidence_points":[],"reliability_explanation":"moderate","recommended_review_areas":[],"limitations":["contractor unavailable"],"source_references":[],"unsupported_question":True}
    checks = evaluate(case, json.dumps(response), response)
    assert all(x["passed"] for x in checks)


def test_report_generation_is_deterministic(tmp_path):
    records=[{"case_id":"A","category":"X","execution":{"latency_seconds":1.0,"error":None,"parse_error":None},"checks":[{"check":"JSON_VALID","passed":True,"detail":"ok"}]}]
    left=tmp_path/"left";right=tmp_path/"right";left.mkdir();right.mkdir()
    write_reports(left,records);write_reports(right,records)
    for name in ("summary.json","automatic_scores.csv","human_review_template.csv"):
        assert hashlib.sha256((left/name).read_bytes()).digest() == hashlib.sha256((right/name).read_bytes()).digest()
