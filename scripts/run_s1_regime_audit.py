from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from src.ml.provisional_research import (
    build_s1_cohort,
    FEATURES_B,
)

SEED = 26103


# ============================================================
# SOURCE COVERAGE
# ============================================================

def get_coverage():
    coverage = {}

    project_level_months = [
        "2023-07", "2023-08", "2023-09", "2023-10", "2023-11",
        "2024-01", "2024-02", "2024-03",
        "2024-06", "2024-07",
        "2024-10", "2024-11", "2024-12",
        "2025-01",
        "2025-03", "2025-04", "2025-05", "2025-06",
        "2025-07", "2025-08", "2025-09", "2025-10", "2025-11",
        "2025-12",
        "2026-01", "2026-02", "2026-03",
        "2026-04", "2026-05", "2026-06",
    ]

    for month in project_level_months:
        coverage[month] = "PROJECT_LEVEL"

    aggregate_only_months = [
        "2023-12",
        "2024-04",
        "2024-05",
        "2024-08",
        "2024-09",
    ]

    for month in aggregate_only_months:
        coverage[month] = "AGGREGATE_ONLY"

    coverage["2025-02"] = "MISSING_SOURCE"

    return coverage


# ============================================================
# CHRONOLOGICAL SPLIT
# ============================================================

def split_name(month):
    if month <= "2025-05":
        return "TRAIN"

    elif month <= "2025-11":
        return "VALIDATION"

    else:
        return "TEST"


# ============================================================
# FEATURE MATRIX
# ============================================================

def make_matrix(df):
    """
    FEATURES_B is a tuple in provisional_research.py.
    Convert it to a list before pandas column selection.
    """

    return df[list(FEATURES_B)].astype(float)


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    y_true,
    probability,
    threshold
):

    from sklearn.metrics import (
        average_precision_score,
        roc_auc_score,
        brier_score_loss,
    )

    y_true = np.asarray(y_true)
    probability = np.asarray(probability)

    prediction = (
        probability >= threshold
    ).astype(int)

    true_positive = int(
        (
            (prediction == 1)
            &
            (y_true == 1)
        ).sum()
    )

    false_positive = int(
        (
            (prediction == 1)
            &
            (y_true == 0)
        ).sum()
    )

    false_negative = int(
        (
            (prediction == 0)
            &
            (y_true == 1)
        ).sum()
    )

    precision = (
        true_positive
        /
        (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0.0
    )

    recall = (
        true_positive
        /
        (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0.0
    )

    false_alerts_per_100 = (
        false_positive
        /
        len(y_true)
        *
        100
        if len(y_true) > 0
        else 0.0
    )

    pr_auc = average_precision_score(
        y_true,
        probability
    )

    try:
        roc_auc = roc_auc_score(
            y_true,
            probability
        )
    except ValueError:
        roc_auc = np.nan

    brier = brier_score_loss(
        y_true,
        probability
    )

    return {
        "anchors": len(y_true),
        "events": int(y_true.sum()),
        "event_rate": float(y_true.mean()),
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "brier": float(brier),
        "precision": float(precision),
        "recall": float(recall),
        "false_alerts_per_100": float(
            false_alerts_per_100
        ),
    }


# ============================================================
# MODEL DEFINITIONS
# ============================================================

def build_model(model_name):

    if model_name == "RANDOM_FOREST_B":

        model = RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=-1,
        )

    elif model_name == "XGBOOST_B":

        model = XGBClassifier(
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

        raise ValueError(
            f"Unknown model: {model_name}"
        )

    return Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=False,
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                model,
            ),
        ]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    repo_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    print()
    print("=" * 60)
    print("PRAHARI S1 REGIME AUDIT")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. LOAD DATASET
    # --------------------------------------------------------

    dataset_path = (
        repo_root
        / "data"
        / "processed"
        / "longitudinal_2023_07_2026_06_mixed"
        / "project_month.csv"
    )

    print()
    print("Dataset:")
    print(dataset_path)

    if not dataset_path.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{dataset_path}"
        )

    data = pd.read_csv(
        dataset_path
    )

    print()
    print(
        "Rows loaded:",
        len(data)
    )

    print(
        "Columns:",
        len(data.columns)
    )

    # --------------------------------------------------------
    # 2. CONVERT DATA TO ROW DICTIONARIES
    # --------------------------------------------------------

    data = data.replace(
        {np.nan: ""}
    )

    rows = (
        data
        .astype(str)
        .to_dict("records")
    )

    coverage = get_coverage()

    # --------------------------------------------------------
    # 3. BUILD EXACT FROZEN S1 COHORT
    # --------------------------------------------------------

    cohort_rows = build_s1_cohort(
        rows,
        coverage,
        horizon=3,
    )

    df = pd.DataFrame(
        cohort_rows
    )

    print()
    print("=" * 60)
    print("EXACT S1 COHORT")
    print("=" * 60)

    print()
    print(
        "Anchors:",
        len(df)
    )

    print(
        "Events:",
        int(df["event"].sum())
    )

    print(
        "Event rate:",
        round(
            df["event"].mean() * 100,
            2
        ),
        "%"
    )

    # --------------------------------------------------------
    # 4. CHRONOLOGICAL SPLITS
    # --------------------------------------------------------

    df["split"] = (
        df["anchor_month"]
        .apply(split_name)
    )

    train = df[
        df["split"] == "TRAIN"
    ].copy()

    validation = df[
        df["split"] == "VALIDATION"
    ].copy()

    test = df[
        df["split"] == "TEST"
    ].copy()

    print()
    print("=" * 60)
    print("CHRONOLOGICAL SPLITS")
    print("=" * 60)

    print()
    print(
        "TRAIN:",
        len(train),
        "anchors /",
        int(train["event"].sum()),
        "events"
    )

    print(
        "VALIDATION:",
        len(validation),
        "anchors /",
        int(validation["event"].sum()),
        "events"
    )

    print(
        "TEST:",
        len(test),
        "anchors /",
        int(test["event"].sum()),
        "events"
    )

    # --------------------------------------------------------
    # 5. TRAINING / VALIDATION MATRICES
    # --------------------------------------------------------

    X_train = make_matrix(
        train
    )

    y_train = (
        train["event"]
        .astype(int)
    )

    X_validation = make_matrix(
        validation
    )

    y_validation = (
        validation["event"]
        .astype(int)
    )

    # --------------------------------------------------------
    # 6. DEFINE REGIMES
    # --------------------------------------------------------

    regimes = {

        "APR-JUN-2025": (
            "2025-04",
            "2025-06",
        ),

        "JUL-NOV-2025": (
            "2025-07",
            "2025-11",
        ),

        "DEC-MAR-2026": (
            "2025-12",
            "2026-03",
        ),
    }

    all_results = []

    # --------------------------------------------------------
    # 7. TRAIN RF AND XGBOOST
    # --------------------------------------------------------

    for model_name in [
        "RANDOM_FOREST_B",
        "XGBOOST_B",
    ]:

        print()
        print("=" * 60)
        print(
            "TRAINING:",
            model_name
        )
        print("=" * 60)

        pipeline = build_model(
            model_name
        )

        # IMPORTANT:
        # Fit ONLY on chronological TRAIN data.
        pipeline.fit(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # 8. FIXED VALIDATION THRESHOLD
        # ----------------------------------------------------

        validation_probability = (
            pipeline
            .predict_proba(
                X_validation
            )[:, 1]
        )

        threshold = float(
            np.quantile(
                validation_probability,
                0.90
            )
        )

        print()
        print(
            "Validation threshold:",
            round(
                threshold,
                6
            )
        )

        # ----------------------------------------------------
        # 9. EVALUATE EACH REGIME
        # ----------------------------------------------------

        for regime_name, (
            start_month,
            end_month
        ) in regimes.items():

            regime = df[
                (
                    df["anchor_month"]
                    >= start_month
                )
                &
                (
                    df["anchor_month"]
                    <= end_month
                )
            ].copy()

            if len(regime) == 0:

                print()
                print(
                    "WARNING:",
                    regime_name,
                    "has zero anchors"
                )

                continue

            X_regime = make_matrix(
                regime
            )

            y_regime = (
                regime["event"]
                .astype(int)
            )

            probability = (
                pipeline
                .predict_proba(
                    X_regime
                )[:, 1]
            )

            result = calculate_metrics(
                y_regime,
                probability,
                threshold,
            )

            result["model"] = (
                model_name
            )

            result["regime"] = (
                regime_name
            )

            result["threshold"] = (
                threshold
            )

            all_results.append(
                result
            )

            print()
            print("-" * 60)
            print(
                regime_name
            )
            print("-" * 60)

            print(
                "Anchors:",
                result["anchors"]
            )

            print(
                "Events:",
                result["events"]
            )

            print(
                "Event rate:",
                round(
                    result["event_rate"] * 100,
                    2
                ),
                "%"
            )

            print(
                "PR-AUC:",
                round(
                    result["pr_auc"],
                    4
                )
            )

            print(
                "ROC-AUC:",
                round(
                    result["roc_auc"],
                    4
                )
            )

            print(
                "Brier:",
                round(
                    result["brier"],
                    4
                )
            )

            print(
                "Precision:",
                round(
                    result["precision"],
                    4
                )
            )

            print(
                "Recall:",
                round(
                    result["recall"],
                    4
                )
            )

            print(
                "False alerts / 100:",
                round(
                    result[
                        "false_alerts_per_100"
                    ],
                    2
                )
            )

    # --------------------------------------------------------
    # 10. FINAL COMPARISON TABLE
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        all_results
    )

    print()
    print()
    print("=" * 60)
    print("FINAL RF vs XGB REGIME COMPARISON")
    print("=" * 60)

    for _, row in (
        results_df.iterrows()
    ):

        print(
            f"{row['regime']:<18} "
            f"{row['model']:<20} "
            f"PR={row['pr_auc']:.4f} "
            f"ROC={row['roc_auc']:.4f} "
            f"Brier={row['brier']:.4f} "
            f"Prec={row['precision']:.4f} "
            f"Recall={row['recall']:.4f} "
            f"FA/100={row['false_alerts_per_100']:.2f}"
        )

    # --------------------------------------------------------
    # 11. SAVE RESULTS
    # --------------------------------------------------------

    output_dir = (
        repo_root
        / "outputs"
        / "ml"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir
        / "PRAHARI_S1_RF_XGB_REGIME_AUDIT.csv"
    )

    results_df.to_csv(
        output_file,
        index=False
    )

    print()
    print("=" * 60)
    print("RESULT SAVED")
    print("=" * 60)

    print()
    print(output_file)
    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
