import warnings
import os
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)

from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed"

INPUT = os.path.join(
    BASE,
    "project_month_ml_ready.csv"
)

OUTPUT = os.path.join(
    BASE,
    "step25_xgboost_threshold_results.csv"
)

df = pd.read_csv(INPUT, low_memory=False)

print("=" * 70)
print("PRAHARI STEP 25 - XGBOOST THRESHOLD CALIBRATION")
print("=" * 70)

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

FEATURES = [
    x for x in FEATURES
    if x in df.columns
]

TARGETS = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

CATEGORICAL = [
    "agency",
    "state"
]

NUMERIC = [
    x for x in FEATURES
    if x not in CATEGORICAL
]

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

# Candidate 4
train_mask = (
    (df["reporting_month"] >= "2025-07-01")
    & (df["reporting_month"] <= "2025-10-01")
)

validation_mask = (
    (df["reporting_month"] >= "2025-11-01")
    & (df["reporting_month"] <= "2025-12-01")
)

test_mask = (
    (df["reporting_month"] >= "2026-01-01")
    & (df["reporting_month"] <= "2026-06-01")
)

print()
print("Features:", len(FEATURES))
print("Schedule proxies: REMOVED")
print("Threshold selection: VALIDATION")
print("Final evaluation: TEST")
print("Threshold objective: F2")

def make_model():

    numeric_pipe = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        )
    ])

    categorical_pipe = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore")
        )
    ])

    preprocessor = ColumnTransformer([
        (
            "numeric",
            numeric_pipe,
            NUMERIC
        ),
        (
            "categorical",
            categorical_pipe,
            CATEGORICAL
        )
    ])

    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )

    return Pipeline([
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            xgb
        )
    ])

results = []

thresholds = [
    round(x / 100, 2)
    for x in range(5, 96, 5)
]

for target in TARGETS:

    print()
    print("=" * 70)
    print("TARGET:", target)
    print("=" * 70)

    train = df.loc[
        train_mask & df[target].notna()
    ].copy()

    validation = df.loc[
        validation_mask & df[target].notna()
    ].copy()

    test = df.loc[
        test_mask & df[target].notna()
    ].copy()

    y_train = train[target].astype(int)
    y_validation = validation[target].astype(int)
    y_test = test[target].astype(int)

    print(
        "Train:",
        len(train),
        "Positive:",
        int(y_train.sum())
    )

    print(
        "Validation:",
        len(validation),
        "Positive:",
        int(y_validation.sum())
    )

    print(
        "Test:",
        len(test),
        "Positive:",
        int(y_test.sum())
    )

    model = make_model()

    model.fit(
        train[FEATURES],
        y_train
    )

    validation_probability = model.predict_proba(
        validation[FEATURES]
    )[:, 1]

    test_probability = model.predict_proba(
        test[FEATURES]
    )[:, 1]

    # --------------------------------------------------------
    # Select threshold ONLY on validation
    # --------------------------------------------------------

    threshold_rows = []

    for threshold in thresholds:

        validation_prediction = (
            validation_probability >= threshold
        ).astype(int)

        precision = precision_score(
            y_validation,
            validation_prediction,
            zero_division=0
        )

        recall = recall_score(
            y_validation,
            validation_prediction,
            zero_division=0
        )

        f1 = f1_score(
            y_validation,
            validation_prediction,
            zero_division=0
        )

        f2 = fbeta_score(
            y_validation,
            validation_prediction,
            beta=2,
            zero_division=0
        )

        threshold_rows.append({
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "f2": f2
        })

    threshold_df = pd.DataFrame(
        threshold_rows
    )

    best = threshold_df.loc[
        threshold_df["f2"].idxmax()
    ]

    best_threshold = float(
        best["threshold"]
    )

    print()
    print("BEST VALIDATION THRESHOLD:", best_threshold)
    print("Validation Precision:", round(best["precision"], 4))
    print("Validation Recall   :", round(best["recall"], 4))
    print("Validation F1       :", round(best["f1"], 4))
    print("Validation F2       :", round(best["f2"], 4))

    # --------------------------------------------------------
    # Locked threshold -> TEST
    # --------------------------------------------------------

    test_prediction = (
        test_probability >= best_threshold
    ).astype(int)

    precision = precision_score(
        y_test,
        test_prediction,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        test_prediction,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        test_prediction,
        zero_division=0
    )

    f2 = fbeta_score(
        y_test,
        test_prediction,
        beta=2,
        zero_division=0
    )

    roc = roc_auc_score(
        y_test,
        test_probability
    )

    pr = average_precision_score(
        y_test,
        test_probability
    )

    brier = brier_score_loss(
        y_test,
        test_probability
    )

    cm = confusion_matrix(
        y_test,
        test_prediction
    )

    print()
    print("LOCKED TEST RESULTS")
    print("Threshold:", best_threshold)
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1       :", round(f1, 4))
    print("F2       :", round(f2, 4))
    print("ROC-AUC  :", round(roc, 4))
    print("PR-AUC   :", round(pr, 4))
    print("Brier    :", round(brier, 4))

    print("Confusion Matrix:")
    print(cm)

    results.append({
        "horizon": target,
        "model": "XGBOOST_ROBUST",
        "threshold": best_threshold,
        "test_n": len(test),
        "test_positive": int(y_test.sum()),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "f2": f2,
        "roc_auc": roc,
        "pr_auc": pr,
        "brier": brier,
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1])
    })

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 70)
print("FINAL STEP 25 RESULTS")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print()
print("=" * 70)
print("STEP 25 COMPLETE")
print("=" * 70)

print()
print("Saved:")
print(OUTPUT)

print()
print("Research rule:")
print("Threshold was selected using validation only.")
print("The 2026 test set was evaluated using the locked threshold.")
