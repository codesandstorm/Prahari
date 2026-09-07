import json
from pathlib import Path

import pytest

from llm.benchmark.candidate_v1 import CANDIDATES, EXPECTED_CASE_HASH, safe_name, verify_frozen

ROOT=Path(__file__).resolve().parents[1]


def test_candidate_set_is_exactly_preregistered():
    assert CANDIDATES == ("llama3:8b","qwen3:8b","gemma3:4b","gemma3:12b")


def test_frozen_case_completeness_and_hash():
    assert len(verify_frozen(ROOT))==65
    assert EXPECTED_CASE_HASH=="366493644a4a0004c5198e14f1bf7ef90c8e74827509a2ffa5cde3e93fb64ed5"


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
