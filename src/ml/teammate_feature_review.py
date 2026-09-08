"""Independent, as-of-time review of proposed teammate features.

This module deliberately extends (and never redefines) the frozen Compact V2
cohort.  Every temporal descriptor is calculated from observations at or before
the anchor month.  Missing history remains missing rather than being invented.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.ml.feature_discovery_v2 import COMPACT_V2, advanced_features, evaluate_variant, metrics
from src.ml.provisional_research import SEED, build_s1_cohort, month_index, number, read_csv, split_name, value, write_csv

PROGRESS_CHANGEPOINT = (
    "progress_months_since_changepoint", "progress_changepoint_direction",
    "progress_changepoint_magnitude",
)
EXPENDITURE_CHANGEPOINT = (
    "expenditure_months_since_changepoint", "expenditure_changepoint_direction",
    "expenditure_changepoint_magnitude",
)
RECOVERY = (
    "prior_stall_count", "recovered_stall_count", "bounce_back_rate",
    "median_recovery_months", "persistent_stall_fraction",
)
PEER = ("peer_velocity_percentile", "peer_velocity_deviation", "peer_group_size")
EXPENDITURE_LAG = ("historical_exp_progress_lag_corr", "historical_exp_progress_lag_slope")


def _finite(x: float) -> bool:
    return bool(np.isfinite(x))


def _series(history: list[dict[str, str]], raw: str, fallback: str) -> list[tuple[int, float]]:
    return [(month_index(r["reporting_month"]), number(value(r, raw, fallback))) for r in history]


def _velocities(series: list[tuple[int, float]]) -> list[tuple[int, int, float]]:
    result = []
    for (li, left), (ri, right) in zip(series, series[1:]):
        if _finite(left) and _finite(right) and ri > li:
            result.append((li, ri, (right - left) / (ri - li)))
    return result


def changepoint_features(series: list[tuple[int, float]]) -> tuple[float, float, float]:
    """Past-only deterministic mean-shift, requiring two intervals per side."""
    velocities = _velocities(series)
    if len(velocities) < 4:
        return math.nan, math.nan, math.nan
    candidates = []
    for split in range(2, len(velocities) - 1):
        pre = np.array([x[2] for x in velocities[:split]], dtype=float)
        post = np.array([x[2] for x in velocities[split:]], dtype=float)
        delta = float(post.mean() - pre.mean())
        strength = abs(delta) * math.sqrt(len(pre) * len(post) / len(velocities))
        candidates.append((strength, split, delta))
    strength, split, delta = max(candidates, key=lambda x: (x[0], x[1]))
    noise = float(np.std([x[2] for x in velocities]))
    # A small absolute floor prevents tiny rounding changes becoming "events".
    if abs(delta) < max(0.5, noise):
        return math.nan, 0.0, math.nan
    change_month = velocities[split][0]
    months_since = float(series[-1][0] - change_month)
    direction = 1.0 if delta > 0.25 else -1.0 if delta < -0.25 else 0.0
    return months_since, direction, abs(delta)


def recovery_features(progress: list[tuple[int, float]]) -> dict[str, float]:
    """Count stalls whose two-calendar-month recovery window is fully observed."""
    intervals = _velocities(progress)
    resolved: list[tuple[bool, float]] = []
    for i, (_, stall_end, velocity) in enumerate(intervals):
        if velocity > 0.1:
            continue
        later = [(end, v) for _, end, v in intervals[i + 1:] if end - stall_end <= 2]
        window_complete = progress[-1][0] - stall_end >= 2
        if not window_complete:
            continue
        recovery = next(((end - stall_end) for end, v in later if v > 0.5), None)
        resolved.append((recovery is not None, float(recovery) if recovery is not None else math.nan))
    stalls = len(resolved)
    recovered = sum(flag for flag, _ in resolved)
    times = [time for flag, time in resolved if flag]
    sufficient = stalls >= 2
    return {
        "prior_stall_count": float(stalls),
        "recovered_stall_count": float(recovered),
        "bounce_back_rate": recovered / stalls if sufficient else math.nan,
        "median_recovery_months": float(np.median(times)) if sufficient and times else math.nan,
        "persistent_stall_fraction": (stalls - recovered) / stalls if sufficient else math.nan,
    }


def expenditure_lag_features(progress: list[tuple[int, float]], expenditure: list[tuple[int, float]]) -> dict[str, float]:
    """Past-only association between prior spend velocity and current progress."""
    pv = _velocities(progress)
    ev = _velocities(expenditure)
    progress_by_end = {end: velocity for _, end, velocity in pv}
    exp_by_end = {end: velocity for _, end, velocity in ev}
    pairs = []
    for progress_end, progress_velocity in progress_by_end.items():
        previous_exp = exp_by_end.get(progress_end - 1)
        if previous_exp is not None:
            pairs.append((previous_exp, progress_velocity))
    if len(pairs) < 4:
        return {"historical_exp_progress_lag_corr": math.nan, "historical_exp_progress_lag_slope": math.nan}
    x, y = np.array(pairs, dtype=float).T
    if np.std(x) <= 1e-9 or np.std(y) <= 1e-9:
        corr = math.nan
    else:
        corr = float(np.corrcoef(x, y)[0, 1])
    slope = float(np.cov(x, y, ddof=0)[0, 1] / np.var(x)) if np.var(x) > 1e-9 else math.nan
    return {"historical_exp_progress_lag_corr": corr, "historical_exp_progress_lag_slope": slope}


def teammate_features(history: list[dict[str, str]]) -> dict[str, float]:
    progress = _series(history, "physical_progress_raw", "reported_physical_progress")
    expenditure = _series(history, "cumulative_expenditure_raw", "reported_cumulative_expenditure")
    p_cp = changepoint_features(progress)
    e_cp = changepoint_features(expenditure)
    return {
        "progress_months_since_changepoint": p_cp[0],
        "progress_changepoint_direction": p_cp[1],
        "progress_changepoint_magnitude": p_cp[2],
        "expenditure_months_since_changepoint": e_cp[0],
        "expenditure_changepoint_direction": e_cp[1],
        "expenditure_changepoint_magnitude": e_cp[2],
        **recovery_features(progress),
        **expenditure_lag_features(progress, expenditure),
    }


def add_peer_features(cohort: list[dict[str, Any]], minimum_group: int = 10) -> None:
    """Same-month, self-excluded peers by observable cost and progress bands."""
    groups: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in cohort:
        log_cost = row.get("log_original_cost", math.nan)
        cost = math.expm1(log_cost) if _finite(log_cost) else math.nan
        progress = row.get("physical_progress", math.nan)
        velocity = row.get("progress_velocity_last", math.nan)
        if not all(_finite(x) for x in (cost, progress, velocity)) or cost <= 0:
            continue
        cost_band = int(min(max(math.floor(math.log10(cost)), 0), 5))
        maturity_band = int(min(max(math.floor(progress / 20), 0), 5))
        key = (row["anchor_month"], cost_band, maturity_band)
        groups[key].append(row)
    for row in cohort:
        row.update({name: math.nan for name in PEER})
        log_cost, progress = row.get("log_original_cost", math.nan), row.get("physical_progress", math.nan)
        cost = math.expm1(log_cost) if _finite(log_cost) else math.nan
        if not (_finite(cost) and cost > 0 and _finite(progress) and _finite(row.get("progress_velocity_last", math.nan))):
            continue
        key = (row["anchor_month"], int(min(max(math.floor(math.log10(cost)), 0), 5)), int(min(max(math.floor(progress / 20), 0), 5)))
        peers = [p["progress_velocity_last"] for p in groups.get(key, []) if p["canonical_project_id"] != row["canonical_project_id"]]
        if len(peers) < minimum_group:
            continue
        own = row["progress_velocity_last"]
        row["peer_velocity_percentile"] = 100 * (sum(v < own for v in peers) + 0.5 * sum(v == own for v in peers)) / len(peers)
        row["peer_velocity_deviation"] = own - float(np.median(peers))
        row["peer_group_size"] = float(len(peers))


def build_review_cohort(rows: list[dict[str, str]], coverage: dict[str, str], horizon: int = 3) -> list[dict[str, Any]]:
    base = build_s1_cohort(rows, coverage, horizon)
    by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_project[row["canonical_project_id"]].append(row)
    history = {}
    for project, observations in by_project.items():
        observations.sort(key=lambda r: r["reporting_month"])
        for i, row in enumerate(observations):
            history[(project, row["reporting_month"])] = observations[: i + 1]
    cohort = []
    for anchor in base:
        h = history[(anchor["canonical_project_id"], anchor["anchor_month"])]
        cohort.append({**anchor, **advanced_features(h), **teammate_features(h)})
    add_peer_features(cohort)
    return cohort


def rolling_origin(cohort: list[dict[str, Any]], variants: dict[str, tuple[str, ...]]) -> list[dict[str, Any]]:
    # Identical boundaries to Feature Discovery V2; comparisons are paired.
    folds = (("R1", "2023-08", "2025-04", "2025-05"), ("R2", "2025-05", "2025-07", "2025-11"), ("R3", "2025-11", "2025-12", "2026-03"))
    output = []
    for variant, features in variants.items():
        for fold, train_end, test_start, test_end in folds:
            train = [r for r in cohort if r["anchor_month"] <= train_end]
            test = [r for r in cohort if test_start <= r["anchor_month"] <= test_end]
            matrix = lambda part: np.array([[r[n] for n in features] for r in part], dtype=float)
            model = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler()), ("model", HistGradientBoostingClassifier(max_iter=150, learning_rate=.05, max_depth=3, random_state=SEED))])
            y_train = np.array([r["event"] for r in train]); model.fit(matrix(train), y_train)
            threshold = float(np.quantile(model.predict_proba(matrix(train))[:, 1], .90))
            y = np.array([r["event"] for r in test]); p = model.predict_proba(matrix(test))[:, 1]
            output.append({"variant": variant, "fold": fold, "train_end": train_end, "test_start": test_start, "test_end": test_end, "train_anchors": len(train), "test_anchors": len(test), "events": int(y.sum()), **metrics(y, p, threshold)})
    return output


def run(root: Path) -> dict[str, Any]:
    dataset = root / "data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv"
    rows = read_csv(dataset)
    coverage = {r["reporting_month"]: r["coverage_class"] for r in read_csv(root / "data/metadata/source_coverage_2023_07_2026_06.csv")}
    cohort = build_review_cohort(rows, coverage)
    variants = {
        "COMPACT_V2": COMPACT_V2,
        "V2_PLUS_PROGRESS_CHANGEPOINT": COMPACT_V2 + PROGRESS_CHANGEPOINT,
        "V2_PLUS_EXPENDITURE_CHANGEPOINT": COMPACT_V2 + EXPENDITURE_CHANGEPOINT,
        "V2_PLUS_RECOVERY": COMPACT_V2 + RECOVERY,
        "V2_PLUS_PEER": COMPACT_V2 + PEER,
        "V2_PLUS_EXPENDITURE_LAG": COMPACT_V2 + EXPENDITURE_LAG,
        "V2_PLUS_ALL_TESTABLE": COMPACT_V2 + PROGRESS_CHANGEPOINT + EXPENDITURE_CHANGEPOINT + RECOVERY + PEER + EXPENDITURE_LAG,
    }
    ablation = []
    models = {}
    for variant, features in variants.items():
        result, model = evaluate_variant(cohort, variant, features, "HIST_GB")
        ablation.extend(result); models[variant] = model
    rolling = rolling_origin(cohort, variants)
    stability = []
    for variant in variants:
        scores = np.array([r["pr_auc"] for r in rolling if r["variant"] == variant])
        stability.append({"variant": variant, "fold_1_pr_auc": scores[0], "fold_2_pr_auc": scores[1], "fold_3_pr_auc": scores[2], "mean_pr_auc": scores.mean(), "median_pr_auc": np.median(scores), "minimum_pr_auc": scores.min(), "maximum_pr_auc": scores.max(), "std_pr_auc": scores.std(), "variance_pr_auc": scores.var()})
    horizon = []
    for months in (3, 5, 6):
        candidate = build_review_cohort(rows, coverage, months)
        for split in ("TRAIN", "VALIDATION", "TEST"):
            part = [r for r in candidate if split_name(r["anchor_month"]) == split]
            horizon.append({"horizon_months": months, "split": split, "eligible_anchors": len(part), "events": sum(r["event"] for r in part), "event_rate": sum(r["event"] for r in part) / len(part) if part else math.nan})
    test = [r for r in cohort if split_name(r["anchor_month"]) == "TEST"]
    comparison = {}
    predictions = {}
    for variant in ("COMPACT_V2", "V2_PLUS_EXPENDITURE_CHANGEPOINT", "V2_PLUS_RECOVERY"):
        features = variants[variant]
        matrix = np.array([[r[n] for n in features] for r in test], dtype=float)
        probability = models[variant].predict_proba(matrix)[:, 1]
        metric_row = next(r for r in ablation if r["variant"] == variant and r["split"] == "TEST")
        predictions[variant] = probability >= metric_row["threshold"]
        truth = np.array([r["event"] for r in test], dtype=bool)
        comparison[variant] = {"false_positives": int((predictions[variant] & ~truth).sum()), "false_negatives": int((~predictions[variant] & truth).sum())}
    truth = np.array([r["event"] for r in test], dtype=bool)
    error_text = """# Teammate feature error analysis\n\nAll counts use the frozen test period and each model's validation-selected 90th-percentile alert threshold. They are descriptive, not a production claim.\n\n| Variant | False positives | False negatives |\n|---|---:|---:|\n"""
    for variant, counts in comparison.items():
        error_text += f"| {variant} | {counts['false_positives']} | {counts['false_negatives']} |\n"
    candidate = predictions["V2_PLUS_EXPENDITURE_CHANGEPOINT"]
    baseline = predictions["COMPACT_V2"]
    error_text += f"\nExpenditure changepoints corrected {int((baseline & ~truth & ~candidate).sum())} baseline false positives but introduced {int((~baseline & ~truth & candidate).sum())} new false positives. They corrected {int((~baseline & truth & candidate).sum())} baseline false negatives but introduced {int((baseline & truth & ~candidate).sum())} new false negatives. Recovery features are retained only as reliability context because their aggregate false-alert burden rose.\n"
    out = root / "outputs/ml"
    write_csv(out / "PRAHARI_TEAMMATE_FEATURE_ABLATION.csv", ablation)
    write_csv(out / "PRAHARI_TEAMMATE_FEATURE_ROLLING_STABILITY.csv", stability)
    write_csv(out / "PRAHARI_TEAMMATE_FEATURE_ROLLING_FOLDS.csv", rolling)
    write_csv(out / "PRAHARI_TEAMMATE_TARGET_HORIZONS.csv", horizon)
    (out / "PRAHARI_TEAMMATE_FEATURE_ERROR_ANALYSIS.md").write_text(error_text, encoding="utf-8")
    metadata = {"status": "PROVISIONAL RESEARCH — NOT PRODUCTION", "cohort_rows": len(cohort), "variants": {k: list(v) for k, v in variants.items()}, "horizons": horizon}
    (out / "PRAHARI_TEAMMATE_FEATURE_RUN_METADATA.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return metadata
