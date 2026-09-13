"""Leakage-safe, origin-isolated Peer Benchmarking V1 service."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from statistics import fmean, median

from .contracts import BenchmarkMetric, BenchmarkMode, BenchmarkResult, BenchmarkStatus

ROOT = Path(__file__).resolve().parents[2]


def _policy() -> dict:
    return json.loads((ROOT / "config" / "benchmark_policy.json").read_text(encoding="utf-8"))


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def cost_band(value: float | None) -> str:
    if not _finite(value) or float(value) < 0:
        return "UNKNOWN"
    value = float(value)
    if value < 150: return "BELOW_150_CR"
    if value < 500: return "150_TO_500_CR"
    if value < 1000: return "500_TO_1000_CR"
    if value < 5000: return "1000_TO_5000_CR"
    return "5000_CR_AND_ABOVE"


def lifecycle_band(approval_date: date | None, completion_date: date | None, as_of: date) -> str:
    if approval_date is None or completion_date is None or completion_date <= approval_date:
        return "UNKNOWN"
    total = (completion_date.year - approval_date.year) * 12 + completion_date.month - approval_date.month
    elapsed = (as_of.year - approval_date.year) * 12 + as_of.month - approval_date.month
    ratio = elapsed / total
    if ratio <= .25: return "EARLY"
    if ratio <= .75: return "MID"
    if ratio <= 1: return "LATE"
    return "OVERDUE"


@dataclass(frozen=True)
class BenchmarkRecord:
    canonical_project_id: str
    as_of_month: str
    data_origin: str
    sector: str | None
    cost_band: str
    lifecycle_band: str
    metrics: dict[str, float | None] = field(default_factory=dict)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1: return ordered[0]
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def _percentile(values: list[float], value: float) -> float:
    lower = sum(x < value for x in values)
    equal = sum(x == value for x in values)
    return round(100 * (lower + .5 * equal) / len(values), 2)


class PeerBenchmarkService:
    """Select supported peers once and calculate transparent descriptive statistics."""

    def __init__(self, records: list[BenchmarkRecord]):
        self.records = tuple(records)
        self.policy = _policy()

    def _eligible_pool(self, subject: BenchmarkRecord, mode: BenchmarkMode) -> list[BenchmarkRecord]:
        expected = "SYNTHETIC_CUF_PROTOTYPE" if mode == BenchmarkMode.SYNTHETIC_SANDBOX else "HISTORICAL_FLASH_REPORT"
        if subject.data_origin != expected:
            raise ValueError("benchmark mode and subject data_origin disagree")
        pool = [r for r in self.records if r.data_origin == expected]
        if mode == BenchmarkMode.REAL_HISTORICAL_AS_OF:
            pool = [r for r in pool if r.as_of_month <= subject.as_of_month]
            # one contemporaneous or last-known record per project, never a future record
            latest: dict[str, BenchmarkRecord] = {}
            for row in sorted(pool, key=lambda x: x.as_of_month): latest[row.canonical_project_id] = row
            pool = list(latest.values())
        else:
            pool = [r for r in pool if r.as_of_month == subject.as_of_month]
        if self.policy["exclude_subject_from_peers"]:
            pool = [r for r in pool if r.canonical_project_id != subject.canonical_project_id]
        return pool

    def benchmark(self, subject: BenchmarkRecord, mode: BenchmarkMode) -> BenchmarkResult:
        pool = self._eligible_pool(subject, mode)
        chosen, definition, level = [], {}, None
        unavailable_dimensions = []
        for idx, dimensions in enumerate(self.policy["fallback_hierarchy"], 1):
            if any(getattr(subject, d) in (None, "", "UNKNOWN") for d in dimensions):
                unavailable_dimensions.extend(d for d in dimensions if getattr(subject, d) in (None, "", "UNKNOWN")); continue
            candidate = [r for r in pool if all(getattr(r, d) == getattr(subject, d) for d in dimensions)]
            if len(candidate) >= self.policy["minimum_peer_count"]:
                chosen, definition, level = candidate, {d: str(getattr(subject, d)) for d in dimensions}, idx
                break
        limitations = []
        if subject.sector in (None, "", "UNKNOWN"):
            limitations.append("BENCHMARK_SECTOR_UNKNOWN: sector was not inferred; a supported fallback group was used when possible.")
        if level == 4:
            limitations.append("Portfolio-wide fallback used because no more specific group met minimum support.")
        if len(chosen) < self.policy["preferred_peer_count"]:
            limitations.append(f"Peer group has {len(chosen)} records; preferred support is {self.policy['preferred_peer_count']}.")
        group_label = " + ".join(f"{k}={v}" for k, v in definition.items()) or "PORTFOLIO_WIDE"
        metrics = []
        for name, direction in self.policy["metrics"].items():
            project_value = subject.metrics.get(name)
            values = [float(r.metrics[name]) for r in chosen if _finite(r.metrics.get(name))]
            if not _finite(project_value):
                status, stats = BenchmarkStatus.FIELD_UNAVAILABLE, (None,) * 5
            elif len(values) < self.policy["minimum_peer_count"]:
                status, stats = BenchmarkStatus.INSUFFICIENT_PEERS, (None,) * 5
            else:
                status = BenchmarkStatus.SYNTHETIC if mode == BenchmarkMode.SYNTHETIC_SANDBOX else BenchmarkStatus.AVAILABLE
                stats = (round(median(values), 4), round(fmean(values), 4), round(_quantile(values, .25), 4), round(_quantile(values, .75), 4), _percentile(values, float(project_value)))
            p50, mean, p25, p75, percentile = stats
            interpretation = None
            if percentile is not None and direction in {"HIGHER_WORSE", "LOWER_WORSE"}:
                adverse = percentile if direction == "HIGHER_WORSE" else 100 - percentile
                interpretation = "MORE_ADVERSE_THAN_MOST_PEERS" if adverse >= 75 else "WITHIN_PEER_INTERQUARTILE_CONTEXT" if 25 <= percentile <= 75 else "LESS_ADVERSE_THAN_MOST_PEERS"
            metrics.append(BenchmarkMetric(metric=name, project_value=float(project_value) if _finite(project_value) else None, peer_median=p50, peer_mean=mean, peer_p25=p25, peer_p75=p75, percentile=percentile, peer_count=len(values), peer_group_definition=group_label, benchmark_status=status, data_origin=subject.data_origin, directionality=direction, interpretation=interpretation))
        overall_count = len(chosen)
        if not chosen: limitations.append("BENCHMARK_INSUFFICIENT_PEERS: no governed fallback group met minimum support.")
        overall_status=BenchmarkStatus.INSUFFICIENT_PEERS if not chosen else BenchmarkStatus.SYNTHETIC if mode==BenchmarkMode.SYNTHETIC_SANDBOX else BenchmarkStatus.AVAILABLE
        return BenchmarkResult(canonical_project_id=subject.canonical_project_id, as_of_month=subject.as_of_month, mode=mode, peer_group=definition, peer_group_level=level, peer_count=overall_count, benchmark_status=overall_status, metrics=metrics, limitations=list(dict.fromkeys(limitations)), data_origin=subject.data_origin)
