import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss
)

# ==============================================================
# PRAHARI STEP 18 - LOGISTIC REGRESSION BASELINE
# ==============================================================

INPUT_FILE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "project_month_ml_ready.csv"
)

OUTPUT_FILE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "step18_logistic_results.csv"
)

print("=" * 70)
print("PRAHARI STEP 18 - LOGISTIC REGRESSION BASELINE")
print("=" * 70)


# ==============================================================
# 1. LOAD DATA
# ==============================================================

df = pd.read_csv(INPUT_FILE)

print("\n1. DATA LOADED")
print("-" * 70)

print("Rows:", len(df))
print("Columns:", len(df))


# ==============================================================
# 2. DATE PREPARATION
# ==============================================================

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

df = df.sort_values(
    ["reporting_month", "canonical_project_id"]
).reset_index(drop=True)

print("\nReporting period:")
print(
    df["reporting_month"].min().strftime("%Y-%m"),
    "to",
    df["reporting_month"].max().strftime("%Y-%m")
)


# ==============================================================
# 3. FINAL FEATURE SET
# ==============================================================

features = [
    "agency",
    "state",

    "project_observation_count",
    "months_since_first_observation",

    "progress_current",
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",
    "progress_5m_change",
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


targets = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]


# ==============================================================
# 4. VERIFY FEATURES
# ==============================================================

missing_features = [
    f for f in features
    if f not in df.columns
]

missing_targets = [
    t for t in targets
    if t not in df.columns
]

if missing_features:
    print("\nERROR - Missing features:")
    print(missing_features)
    raise SystemExit

if missing_targets:
    print("\nERROR - Missing targets:")
    print(missing_targets)
    raise SystemExit

print("\n2. FEATURE CHECK")
print("-" * 70)

print("Features:", len(features))
print("Targets:", len(targets))
print("Feature/target check: PASS")


# ==============================================================
# 5. TEMPORAL SPLIT
# ==============================================================

TRAIN_START = "2025-07"
TRAIN_END = "2025-10"

VAL_START = "2025-11"
VAL_END = "2025-12"

TEST_START = "2026-01"
TEST_END = "2026-06"


train_mask = (
    (df["reporting_month"] >= "2025-07-01") &
    (df["reporting_month"] <= "2025-10-01")
)

val_mask = (
    (df["reporting_month"] >= "2025-11-01") &
    (df["reporting_month"] <= "2025-12-01")
)

test_mask = (
    (df["reporting_month"] >= "2026-01-01") &
    (df["reporting_month"] <= "2026-06-01")
)

train_df = df.loc[train_mask].copy()
val_df = df.loc[val_mask].copy()
test_df = df.loc[test_mask].copy()

print("\n3. TEMPORAL SPLIT")
print("-" * 70)

print(
    f"TRAIN      : {TRAIN_START} -> {TRAIN_END} "
    f"| rows={len(train_df)}"
)

print(
    f"VALIDATION : {VAL_START} -> {VAL_END} "
    f"| rows={len(val_df)}"
)

print(
    f"TEST       : {TEST_START} -> {TEST_END} "
    f"| rows={len(test_df)}"
)


# ==============================================================
# 6. FEATURE TYPES
# ==============================================================

categorical_features = [
    "agency",
    "state"
]

numeric_features = [
    f for f in features
    if f not in categorical_features
]


# ==============================================================
# 7. PREPROCESSING
# ==============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
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
            "onehot",
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
            numeric_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    ]
)


# ==============================================================
# 8. LOGISTIC REGRESSION
# ==============================================================

model = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    random_state=42
)


pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# ==============================================================
# 9. TRAIN HORIZON-BY-HORIZON
# ==============================================================

results = []

print("\n4. HORIZON-WISE MODEL TRAINING")
print("=" * 70)


for horizon in targets:

    print("\n" + "-" * 70)
    print(horizon)
    print("-" * 70)

    # ----------------------------------------------------------
    # Remove unknown/censored labels
    # ----------------------------------------------------------

    train_known = train_df[
        train_df[horizon].notna()
    ].copy()

    val_known = val_df[
        val_df[horizon].notna()
    ].copy()

    test_known = test_df[
        test_df[horizon].notna()
    ].copy()


    # ----------------------------------------------------------
    # Target conversion
    # ----------------------------------------------------------

    y_train = train_known[horizon].astype(int)
    y_val = val_known[horizon].astype(int)
    y_test = test_known[horizon].astype(int)


    X_train = train_known[features]
    X_val = val_known[features]
    X_test = test_known[features]


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


    # ----------------------------------------------------------
    # Safety check
    # ----------------------------------------------------------

    if y_train.nunique() < 2:
        print("SKIPPED - training has only one class.")
        continue

    if y_val.nunique() < 2:
        print("WARNING - validation has only one class.")

    if y_test.nunique() < 2:
        print("WARNING - test has only one class.")


    # ----------------------------------------------------------
    # TRAIN
    # ----------------------------------------------------------

    pipeline.fit(
        X_train,
        y_train
    )


    # ----------------------------------------------------------
    # PREDICTIONS
    # ----------------------------------------------------------

    val_probability = pipeline.predict_proba(
        X_val
    )[:, 1]

    test_probability = pipeline.predict_proba(
        X_test
    )[:, 1]


    val_prediction = (
        val_probability >= 0.50
    ).astype(int)

    test_prediction = (
        test_probability >= 0.50
    ).astype(int)


    # ==========================================================
    # VALIDATION METRICS
    # ==========================================================

    val_accuracy = accuracy_score(
        y_val,
        val_prediction
    )

    val_precision = precision_score(
        y_val,
        val_prediction,
        zero_division=0
    )

    val_recall = recall_score(
        y_val,
        val_prediction,
        zero_division=0
    )

    val_f1 = f1_score(
        y_val,
        val_prediction,
        zero_division=0
    )

    if y_val.nunique() == 2:
        val_roc_auc = roc_auc_score(
            y_val,
            val_probability
        )

        val_pr_auc = average_precision_score(
            y_val,
            val_probability
        )

        val_brier = brier_score_loss(
            y_val,
            val_probability
        )
    else:
        val_roc_auc = np.nan
        val_pr_auc = np.nan
        val_brier = np.nan


    # ==========================================================
    # TEST METRICS
    # ==========================================================

    test_accuracy = accuracy_score(
        y_test,
        test_prediction
    )

    test_precision = precision_score(
        y_test,
        test_prediction,
        zero_division=0
    )

    test_recall = recall_score(
        y_test,
        test_prediction,
        zero_division=0
    )

    test_f1 = f1_score(
        y_test,
        test_prediction,
        zero_division=0
    )


    if y_test.nunique() == 2:

        test_roc_auc = roc_auc_score(
            y_test,
            test_probability
        )

        test_pr_auc = average_precision_score(
            y_test,
            test_probability
        )

        test_brier = brier_score_loss(
            y_test,
            test_probability
        )

    else:

        test_roc_auc = np.nan
        test_pr_auc = np.nan
        test_brier = np.nan


    # ==========================================================
    # CONFUSION MATRIX
    # ==========================================================

    cm = confusion_matrix(
        y_test,
        test_prediction,
        labels=[0, 1]
    )

    tn, fp, fn, tp = cm.ravel()


    # ==========================================================
    # PRINT RESULTS
    # ==========================================================

    print("\nVALIDATION")
    print(
        f"Accuracy : {val_accuracy:.4f}"
    )
    print(
        f"Precision: {val_precision:.4f}"
    )
    print(
        f"Recall   : {val_recall:.4f}"
    )
    print(
        f"F1       : {val_f1:.4f}"
    )
    print(
        f"ROC-AUC  : {val_roc_auc:.4f}"
    )
    print(
        f"PR-AUC   : {val_pr_auc:.4f}"
    )
    print(
        f"Brier    : {val_brier:.4f}"
    )


    print("\nTEST")
    print(
        f"Accuracy : {test_accuracy:.4f}"
    )
    print(
        f"Precision: {test_precision:.4f}"
    )
    print(
        f"Recall   : {test_recall:.4f}"
    )
    print(
        f"F1       : {test_f1:.4f}"
    )
    print(
        f"ROC-AUC  : {test_roc_auc:.4f}"
    )
    print(
        f"PR-AUC   : {test_pr_auc:.4f}"
    )
    print(
        f"Brier    : {test_brier:.4f}"
    )

    print("\nTEST CONFUSION MATRIX")
    print(cm)

    print(
        f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
    )


    # ==========================================================
    # SAVE RESULTS
    # ==========================================================

    results.append({

        "horizon": horizon,

        "train_n": len(y_train),
        "train_positive": int(y_train.sum()),
        "train_negative": int((y_train == 0).sum()),

        "validation_n": len(y_val),
        "validation_positive": int(y_val.sum()),
        "validation_negative": int((y_val == 0).sum()),

        "test_n": len(y_test),
        "test_positive": int(y_test.sum()),
        "test_negative": int((y_test == 0).sum()),

        "validation_accuracy": val_accuracy,
        "validation_precision": val_precision,
        "validation_recall": val_recall,
        "validation_f1": val_f1,
        "validation_roc_auc": val_roc_auc,
        "validation_pr_auc": val_pr_auc,
        "validation_brier": val_brier,

        "test_accuracy": test_accuracy,
        "test_precision": test_precision,
        "test_recall": test_recall,
        "test_f1": test_f1,
        "test_roc_auc": test_roc_auc,
        "test_pr_auc": test_pr_auc,
        "test_brier": test_brier,

        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp
    })


# ==============================================================
# 10. SAVE RESULTS
# ==============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==============================================================
# 11. FINAL SUMMARY
# ==============================================================

print("\n" + "=" * 70)
print("STEP 18 COMPLETE")
print("=" * 70)

print("\nFINAL TEST RESULTS")

print(
    results_df[
        [
            "horizon",
            "test_n",
            "test_positive",
            "test_roc_auc",
            "test_pr_auc",
            "test_recall",
            "test_f1",
            "test_brier"
        ]
    ].to_string(index=False)
)

print("\nResults saved to:")
print(OUTPUT_FILE)

print("\nResearch notes:")
print("1. Temporal split used.")
print("2. Unknown labels remained NaN.")
print("3. No random train/test split.")
print("4. Median imputation performed inside pipeline.")
print("5. Agency/state one-hot encoded.")
print("6. class_weight='balanced' used.")
print("7. T+5 results must be interpreted cautiously.")
