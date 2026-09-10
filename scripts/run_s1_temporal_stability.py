from pathlib import Path
import csv
import math
import json

import numpy as np

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
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


ROOT = Path(__file__).resolve().parents[1]

DATASET = ROOT / (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "project_month.csv"
)

COVERAGE = ROOT / (
    "data/metadata/"
    "source_coverage_2023_07_2026_06.csv"
)

OUTPUT = ROOT / "outputs/ml/PRAHARI_S1_TEMPORAL_STABILITY.csv"


def month_index(month: str) -> int:
    year, mon = map(int, month.split("-"))
    return year * 12 + mon


def month_from_index(index: int) -> str:
    year = (index - 1) // 12
    month = (index - 1) % 12 + 1
    return f"{year:04d}-{month:02d}"


def matrix(part):
    return np.array(
        [
            [row[name] for name in FEATURES_B]
            for row in part
        ],
        dtype=float,
    )


def metrics(y, probability):
    return {
        "anchors": int(len(y)),
        "events": int(y.sum()),
        "prevalence": float(y.mean()),
        "pr_auc": float(average_precision_score(y, probability)),
        "roc_auc": float(
            roc_auc_score(y, probability)
        ) if len(set(y)) == 2 else math.nan,
        "brier": float(
            brier_score_loss(y, probability)
        ),
    }


def make_model(name):

    if name == "LOGISTIC_B":
        estimator = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=SEED,
        )

        return Pipeline([
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=False,
                ),
            ),
            ("scale", StandardScaler()),
            ("model", estimator),
        ])

    if name == "HIST_GB_B":
        estimator = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=SEED,
        )

    elif name == "RANDOM_FOREST_B":
        estimator = RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=-1,
        )

    elif name == "XGBOOST_B":
        estimator = XGBClassifier(
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
        )

    else:
        raise ValueError(f"Unknown model: {name}")

    return Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="median",
                add_indicator=False,
            ),
        ),
        ("model", estimator),
    ])


def temporal_folds(cohort):

    months = sorted(
        {
            row["anchor_month"]
            for row in cohort
        }
    )

    # We need enough history to train before each future period.
    #
    # Each fold uses:
    #   TRAIN = all earlier anchors
    #   TEST  = one later calendar month
    #
    # This is a rolling-origin evaluation.
    for i in range(1, len(months)):

        train_months = set(months[:i])
        test_month = months[i]

        train = [
            row
            for row in cohort
            if row["anchor_month"] in train_months
        ]

        test = [
            row
            for row in cohort
            if row["anchor_month"] == test_month
        ]

        if not train or not test:
            continue

        # Both classes must exist in training and test.
        y_train = {
            row["event"]
            for row in train
        }

        y_test = {
            row["event"]
            for row in test
        }

        if len(y_train) < 2 or len(y_test) < 2:
            continue

        yield test_month, train, test


def main():

    print("=" * 70)
    print("PRAHARI S1 TEMPORAL STABILITY")
    print("=" * 70)

    rows = read_csv(DATASET)

    coverage_rows = read_csv(COVERAGE)

    coverage = {
        row["reporting_month"]: row["coverage_class"]
        for row in coverage_rows
    }

    cohort = build_s1_cohort(
        rows,
        coverage,
        horizon=3,
    )

    print(f"Total S1 anchors: {len(cohort)}")
    print(
        f"Total S1 events: "
        f"{sum(row['event'] for row in cohort)}"
    )

    model_names = (
        "LOGISTIC_B",
        "HIST_GB_B",
        "RANDOM_FOREST_B",
        "XGBOOST_B",
    )

    output_rows = []

    folds = list(
        temporal_folds(cohort)
    )

    print(f"Temporal folds: {len(folds)}")

    for fold_number, (
        test_month,
        train,
        test,
    ) in enumerate(folds, start=1):

        print(
            f"\nFold {fold_number}: "
            f"train < {test_month}, "
            f"test = {test_month}, "
            f"train={len(train)}, "
            f"test={len(test)}"
        )

        x_train = matrix(train)
        y_train = np.array(
            [row["event"] for row in train],
            dtype=int,
        )

        x_test = matrix(test)
        y_test = np.array(
            [row["event"] for row in test],
            dtype=int,
        )

        for model_name in model_names:

            model = make_model(model_name)

            model.fit(
                x_train,
                y_train,
            )

            probability = model.predict_proba(
                x_test
            )[:, 1]

            result = metrics(
                y_test,
                probability,
            )

            output_rows.append({
                "fold": fold_number,
                "test_month": test_month,
                "model": model_name,
                "feature_set": "FEATURES_B_12",
                **result,
            })

            print(
                f"  {model_name}: "
                f"PR-AUC={result['pr_auc']:.3f} "
                f"ROC-AUC={result['roc_auc']:.3f}"
            )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        fieldnames = [
            "fold",
            "test_month",
            "model",
            "feature_set",
            "anchors",
            "events",
            "prevalence",
            "pr_auc",
            "roc_auc",
            "brier",
        ]

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(output_rows)

    # --------------------------------------------------------
    # Aggregate stability summary
    # --------------------------------------------------------

    summary = {}

    for model_name in model_names:

        rows_for_model = [
            row
            for row in output_rows
            if row["model"] == model_name
        ]

        pr_values = np.array([
            row["pr_auc"]
            for row in rows_for_model
        ])

        roc_values = np.array([
            row["roc_auc"]
            for row in rows_for_model
        ])

        brier_values = np.array([
            row["brier"]
            for row in rows_for_model
        ])

        summary[model_name] = {
            "folds": len(rows_for_model),
            "mean_pr_auc": float(
                np.mean(pr_values)
            ),
            "std_pr_auc": float(
                np.std(pr_values)
            ),
            "min_pr_auc": float(
                np.min(pr_values)
            ),
            "max_pr_auc": float(
                np.max(pr_values)
            ),
            "mean_roc_auc": float(
                np.mean(roc_values)
            ),
            "std_roc_auc": float(
                np.std(roc_values)
            ),
            "mean_brier": float(
                np.mean(brier_values)
            ),
        }

    summary_path = ROOT / (
        "outputs/ml/"
        "PRAHARI_S1_TEMPORAL_STABILITY_SUMMARY.json"
    )

    summary_path.write_text(
        json.dumps(
            {
                "status": (
                    "PROVISIONAL — NOT FINAL SIH CLAIM"
                ),
                "seed": SEED,
                "feature_set": "FEATURES_B_12",
                "fold_definition": (
                    "rolling-origin: all earlier "
                    "anchor months train, one later "
                    "anchor month test"
                ),
                "models": list(model_names),
                "summary": summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 70)
    print("TEMPORAL STABILITY SUMMARY")
    print("=" * 70)

    for model_name, values in summary.items():

        print(
            f"{model_name:20s} "
            f"mean PR-AUC={values['mean_pr_auc']:.3f} "
            f"std={values['std_pr_auc']:.3f} "
            f"min={values['min_pr_auc']:.3f}"
        )

    print("\nSaved:")
    print(OUTPUT)
    print(summary_path)


if __name__ == "__main__":
    main()
