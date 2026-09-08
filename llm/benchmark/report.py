"""Deterministic summary and human-review template generation."""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def build_summary(records: list[dict]) -> dict:
    latencies = [r["execution"]["latency_seconds"] for r in records if r["execution"].get("error") is None]
    sorted_latency = sorted(latencies)
    p90 = sorted_latency[min(len(sorted_latency) - 1, max(0, int(.9 * len(sorted_latency))))] if sorted_latency else None
    checks = [c for r in records for c in r.get("checks", [])]
    by_category = defaultdict(list)
    for record in records:
        by_category[record["category"]].extend(record.get("checks", []))
    return {
        "cases": len(records), "response_failures": sum(bool(r["execution"].get("error")) for r in records),
        "json_parse_failures": sum(bool(r["execution"].get("parse_error")) for r in records),
        "median_latency_seconds": statistics.median(latencies) if latencies else None, "p90_latency_seconds": p90,
        "automatic_checks_passed": sum(c["passed"] for c in checks), "automatic_checks_total": len(checks),
        "category_scores": {k: {"passed": sum(c["passed"] for c in v), "total": len(v)} for k, v in sorted(by_category.items())},
    }


def write_reports(run_dir: Path, records: list[dict]) -> None:
    (run_dir / "summary.json").write_text(json.dumps(build_summary(records), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (run_dir / "automatic_scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "category", "check", "passed", "detail"]); writer.writeheader()
        for r in records:
            for check in r.get("checks", []): writer.writerow({"case_id": r["case_id"], "category": r["category"], **check})
    with (run_dir / "human_review_template.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["case_id", "category", "groundedness_score", "clarity_score", "officer_usefulness_score", "uncertainty_handling_score", "hallucination_flag", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for r in records: writer.writerow({"case_id": r["case_id"], "category": r["category"]})
