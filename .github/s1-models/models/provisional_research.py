"""Reproducible, provisional schedule-deterioration research.

This module is deliberately conservative: it builds no label where the complete
future observation window is unavailable and never interprets disappearance as
a negative outcome. It is research infrastructure, not a production predictor.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

SEED = 26103
MISSING = {"", "-", "NA", "N.A.", "N/A", "NULL", "UNKNOWN", "NONE"}
FEATURES_A = (
    "log_original_cost", "planned_duration_months", "project_age_months",
    "expenditure_to_cost", "physical_progress", "physical_progress_missing",
)
FEATURES_B = FEATURES_A + (
    "progress_delta_1m", "progress_delta_3m", "expenditure_delta_1m",
    "stagnant_progress_2m", "history_months", "correction_count",
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def value(row: dict[str, str], raw: str, fallback: str = "") -> str:
    return clean(row.get(raw)) or clean(row.get(fallback))


def number(raw: Any) -> float:
    text = clean(raw).replace(",", "").replace("₹", "")
    if text.upper() in MISSING:
        return math.nan
    try:
        return float(text.replace("%", ""))
    except ValueError:
        return math.nan


def month_date(raw: Any) -> date | None:
    text = clean(raw).split("(")[0].strip()
    if text.upper() in MISSING:
        return None
    parts = text.replace("-", "/").split("/")
    try:
        if len(parts) == 2:
            month, year = map(int, parts)
            return date(year, month, 1)
        if len(parts) == 3:
            day, month, year = map(int, parts)
            return date(year, month, day)
    except (ValueError, OverflowError):
        return None
    return None


def month_index(raw: str) -> int:
    year, month = map(int, raw.split("-"))
    return year * 12 + month


def months_between(left: date | None, right: date | None) -> float:
    if left is None or right is None:
        return math.nan
    return float((right.year - left.year) * 12 + right.month - left.month)


def approved_doc(row: dict[str, str]) -> date | None:
    original = month_date(value(row, "original_target_doc_raw", "reported_original_target_doc"))
    revised = month_date(value(row, "revised_doc_raw", "reported_revised_doc"))
    return revised or original


def is_initially_unrevised(row: dict[str, str]) -> bool:
    original = month_date(value(row, "original_target_doc_raw", "reported_original_target_doc"))
    revised = month_date(value(row, "revised_doc_raw", "reported_revised_doc"))
    return original is not None and (revised is None or revised <= original)


def has_ever_been_revised(history: Iterable[dict[str, str]]) -> bool:
    """Return true when an approved schedule deterioration was already observed."""
    for row in history:
        original = month_date(value(row, "original_target_doc_raw", "reported_original_target_doc"))
        revised = month_date(value(row, "revised_doc_raw", "reported_revised_doc"))
        if original is not None and revised is not None and revised > original:
            return True
    return False


def has_future_schedule_deterioration(current: dict[str, str], future: Iterable[dict[str, str]]) -> bool:
    baseline = approved_doc(current)
    return baseline is not None and any((candidate := approved_doc(row)) is not None and candidate > baseline for row in future)


def _features(history: list[dict[str, str]], anchor: dict[str, str]) -> dict[str, float]:
    original_cost = number(value(anchor, "original_cost_raw", "reported_original_cost"))
    expenditure = number(value(anchor, "cumulative_expenditure_raw", "reported_cumulative_expenditure"))
    progress = number(value(anchor, "physical_progress_raw", "reported_physical_progress"))
    approval = month_date(value(anchor, "approval_date_raw", "reported_approval_date"))
    original_doc = month_date(value(anchor, "original_target_doc_raw", "reported_original_target_doc"))

    anchor_year, anchor_month = map(int, anchor["reporting_month"].split("-"))
    anchor_date = date(anchor_year, anchor_month, 1)

    # Temporal features are calculated only from contiguous calendar observations.
    progress_history = [
        (
            month_index(row["reporting_month"]),
            number(value(row, "physical_progress_raw", "reported_physical_progress"))
        )
        for row in history
    ]

    expenditure_history = [
        (
            month_index(row["reporting_month"]),
            number(value(row, "cumulative_expenditure_raw", "reported_cumulative_expenditure"))
        )
        for row in history
    ]

    docs = [approved_doc(row) for row in history]
    corrections = sum(
        1 for left, right in zip(docs, docs[1:])
        if left and right and right < left
    )

    def contiguous_delta(series: list[tuple[int, float]], lag_months: int) -> float:
        if len(series) < 2:
            return math.nan

        current_month, current_value = series[-1]
        target_month = current_month - lag_months

        previous_value = math.nan
        for month, value_ in reversed(series[:-1]):
            if month == target_month:
                previous_value = value_
                break

        if (
            np.isfinite(current_value)
            and np.isfinite(previous_value)
        ):
            return current_value - previous_value

        return math.nan

    progress_1 = contiguous_delta(progress_history, 1)

    return {
        "log_original_cost": (
            math.log1p(original_cost)
            if np.isfinite(original_cost) and original_cost >= 0
            else math.nan
        ),
        "planned_duration_months": months_between(approval, original_doc),
        "project_age_months": months_between(approval, anchor_date),
        "expenditure_to_cost": (
            expenditure / original_cost
            if np.isfinite(expenditure)
            and np.isfinite(original_cost)
            and original_cost > 0
            else math.nan
        ),
        "physical_progress": progress,
        "physical_progress_missing": float(not np.isfinite(progress)),
        "progress_delta_1m": progress_1,
        "progress_delta_3m": contiguous_delta(progress_history, 3),
        "expenditure_delta_1m": contiguous_delta(expenditure_history, 1),
        "stagnant_progress_2m": float(
            np.isfinite(progress_1) and progress_1 <= 0
        ),
        "history_months": float(len(history)),
        "correction_count": float(corrections),
    }



def build_s1_cohort(rows: list[dict[str, str]], coverage: dict[str, str], horizon: int = 3) -> list[dict[str, Any]]:
    by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_project[row["canonical_project_id"]].append(row)
    cohort: list[dict[str, Any]] = []
    for project_id, observations in by_project.items():
        observations.sort(key=lambda row: row["reporting_month"])
        lookup = {row["reporting_month"]: row for row in observations}
        for index, anchor in enumerate(observations):
            anchor_i = month_index(anchor["reporting_month"])
            future_months = [f"{(anchor_i + step - 1)//12:04d}-{(anchor_i + step - 1)%12 + 1:02d}" for step in range(1, horizon + 1)]
            if any(coverage.get(month) != "PROJECT_LEVEL" for month in future_months):
                continue
            if any(month not in lookup for month in future_months):
                continue
            history = observations[: index + 1]
            if len(history) < 2 or month_index(history[-1]["reporting_month"]) - month_index(history[-2]["reporting_month"]) != 1:
                continue
            if not is_initially_unrevised(anchor) or has_ever_been_revised(history[:-1]):
                continue
            features = _features(history, anchor)
            cohort.append({"canonical_project_id": project_id, "anchor_month": anchor["reporting_month"],
                           "event": int(has_future_schedule_deterioration(anchor, [lookup[m] for m in future_months])), **features})
    return cohort


def split_name(month: str) -> str:
    if month <= "2025-05":
        return "TRAIN"
    if month <= "2025-11":
        return "VALIDATION"
    return "TEST"


AGENCY_ALIASES = {
    "nhai": ("AG-NHAI", "National Highways Authority of India", "AUTHORITY", "VERIFIED_ALIAS"),
    "nationalhighwaysauthorityofindianhai": ("AG-NHAI", "National Highways Authority of India", "AUTHORITY", "VERIFIED_ALIAS"),
    "pgcil": ("AG-POWERGRID", "Power Grid Corporation of India Limited", "PSU", "VERIFIED_ALIAS"),
    "powergridcorporationofindialimitedpowergrid": ("AG-POWERGRID", "Power Grid Corporation of India Limited", "PSU", "VERIFIED_ALIAS"),
}


def normalize_agency(raw: str) -> dict[str, str]:
    key = "".join(character for character in clean(raw).lower() if character.isalnum())
    mapped = AGENCY_ALIASES.get(key)
    if not mapped:
        return {"agency_raw": raw, "agency_entity_id": "", "agency_normalized_name": raw,
                "agency_role": "UNKNOWN", "agency_normalization_quality": "UNRESOLVED"}
    entity_id, name, role, quality = mapped
    return {"agency_raw": raw, "agency_entity_id": entity_id, "agency_normalized_name": name,
            "agency_role": role, "agency_normalization_quality": quality}


def abstention_reason(*, history_months: int, critical_missing: bool, source_gap: bool,
                      identity_resolved: bool, subgroup_supported: bool) -> str:
    reasons = []
    if history_months < 2: reasons.append("INSUFFICIENT_HISTORY")
    if critical_missing: reasons.append("CRITICAL_FEATURE_MISSING")
    if source_gap: reasons.append("SOURCE_GAP")
    if not identity_resolved: reasons.append("UNRESOLVED_IDENTITY")
    if not subgroup_supported: reasons.append("UNSUPPORTED_SUBGROUP")
    return "|".join(reasons)


def evidence_object(project_id: str, as_of_month: str, probability: float | None,
                    reliability: str, abstention: str = "") -> dict[str, Any]:
    if abstention:
        probability = None
    return {"prediction_id": f"S1-3M-{project_id}-{as_of_month}", "canonical_project_id": project_id,
            "as_of_month": as_of_month, "target": "S1", "horizon_months": 3,
            "eligibility": not bool(abstention), "calibrated_probability": probability,
            "risk_band": None, "reliability_band": "ABSTAIN" if abstention else reliability,
            "reliability_reasons": [], "data_quality_status": "REVIEW" if abstention else "GOOD",
            "review_priority": "DATA_QUALITY_REVIEW" if abstention else None,
            "top_contributors": [], "rule_result": None, "peer_summary": None,
            "trajectory_summary": None, "provenance": [], "model_version": "PROVISIONAL",
            "feature_version": "features-v0.1", "target_version": "S1-v0.1-provisional",
            "calibration_version": "UNVALIDATED", "abstention_reason": abstention}


def _metrics(y: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, float]:
    prediction = probability >= threshold
    return {
        "anchors": int(len(y)), "events": int(y.sum()), "prevalence": float(y.mean()),
        "pr_auc": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)) if len(set(y)) == 2 else math.nan,
        "brier": float(brier_score_loss(y, probability)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "false_alerts_per_100": float(100 * ((prediction == 1) & (y == 0)).sum() / len(y)),
        "threshold": float(threshold),
    }


def evaluate(cohort: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Controlled S1 model comparison.

    Frozen:
      - S1 target and cohort
      - FEATURES_B (12 features)
      - chronological TRAIN / VALIDATION / TEST split
      - preprocessing fitted only on TRAIN
      - 10% review-capacity threshold fitted on VALIDATION

    Models:
      - Logistic Regression
      - HistGradientBoosting
      - Random Forest
      - XGBoost
      - Rule baseline

    TEST is used only for final evaluation.
    """

    partitions = {
        name: [
            row for row in cohort
            if split_name(row["anchor_month"]) == name
        ]
        for name in ("TRAIN", "VALIDATION", "TEST")
    }

    if any(not part for part in partitions.values()):
        raise RuntimeError("temporal split has an empty partition")

    results: list[dict[str, Any]] = []
    fitted: dict[str, Any] = {}

    train = partitions["TRAIN"]
    validation = partitions["VALIDATION"]

    def matrix(
        part: list[dict[str, Any]],
        feature_names: tuple[str, ...]
    ) -> np.ndarray:
        return np.array(
            [
                [row[name] for name in feature_names]
                for row in part
            ],
            dtype=float
        )

    y_train = np.array(
        [row["event"] for row in train],
        dtype=int
    )

    # ========================================================
    # SAME 12-FEATURE CONTRACT FOR ALL FOUR ML MODELS
    # ========================================================

    models = (
        (
            "LOGISTIC_B",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=SEED
            )
        ),
        (
            "HIST_GB_B",
            HistGradientBoostingClassifier(
                max_iter=150,
                learning_rate=0.05,
                max_depth=3,
                random_state=SEED
            )
        ),
        (
            "RANDOM_FOREST_B",
            RandomForestClassifier(
                n_estimators=500,
                max_depth=None,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=SEED,
                n_jobs=-1
            )
        ),
        (
            "XGBOOST_B",
            XGBClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_lambda=1.0,
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=SEED,
                n_jobs=-1
            )
        ),
    )

    for label, estimator in models:

        # ----------------------------------------------------
        # Preprocessing is fitted ONLY on TRAIN.
        # ----------------------------------------------------
        pipeline = Pipeline([
            (
                "imputer",
                SimpleImputer(
    strategy="median",
    add_indicator=False,
    keep_empty_features=True
)
            ),
            (
                "scale",
                StandardScaler()
            ),
            (
                "model",
                estimator
            )
        ])

        x_train = matrix(train, FEATURES_B)

        pipeline.fit(
            x_train,
            y_train
        )

        # ----------------------------------------------------
        # Validation threshold:
        # approximately 10% review capacity.
        # ----------------------------------------------------
        val_probability = pipeline.predict_proba(
            matrix(validation, FEATURES_B)
        )[:, 1]

        threshold = float(
            np.quantile(val_probability, 0.90)
        )

        # ----------------------------------------------------
        # Evaluate TRAIN / VALIDATION / TEST.
        # Threshold is fixed from validation.
        # ----------------------------------------------------
        for split, part in partitions.items():

            probability = pipeline.predict_proba(
                matrix(part, FEATURES_B)
            )[:, 1]

            y = np.array(
                [row["event"] for row in part],
                dtype=int
            )

            results.append({
                "model": label,
                "feature_set": "FEATURES_B_12",
                "split": split,
                **_metrics(
                    y,
                    probability,
                    threshold
                )
            })

        fitted[label] = pipeline

    # ========================================================
    # RULE BASELINE
    # ========================================================

    for split, part in partitions.items():

        scores = np.array([
            float(
                (row["stagnant_progress_2m"] == 1)
                or
                (
                    np.isfinite(row["physical_progress"])
                    and row["physical_progress"] < 50
                    and np.isfinite(row["project_age_months"])
                    and np.isfinite(row["planned_duration_months"])
                    and row["project_age_months"]
                    > 0.8 * row["planned_duration_months"]
                )
            )
            for row in part
        ])

        results.append({
            "model": "RULE",
            "feature_set": "RULE_ONLY",
            "split": split,
            **_metrics(
                np.array(
                    [row["event"] for row in part],
                    dtype=int
                ),
                scores,
                0.5
            )
        })

    # ========================================================
    # PROVISIONAL PLATT CALIBRATION FOR HIST_GB
    # ========================================================

    hist = fitted["HIST_GB_B"]

    val_raw = np.clip(
        hist.predict_proba(
            matrix(validation, FEATURES_B)
        )[:, 1],
        1e-6,
        1 - 1e-6
    )

    test = partitions["TEST"]

    test_raw = np.clip(
        hist.predict_proba(
            matrix(test, FEATURES_B)
        )[:, 1],
        1e-6,
        1 - 1e-6
    )

    y_validation = np.array(
        [row["event"] for row in validation],
        dtype=int
    )

    y_test = np.array(
        [row["event"] for row in test],
        dtype=int
    )

    calibrator = LogisticRegression(
        random_state=SEED
    ).fit(
        np.log(
            val_raw / (1 - val_raw)
        ).reshape(-1, 1),
        y_validation
    )

    val_calibrated = calibrator.predict_proba(
        np.log(
            val_raw / (1 - val_raw)
        ).reshape(-1, 1)
    )[:, 1]

    test_calibrated = calibrator.predict_proba(
        np.log(
            test_raw / (1 - test_raw)
        ).reshape(-1, 1)
    )[:, 1]

    calibrated_threshold = float(
        np.quantile(val_calibrated, 0.90)
    )

    results.append({
        "model": "HIST_GB_B_PLATT",
        "feature_set": "FEATURES_B_12",
        "split": "TEST",
        **_metrics(
            y_test,
            test_calibrated,
            calibrated_threshold
        )
    })

    metadata = {
        "partitions": {
            key: {
                "anchors": len(value),
                "events": sum(
                    row["event"]
                    for row in value
                )
            }
            for key, value in partitions.items()
        },
        "seed": SEED,
        "feature_set": "FEATURES_B",
        "feature_count": len(FEATURES_B),
        "feature_names": list(FEATURES_B),
        "threshold_policy": "90th percentile of validation probability",
        "review_capacity": 0.10,
        "models": [
            "LOGISTIC_B",
            "HIST_GB_B",
            "RANDOM_FOREST_B",
            "XGBOOST_B",
            "RULE"
        ],
        "status": "PROVISIONAL — NOT FINAL SIH CLAIM"
    }

    return results, metadata



def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader(); writer.writerows(rows)


def run(root: Path) -> dict[str, Any]:
    dataset = root / "data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv"
    coverage_rows = read_csv(root / "data/metadata/source_coverage_2023_07_2026_06.csv")
    coverage = {row["reporting_month"]: row["coverage_class"] for row in coverage_rows}
    cohort = build_s1_cohort(read_csv(dataset), coverage, 3)
    results, metadata = evaluate(cohort)
    output = root / "outputs/ml"
    write_csv(output / "PRAHARI_S1_MODEL_COMPARISON.csv", results)
    write_csv(output / "PRAHARI_SUBGROUP_EVALUATION.csv", [{"status": "NOT_EVALUABLE", "reason": "authoritative ministry and sector fields are absent from frozen modern rows"}])
    write_csv(output / "PRAHARI_CALIBRATION_RESULTS.csv", [{"model": row["model"], "split": row["split"], "brier": row["brier"], "status": "PLATT_PROVISIONAL" if row["model"].endswith("PLATT") else "UNCALIBRATED_PROVISIONAL"} for row in results if row["model"] != "RULE"])
    write_csv(output / "PRAHARI_LEAD_TIME_RESULTS.csv", [{"target": "S1", "horizon_months": 3, "lead_time_status": "NOT_ESTIMATED", "reason": "first detection timing requires human-validated event adjudication"}])
    payload = {"status": "PROVISIONAL — NOT FINAL SIH CLAIM", "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(), "target_version": "S1-v0.1-provisional", "feature_version": "features-v0.1", **metadata, "results": results}
    (output / "provisional_run_metadata.json").write_text(json.dumps(payload, indent=2, allow_nan=False, default=lambda _: None) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[2])
