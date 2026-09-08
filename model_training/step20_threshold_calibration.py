# ================================================================
# PRAHARI STEP 20 - THRESHOLD SELECTION + CALIBRATION ANALYSIS
# ================================================================

import os
import warnings
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)

warnings.filterwarnings("ignore")

# ================================================================
# 1. PATH
# ================================================================

BASE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed"
)

INPUT_FILE = os.path.join(
    BASE,
    "project_month_ml_ready.csv"
)

OUTPUT_FILE = os.path.join(
    BASE,
    "step20_threshold_calibration_results.csv"
)

# ================================================================
# 2. LOAD DATA
# ================================================================

print("=" * 70)
print("PRAHARI STEP 20 - THRESHOLD + CALIBRATION ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE, low_memory=False)

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

print("\n1. DATA LOADED")
print("-" * 70)
print("Rows   :", len(df))
print("Columns:", len(df.columns))

# ================================================================
# 3. FEATURES
# ================================================================

FEATURES = [
    "agency",
    "state",

    "project_observation_count",
    "months_since_first_observation",

    "progress_current",
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",

    "progress_stalled",
    "stall_count_to_date",

    "expenditure_current",
    "expenditure_velocity",
    "expenditure_3m_change",

    "cost_ratio",
    "revised_cost_change",
    "revised_cost_ratio",

    "months_to_revised_doc",
    "months_from_original_doc",

    "progress_first_observation",

    "large_progress_jump",
    "very_large_progress_jump",
    "progress_decrease_flag",

    "expenditure_decrease_flag",
    "large_expenditure_change",
    "very_large_expenditure_change",

    "long_observation_gap",

    "progress_available",
    "expenditure_available"
]

TARGETS = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

# ================================================================
# 4. FEATURE CHECK
# ================================================================

print("\n2. FEATURE CHECK")
print("-" * 70)

missing_features = [
    x for x in FEATURES
    if x not in df.columns
]

missing_targets = [
    x for x in TARGETS
    if x not in df.columns
]

if missing_features:
    print("Missing features:", missing_features)
    raise ValueError("Feature check failed.")

if missing_targets:
    print("Missing targets:", missing_targets)
    raise ValueError("Target check failed.")

print("Features:", len(FEATURES))
print("Targets :", len(TARGETS))
print("Feature/target check: PASS")

# ================================================================
# 5. CANDIDATE 4 TEMPORAL SPLIT
# ================================================================

TRAIN_START = "2025-07"
TRAIN_END = "2025-10"

VAL_START = "2025-11"
VAL_END = "2025-12"

TEST_START = "2026-01"
TEST_END = "2026-06"

train_mask = (
    (df["reporting_month"] >= "2025-07-01") &
    (df["reporting_month"] <= "2025-10-31")
)

val_mask = (
    (df["reporting_month"] >= "2025-11-01") &
    (df["reporting_month"] <= "2025-12-31")
)

test_mask = (
    (df["reporting_month"] >= "2026-01-01") &
    (df["reporting_month"] <= "2026-06-30")
)

train_df = df.loc[train_mask].copy()
val_df = df.loc[val_mask].copy()
test_df = df.loc[test_mask].copy()

print("\n3. TEMPORAL SPLIT")
print("-" * 70)

print(
    f"TRAIN      : {TRAIN_START} -> {TRAIN_END}"
    f" | rows={len(train_df)}"
)

print(
    f"VALIDATION : {VAL_START} -> {VAL_END}"
    f" | rows={len(val_df)}"
)

print(
    f"TEST       : {TEST_START} -> {TEST_END}"
    f" | rows={len(test_df)}"
)

# ================================================================
# 6. FEATURE TYPES
# ================================================================

CATEGORICAL = [
    "agency",
    "state"
]

NUMERIC = [
    x for x in FEATURES
    if x not in CATEGORICAL
]

print("\n4. FEATURE TYPES")
print("-" * 70)
print("Categorical:", CATEGORICAL)
print("Numeric    :", len(NUMERIC))

# ================================================================
# 7. PREPROCESSING
# ================================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        )
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            NUMERIC
        ),
        (
            "categorical",
            categorical_pipeline,
            CATEGORICAL
        )
    ]
)

# ================================================================
# 8. MODELS
# ================================================================

logistic_model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=42
            )
        )
    ]
)

random_forest_model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=None,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1
            )
        )
    ]
)

MODELS = {
    "Logistic Regression": logistic_model,
    "Random Forest": random_forest_model
}

# ================================================================
# 9. THRESHOLDS
# ================================================================

THRESHOLDS = np.round(
    np.arange(0.10, 0.91, 0.05),
    2
)

# ================================================================
# 10. RESULT STORAGE
# ================================================================

all_results = []

# ================================================================
# 11. HORIZON-WISE ANALYSIS
# ================================================================

print("\n5. HORIZON-WISE THRESHOLD ANALYSIS")
print("=" * 70)

for target in TARGETS:

    print("\n")
    print("-" * 70)
    print(target)
    print("-" * 70)

    train_part = train_df[
        train_df[target].notna()
    ].copy()

    val_part = val_df[
        val_df[target].notna()
    ].copy()

    test_part = test_df[
        test_df[target].notna()
    ].copy()

    if len(train_part) == 0:
        print("No training data. Skipping.")
        continue

    if len(val_part) == 0:
        print("No validation data. Skipping.")
        continue

    if len(test_part) == 0:
        print("No test data. Skipping.")
        continue

    X_train = train_part[FEATURES]
    y_train = train_part[target].astype(int)

    X_val = val_part[FEATURES]
    y_val = val_part[target].astype(int)

    X_test = test_part[FEATURES]
    y_test = test_part[target].astype(int)

    print(
        f"Train:      n={len(y_train)}, "
        f"positive={y_train.sum()}, "
        f"negative={(y_train == 0).sum()}"
    )

    print(
        f"Validation: n={len(y_val)}, "
        f"positive={y_val.sum()}, "
        f"negative={(y_val == 0).sum()}"
    )

    print(
        f"Test:       n={len(y_test)}, "
        f"positive={y_test.sum()}, "
        f"negative={(y_test == 0).sum()}"
    )

    # ============================================================
    # TRAIN BOTH MODELS
    # ============================================================

    for model_name, model in MODELS.items():

        print("\nTraining:", model_name)

        model.fit(
            X_train,
            y_train
        )

        # --------------------------------------------------------
        # PROBABILITIES
        # --------------------------------------------------------

        val_prob = model.predict_proba(
            X_val
        )[:, 1]

        test_prob = model.predict_proba(
            X_test
        )[:, 1]

        # --------------------------------------------------------
        # DISCRIMINATION METRICS
        # --------------------------------------------------------

        val_roc_auc = roc_auc_score(
            y_val,
            val_prob
        )

        val_pr_auc = average_precision_score(
            y_val,
            val_prob
        )

        test_roc_auc = roc_auc_score(
            y_test,
            test_prob
        )

        test_pr_auc = average_precision_score(
            y_test,
            test_prob
        )

        # --------------------------------------------------------
        # BRIER
        # --------------------------------------------------------

        val_brier = brier_score_loss(
            y_val,
            val_prob
        )

        test_brier = brier_score_loss(
            y_test,
            test_prob
        )

        # --------------------------------------------------------
        # THRESHOLD SEARCH ON VALIDATION ONLY
        # --------------------------------------------------------

        threshold_rows = []

        for threshold in THRESHOLDS:

            val_pred = (
                val_prob >= threshold
            ).astype(int)

            precision = precision_score(
                y_val,
                val_pred,
                zero_division=0
            )

            recall = recall_score(
                y_val,
                val_pred,
                zero_division=0
            )

            f1 = f1_score(
                y_val,
                val_pred,
                zero_division=0
            )

            f2 = fbeta_score(
                y_val,
                val_pred,
                beta=2,
                zero_division=0
            )

            accuracy = accuracy_score(
                y_val,
                val_pred
            )

            threshold_rows.append(
                {
                    "threshold": threshold,
                    "validation_accuracy": accuracy,
                    "validation_precision": precision,
                    "validation_recall": recall,
                    "validation_f1": f1,
                    "validation_f2": f2
                }
            )

        threshold_df = pd.DataFrame(
            threshold_rows
        )

        # ========================================================
        # SELECT THRESHOLD
        # ========================================================

        # Primary criterion:
        # maximize F2 because PRAHARI is an early-warning system
        #
        # F2 gives more importance to recall than precision.

        best_row = threshold_df.loc[
            threshold_df["validation_f2"].idxmax()
        ]

        best_threshold = float(
            best_row["threshold"]
        )

        print(
            "\nSelected threshold:",
            best_threshold
        )

        print(
            "Validation F2:",
            round(
                best_row["validation_f2"],
                4
            )
        )

        print(
            "Validation Recall:",
            round(
                best_row["validation_recall"],
                4
            )
        )

        print(
            "Validation Precision:",
            round(
                best_row["validation_precision"],
                4
            )
        )

        # --------------------------------------------------------
        # FINAL TEST EVALUATION
        # --------------------------------------------------------

        test_pred = (
            test_prob >= best_threshold
        ).astype(int)

        test_accuracy = accuracy_score(
            y_test,
            test_pred
        )

        test_precision = precision_score(
            y_test,
            test_pred,
            zero_division=0
        )

        test_recall = recall_score(
            y_test,
            test_pred,
            zero_division=0
        )

        test_f1 = f1_score(
            y_test,
            test_pred,
            zero_division=0
        )

        test_f2 = fbeta_score(
            y_test,
            test_pred,
            beta=2,
            zero_division=0
        )

        cm = confusion_matrix(
            y_test,
            test_pred
        )

        tn, fp, fn, tp = cm.ravel()

        # --------------------------------------------------------
        # CALIBRATION SUMMARY
        # --------------------------------------------------------

        # Mean predicted probability
        # versus actual positive rate.

        mean_predicted_risk = np.mean(
            test_prob
        )

        actual_positive_rate = np.mean(
            y_test
        )

        calibration_gap = abs(
            mean_predicted_risk
            - actual_positive_rate
        )

        # --------------------------------------------------------
        # STORE FINAL RESULT
        # --------------------------------------------------------

        all_results.append(
            {
                "model": model_name,
                "horizon": target,

                "train_n": len(y_train),
                "validation_n": len(y_val),
                "test_n": len(y_test),

                "train_positive": int(
                    y_train.sum()
                ),

                "validation_positive": int(
                    y_val.sum()
                ),

                "test_positive": int(
                    y_test.sum()
                ),

                "selected_threshold": best_threshold,

                "validation_accuracy": float(
                    best_row[
                        "validation_accuracy"
                    ]
                ),

                "validation_precision": float(
                    best_row[
                        "validation_precision"
                    ]
                ),

                "validation_recall": float(
                    best_row[
                        "validation_recall"
                    ]
                ),

                "validation_f1": float(
                    best_row[
                        "validation_f1"
                    ]
                ),

                "validation_f2": float(
                    best_row[
                        "validation_f2"
                    ]
                ),

                "validation_roc_auc": float(
                    val_roc_auc
                ),

                "validation_pr_auc": float(
                    val_pr_auc
                ),

                "validation_brier": float(
                    val_brier
                ),

                "test_accuracy": float(
                    test_accuracy
                ),

                "test_precision": float(
                    test_precision
                ),

                "test_recall": float(
                    test_recall
                ),

                "test_f1": float(
                    test_f1
                ),

                "test_f2": float(
                    test_f2
                ),

                "test_roc_auc": float(
                    test_roc_auc
                ),

                "test_pr_auc": float(
                    test_pr_auc
                ),

                "test_brier": float(
                    test_brier
                ),

                "test_mean_predicted_risk": float(
                    mean_predicted_risk
                ),

                "test_actual_positive_rate": float(
                    actual_positive_rate
                ),

                "test_calibration_gap": float(
                    calibration_gap
                ),

                "test_tn": int(tn),
                "test_fp": int(fp),
                "test_fn": int(fn),
                "test_tp": int(tp)
            }
        )

        # --------------------------------------------------------
        # PRINT TEST RESULTS
        # --------------------------------------------------------

        print("\nTEST AFTER VALIDATION THRESHOLD")
        print("-" * 70)

        print(
            "Threshold :",
            round(best_threshold, 2)
        )

        print(
            "Accuracy  :",
            round(test_accuracy, 4)
        )

        print(
            "Precision :",
            round(test_precision, 4)
        )

        print(
            "Recall    :",
            round(test_recall, 4)
        )

        print(
            "F1        :",
            round(test_f1, 4)
        )

        print(
            "F2        :",
            round(test_f2, 4)
        )

        print(
            "ROC-AUC   :",
            round(test_roc_auc, 4)
        )

        print(
            "PR-AUC    :",
            round(test_pr_auc, 4)
        )

        print(
            "Brier     :",
            round(test_brier, 4)
        )

        print(
            "Mean predicted risk:",
            round(mean_predicted_risk, 4)
        )

        print(
            "Actual positive rate:",
            round(actual_positive_rate, 4)
        )

        print(
            "Calibration gap:",
            round(calibration_gap, 4)
        )

        print("\nTEST CONFUSION MATRIX")
        print(cm)

        print(
            f"TN={tn}, FP={fp}, "
            f"FN={fn}, TP={tp}"
        )

# ================================================================
# 12. SAVE RESULTS
# ================================================================

results_df = pd.DataFrame(
    all_results
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ================================================================
# 13. FINAL SUMMARY
# ================================================================

print("\n")
print("=" * 70)
print("STEP 20 COMPLETE")
print("=" * 70)

print("\nFINAL THRESHOLD + CALIBRATION RESULTS")
print("-" * 70)

display_columns = [
    "model",
    "horizon",
    "selected_threshold",
    "test_precision",
    "test_recall",
    "test_f1",
    "test_f2",
    "test_roc_auc",
    "test_pr_auc",
    "test_brier",
    "test_calibration_gap"
]

print(
    results_df[
        display_columns
    ].to_string(index=False)
)

print("\nResults saved to:")
print(OUTPUT_FILE)

print("\nResearch rules followed:")
print("1. Candidate 4 temporal split used.")
print("2. Unknown/censored labels remained NaN.")
print("3. Threshold selected using VALIDATION only.")
print("4. TEST set was not used for threshold selection.")
print("5. No random train/test split.")
print("6. F2 used as primary threshold criterion.")
print("7. T+5 remains subject to limited observability.")
print("8. Calibration gap reported.")
