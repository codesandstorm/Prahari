import warnings
import os
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    recall_score,
    f1_score,
    brier_score_loss
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
    "step24_xgboost_robust_results.csv"
)

df = pd.read_csv(
    INPUT,
    low_memory=False
)

print("=" * 70)
print("PRAHARI STEP 24 - XGBOOST ROBUST MODEL")
print("=" * 70)

# ------------------------------------------------------------
# Robust feature set
# Schedule proxy variables intentionally excluded
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# Candidate 4 temporal split
# ------------------------------------------------------------

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
print("Rows:", len(df))
print("Features:", len(FEATURES))
print("Schedule proxy features: REMOVED")
print()
print("TRAIN      : 2025-07 to 2025-10")
print("VALIDATION : 2025-11 to 2025-12")
print("TEST       : 2026-01 to 2026-06")

# ------------------------------------------------------------
# XGBoost model
# ------------------------------------------------------------

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
            model
        )
    ])

# ------------------------------------------------------------
# Evaluation
# ------------------------------------------------------------

def evaluate(model, X_train, y_train, X_test, y_test):

    model.fit(
        X_train,
        y_train
    )

    probability = model.predict_proba(
        X_test
    )[:, 1]

    prediction = (
        probability >= 0.50
    ).astype(int)

    return {
        "roc_auc": roc_auc_score(
            y_test,
            probability
        ),
        "pr_auc": average_precision_score(
            y_test,
            probability
        ),
        "recall": recall_score(
            y_test,
            prediction,
            zero_division=0
        ),
        "f1": f1_score(
            y_test,
            prediction,
            zero_division=0
        ),
        "brier": brier_score_loss(
            y_test,
            probability
        )
    }

results = []

# ------------------------------------------------------------
# Train one model per horizon
# ------------------------------------------------------------

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

    metrics = evaluate(
        model,
        train[FEATURES],
        y_train,
        test[FEATURES],
        y_test
    )

    print()
    print("XGBOOST ROBUST RESULTS")

    print(
        "ROC-AUC:",
        round(metrics["roc_auc"], 4)
    )

    print(
        "PR-AUC :",
        round(metrics["pr_auc"], 4)
    )

    print(
        "Recall :",
        round(metrics["recall"], 4)
    )

    print(
        "F1     :",
        round(metrics["f1"], 4)
    )

    print(
        "Brier  :",
        round(metrics["brier"], 4)
    )

    results.append({
        "horizon": target,
        "model": "XGBOOST_ROBUST",
        "test_n": len(test),
        "test_positive": int(y_test.sum()),
        **metrics
    })

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 70)
print("FINAL STEP 24 RESULTS")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print()
print("=" * 70)
print("STEP 24 COMPLETE")
print("=" * 70)

print()
print("Saved:")
print(OUTPUT)

print()
print("Important:")
print("These results use the robust feature set.")
print("Schedule proxy variables were intentionally excluded.")
print("Threshold = 0.50.")
print("This is a model comparison, not final threshold tuning.")
