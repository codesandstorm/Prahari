"""CLI runner for immutable, model-independent Ollama benchmark runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from llm.benchmark.evaluator import evaluate
from llm.benchmark.report import write_reports
from llm.schemas import BenchmarkCase, PrahariResponse
from llm.service import GenerationSettings, OllamaClient

BENCHMARK_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
PROMPT_VERSION = "system_prompt_v1"


def load_cases(case_dir: Path) -> tuple[list[BenchmarkCase], str]:
    files = sorted(case_dir.glob("*.jsonl"))
    digest = hashlib.sha256()
    cases, seen = [], set()
    for path in files:
        content = path.read_bytes()
        # Candidate V1 was frozen from a Windows checkout. Hash a canonical
        # CRLF representation so Git's LF checkout on Linux has the same
        # byte identity without changing any case content or expected hash.
        canonical = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", b"\r\n")
        digest.update(path.name.encode()); digest.update(canonical)
        for line_number, line in enumerate(content.decode("utf-8").splitlines(), 1):
            if not line.strip(): continue
            case = BenchmarkCase.from_dict(json.loads(line))
            if case.case_id in seen: raise ValueError(f"duplicate case_id {case.case_id} at {path}:{line_number}")
            seen.add(case.case_id); cases.append(case)
    if not cases: raise ValueError("no benchmark cases found")
    return cases, digest.hexdigest()


def build_user_prompt(case: BenchmarkCase) -> str:
    schema = {"summary": "string", "evidence_points": ["string"], "reliability_explanation": "string", "recommended_review_areas": ["string"], "limitations": ["string"], "source_references": ["string"], "unsupported_question": False}
    return "PRAHARI EVIDENCE:\n" + json.dumps(case.evidence.to_dict(), ensure_ascii=False, sort_keys=True) + "\n\nOFFICER QUESTION:\n" + case.question + "\n\nREQUIRED JSON SHAPE:\n" + json.dumps(schema, sort_keys=True)


def run(root: Path, model: str, case_ids: set[str] | None = None, run_id: str | None = None, client: OllamaClient | None = None) -> Path:
    cases, case_hash = load_cases(root / "llm/cases")
    if case_ids: cases = [c for c in cases if c.case_id in case_ids]
    if not cases: raise ValueError("case selection is empty")
    system = (root / "llm/prompts/system_prompt_v1.txt").read_text(encoding="utf-8")
    settings = GenerationSettings(); client = client or OllamaClient()
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = root / "outputs/llm/benchmark" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    metadata = {"benchmark_version": BENCHMARK_VERSION, "schema_version": SCHEMA_VERSION, "system_prompt_version": PROMPT_VERSION, "system_prompt_sha256": hashlib.sha256(system.encode()).hexdigest(), "case_set_sha256": case_hash, "model_name": model, "generation_settings": asdict(settings), "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(), "hardware_note": "Latency is local-machine-specific and is not universal."}
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    records = []
    with (run_dir / "responses.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            execution = client.generate(model, system, build_user_prompt(case), settings)
            parsed = execution.get("parsed_response")
            schema_error = None
            if parsed is not None:
                try: PrahariResponse.from_dict(parsed)
                except ValueError as exc: schema_error = str(exc)
            record = {"case_id": case.case_id, "category": case.category, "question": case.question, "execution": execution, "response_schema_error": schema_error, "checks": evaluate(case, execution.get("raw_response", ""), parsed)}
            records.append(record); handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    write_reports(run_dir, records)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PRAHARI Ollama benchmark")
    parser.add_argument("--model", required=True); parser.add_argument("--case-id", action="append")
    args = parser.parse_args(); root = Path(__file__).resolve().parents[2]
    print(run(root, args.model, set(args.case_id or [])))


if __name__ == "__main__": main()
