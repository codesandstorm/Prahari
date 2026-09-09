import json
from dataclasses import asdict
from pathlib import Path

import pytest

from llm.benchmark.candidate_v1 import CANDIDATES, EXPECTED_CASE_HASH, safe_name, verify_frozen

ROOT=Path(__file__).resolve().parents[1]


def test_candidate_set_is_exactly_preregistered():
    assert CANDIDATES == ("llama3:8b","qwen3:8b","gemma3:4b","gemma3:12b")


def test_frozen_case_completeness_and_hash():
    assert len(verify_frozen(ROOT))==65
    assert EXPECTED_CASE_HASH=="366493644a4a0004c5198e14f1bf7ef90c8e74827509a2ffa5cde3e93fb64ed5"


def test_frozen_hash_is_stable_across_lf_and_crlf(tmp_path):
    from llm.benchmark.runner import load_cases
    source=ROOT/"llm/cases"
    lf=tmp_path/"lf";crlf=tmp_path/"crlf";lf.mkdir();crlf.mkdir()
    for path in source.glob("*.jsonl"):
        content=path.read_bytes().replace(b"\r\n",b"\n")
        (lf/path.name).write_bytes(content)
        (crlf/path.name).write_bytes(content.replace(b"\n",b"\r\n"))
    lf_cases,lf_hash=load_cases(lf);crlf_cases,crlf_hash=load_cases(crlf)
    assert [asdict(x) for x in lf_cases]==[asdict(x) for x in crlf_cases]
    assert lf_hash==crlf_hash==EXPECTED_CASE_HASH


def test_safe_name_is_filesystem_safe():
    assert safe_name("gemma3:12b")=="gemma3_12b"


def test_preregistration_precedes_formal_manifests():
    prereg=ROOT/"docs/llm/PRAHARI_LLM_BENCHMARK_V1_PREREGISTRATION.md"
    assert prereg.exists() and EXPECTED_CASE_HASH in prereg.read_text(encoding="utf-8")


def test_model_key_is_not_a_column_in_blinded_sheet_if_outputs_exist():
    sheet=ROOT/"outputs/llm/benchmark_v1/human_review_blinded.csv"
    if sheet.exists():
        header=sheet.read_text(encoding="utf-8").splitlines()[0]
        assert "model_name" not in header and "anonymous_model" in header


def test_completed_aggregate_is_immutable():
    from llm.benchmark.candidate_v1 import aggregate
    if (ROOT/"outputs/llm/benchmark_v1/run_metadata.json").exists():
        with pytest.raises(FileExistsError, match="not overwritten"):
            aggregate(ROOT)
