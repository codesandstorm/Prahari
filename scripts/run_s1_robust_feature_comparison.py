from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
)
from xgboost import XGBClassifier

from src.ml.provisional_research import (
    read_csv,
    build_s1_cohort,
    FEATURES_B,
    SEED,
)


# ============================================================
# PATHS
# ============================================================

DATA_PATH = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "project_month.csv"
)

OUTPUT_DIR = Path("outputs/ml")


# ============================================================
# ROBUST CORE FEATURES
# ============================================================

ROBUST_CORE = [
    "planned_duration_months",
    "progress_delta_1m",
    "progress_delta_3m",
]


# ============================================================
# MODELS
# Same controlled models as the S1 comparison
# ============================================================

def make_models() -> dict[str, Any]:

    return {
        "LOGISTIC_B": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=SEED,
        ),

        "HIST_GB_B": HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=SEED,
        ),

        "RANDOM_FOREST_B": RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=-1,
        ),

        "XGBOOST_B": XGBClassifier(
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
            n_jobs=-1,
        ),
    }


# ============================================================
# PREPARE X AND Y
# ============================================================

def prepare_xy(
    cohort: list[dict[str, Any]],
    feature_names: list[str],
) -> tuple[np.ndarray, np.ndarray]:

    X = []

    for row in cohort:

        values = []

        for feature in feature_names:

            raw_value = row.get(
                feature,
                np.nan,
            )

            try:

                if raw_value is None or raw_value == "":
                    value = np.nan
                else:
                    value = float(raw_value)

            except (
                TypeError,
                ValueError,
            ):

                value = np.nan

            values.append(value)

        X.append(values)

    X = np.asarray(
        X,
        dtype=float,
    )

    # IMPORTANT:
    # Your build_s1_cohort() creates "event",
    # NOT "target".
    y = np.asarray(
        [
            int(row["event"])
            for row in cohort
        ],
        dtype=int,
    )

    return X, y


# ============================================================
# SAFE METRICS
# ============================================================

def safe_pr_auc(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> float:

    if len(np.unique(y_true)) < 2:
        return float("nan")

    return float(
        average_precision_score(
            y_true,
            probability,
        )
    )


def safe_roc_auc(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> float:

    if len(np.unique(y_true)) < 2:
        return float("nan")

    return float(
        roc_auc_score(
            y_true,
            probability,
        )
    )


def safe_brier(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> float:

    return float(
        brier_score_loss(
            y_true,
            probability,
        )
    )


# ============================================================
# ROLLING-ORIGIN EVALUATION
# ============================================================

def evaluate_feature_set(
    cohort: list[dict[str, Any]],
    feature_names: list[str],
    feature_set_name: str,
) -> list[dict[str, Any]]:

    months = sorted(
        {
            str(row["anchor_month"])
            for row in cohort
            if row.get("anchor_month")
        }
    )

    print()
    print("=" * 80)
    print(
        f"FEATURE SET: {feature_set_name}"
    )
    print("=" * 80)

    print("Features:")

    for feature in feature_names:
        print(f"  - {feature}")

    fold_results = []

    # --------------------------------------------------------
    # Rolling-origin:
    #
    # All earlier anchor months = TRAIN
    # One later anchor month = TEST
    # --------------------------------------------------------

    for test_month in months[1:]:

        train_rows = [
            row
            for row in cohort
            if str(row["anchor_month"]) < test_month
        ]

        test_rows = [
            row
            for row in cohort
            if str(row["anchor_month"]) == test_month
        ]

        if not train_rows or not test_rows:
            continue

        X_train, y_train = prepare_xy(
            train_rows,
            feature_names,
        )

        X_test, y_test = prepare_xy(
            test_rows,
            feature_names,
        )

        # Both classes required for training
        if len(np.unique(y_train)) < 2:

            print(
                f"\nSkipping {test_month}: "
                "training data contains only one class."
            )

            continue

        print()
        print(
            f"Test month: {test_month} | "
            f"Train: {len(train_rows)} | "
            f"Test: {len(test_rows)} | "
            f"Events: {int(y_test.sum())} | "
            f"Prevalence: {np.mean(y_test):.2%}"
        )

        # ----------------------------------------------------
        # Median imputation
        # No automatic missing indicators
        # ----------------------------------------------------

        imputer = SimpleImputer(
            strategy="median",
            add_indicator=False,
        )

        X_train_imp = imputer.fit_transform(
            X_train
        )

        X_test_imp = imputer.transform(
            X_test
        )

        models = make_models()

        for model_name, model in models.items():

            model.fit(
                X_train_imp,
                y_train,
            )

            probability = (
                model.predict_proba(
                    X_test_imp
                )[:, 1]
            )

            pr_auc = safe_pr_auc(
                y_test,
                probability,
            )

            roc_auc = safe_roc_auc(
                y_test,
                probability,
            )

            brier = safe_brier(
                y_test,
                probability,
            )

            result = {
                "feature_set": feature_set_name,
                "model": model_name,
                "test_month": test_month,
                "train_anchors": len(train_rows),
                "test_anchors": len(test_rows),
                "test_events": int(y_test.sum()),
                "test_prevalence": float(
                    np.mean(y_test)
                ),
                "pr_auc": pr_auc,
                "roc_auc": roc_auc,
                "brier": brier,
            }

            fold_results.append(result)

            print(
                f"  {model_name:<20}"
                f"PR-AUC={pr_auc:.4f}  "
                f"ROC-AUC={roc_auc:.4f}  "
                f"Brier={brier:.4f}"
            )

    return fold_results


# ============================================================
# SUMMARY
# ============================================================

def create_summary(
    folds_df: pd.DataFrame,
) -> pd.DataFrame:

    if folds_df.empty:
        return pd.DataFrame()

    summary = (
        folds_df
        .groupby(
            [
                "feature_set",
                "model",
            ],
            as_index=False,
        )
        .agg(
            folds=(
                "test_month",
                "count",
            ),

            mean_pr_auc=(
                "pr_auc",
                "mean",
            ),

            std_pr_auc=(
                "pr_auc",
                "std",
            ),

            min_pr_auc=(
                "pr_auc",
                "min",
            ),

            max_pr_auc=(
                "pr_auc",
                "max",
            ),

            mean_roc_auc=(
                "roc_auc",
                "mean",
            ),

            std_roc_auc=(
                "roc_auc",
                "std",
            ),

            mean_brier=(
                "brier",
                "mean",
            ),

            std_brier=(
                "brier",
                "std",
            ),
        )
    )

    return summary


# ============================================================
# PRINT FINAL COMPARISON
# ============================================================

def print_final_comparison(
    summary_df: pd.DataFrame,
) -> None:

    print()
    print("=" * 100)
    print("FINAL ROBUST FEATURE COMPARISON")
    print("=" * 100)

    if summary_df.empty:

        print("No results generated.")

        return

    columns = [
        "feature_set",
        "model",
        "folds",
        "mean_pr_auc",
        "std_pr_auc",
        "min_pr_auc",
        "max_pr_auc",
        "mean_roc_auc",
        "std_roc_auc",
        "mean_brier",
        "std_brier",
    ]

    print(
        summary_df[columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )


# ============================================================
# BUILD SOURCE COVERAGE
# ============================================================

def build_coverage(
    rows: list[dict[str, str]],
) -> dict[str, str]:

    # IMPORTANT:
    # Your actual column is reporting_month,
    # not month.

    reporting_months = sorted(
        {
            row["reporting_month"]
            for row in rows
            if row.get("reporting_month")
        }
    )

    coverage = {}

    # Default:
    # Every month represented in project_month.csv
    # is treated as PROJECT_LEVEL.
    #
    # Then known source-regime exceptions are explicitly
    # overridden below.

    for month in reporting_months:
        coverage[month] = "PROJECT_LEVEL"

    # Known aggregate-only months from the PRAHARI
    # source coverage audit.
    aggregate_only = {
        "2023-12",
        "2024-04",
        "2024-05",
        "2024-08",
        "2024-09",
    }

    for month in aggregate_only:

        coverage[month] = "AGGREGATE_ONLY"

    # Known missing source.
    coverage["2025-02"] = "MISSING_SOURCE"

    return coverage


# ============================================================
# MAIN RUN
# ============================================================

def run(
    root: Path,
) -> None:

    print("=" * 80)
    print("PRAHARI S1 ROBUST FEATURE COMPARISON")
    print("=" * 80)

    data_path = root / DATA_PATH

    print()
    print(
        f"Dataset: {data_path}"
    )

    if not data_path.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{data_path}"
        )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    print()
    print("Loading project-month data...")

    rows = read_csv(
        data_path
    )

    print(
        f"Loaded {len(rows):,} "
        "project-month rows."
    )

    # --------------------------------------------------------
    # BUILD COVERAGE
    # --------------------------------------------------------

    print()
    print("Building source coverage...")

    coverage = build_coverage(
        rows
    )

    print(
        f"Coverage months: "
        f"{len(coverage)}"
    )

    # Print important coverage checks
    for month in [
        "2024-04",
        "2024-05",
        "2024-08",
        "2024-09",
        "2025-02",
        "2025-07",
        "2025-08",
        "2025-11",
        "2026-03",
    ]:

        print(
            f"  {month}: "
            f"{coverage.get(month)}"
        )

    # --------------------------------------------------------
    # BUILD S1 COHORT
    # --------------------------------------------------------

    print()
    print("Building S1 cohort...")

    cohort = build_s1_cohort(
        rows,
        coverage,
        horizon=3,
    )

    print()
    print(
        f"S1 cohort anchors: "
        f"{len(cohort):,}"
    )

    if not cohort:

        raise RuntimeError(
            "S1 cohort is empty. "
            "Coverage or source-month construction is incorrect."
        )

    # --------------------------------------------------------
    # S1 TARGET CHECK
    # --------------------------------------------------------

    event_count = sum(
        int(row["event"])
        for row in cohort
    )

    print(
        f"S1 events: "
        f"{event_count:,}"
    )

    print(
        f"S1 non-events: "
        f"{len(cohort) - event_count:,}"
    )

    print(
        f"S1 event rate: "
        f"{event_count / len(cohort):.2%}"
    )

    # --------------------------------------------------------
    # EXPECTED SANITY CHECK
    # --------------------------------------------------------

    print()
    print("Expected frozen S1 sanity check:")
    print("  Anchors ≈ 5,982")
    print("  Events  ≈ 1,417")
    print("  Rate    ≈ 23.69%")

    # We don't hard-fail if these differ slightly,
    # because this script should use the current
    # source code and data exactly as present.
    #
    # A large difference, however, should be investigated.

    if len(cohort) < 5000:

        print()
        print(
            "WARNING: Cohort is substantially smaller "
            "than the previously validated 5,982 anchors."
        )

    # --------------------------------------------------------
    # FEATURE CHECK
    # --------------------------------------------------------

    print()
    print("Checking FEATURES_B...")

    missing_features = [
        feature
        for feature in FEATURES_B
        if not all(
            feature in row
            for row in cohort
        )
    ]

    if missing_features:

        raise RuntimeError(
            "Missing FEATURES_B columns in cohort: "
            + ", ".join(
                missing_features
            )
        )

    print(
        f"FEATURES_B_12: "
        f"{len(FEATURES_B)} features"
    )

    # --------------------------------------------------------
    # ROBUST CORE CHECK
    # --------------------------------------------------------

    print()
    print("Checking ROBUST_CORE_3...")

    missing_core = [
        feature
        for feature in ROBUST_CORE
        if not all(
            feature in row
            for row in cohort
        )
    ]

    if missing_core:

        raise RuntimeError(
            "Missing ROBUST_CORE features: "
            + ", ".join(
                missing_core
            )
        )

    print(
        "ROBUST_CORE_3:"
    )

    for feature in ROBUST_CORE:
        print(
            f"  - {feature}"
        )

    # --------------------------------------------------------
    # FULL 12-FEATURE EXPERIMENT
    # --------------------------------------------------------

    full_results = evaluate_feature_set(
        cohort=cohort,
        feature_names=list(FEATURES_B),
        feature_set_name="FEATURES_B_12",
    )

    # --------------------------------------------------------
    # ROBUST 3-FEATURE EXPERIMENT
    # --------------------------------------------------------

    robust_results = evaluate_feature_set(
        cohort=cohort,
        feature_names=ROBUST_CORE,
        feature_set_name="ROBUST_CORE_3",
    )

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    all_results = (
        full_results
        + robust_results
    )

    if not all_results:

        raise RuntimeError(
            "No rolling-origin results were produced."
        )

    folds_df = pd.DataFrame(
        all_results
    )

    summary_df = create_summary(
        folds_df
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    folds_path = (
        OUTPUT_DIR
        / "PRAHARI_S1_ROBUST_FEATURE_COMPARISON_FOLDS.csv"
    )

    summary_path = (
        OUTPUT_DIR
        / "PRAHARI_S1_ROBUST_FEATURE_COMPARISON_SUMMARY.csv"
    )

    folds_df.to_csv(
        folds_path,
        index=False,
    )

    summary_df.to_csv(
        summary_path,
        index=False,
    )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    print_final_comparison(
        summary_df
    )

    print()
    print("=" * 80)
    print("FILES SAVED")
    print("=" * 80)

    print()
    print(
        folds_path
    )

    print()
    print(
        summary_path
    )

    print()
    print("=" * 80)
    print("ROBUST FEATURE COMPARISON COMPLETE")
    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run(
        Path(__file__).resolve().parents[1]
    )
