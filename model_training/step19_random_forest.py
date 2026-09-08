import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
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
# PRAHARI STEP 19 - RANDOM FOREST
# ==============================================================

INPUT_FILE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "project_month_ml_ready.csv"
)

OUTPUT_FILE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed/"
    "step19_random_forest_results.csv"
)

print("=" * 70)
print("PRAHARI STEP 19 - RANDOM FOREST")
print("=" * 70)


# ==============================================================
# 1. LOAD DATA
# ==============================================================

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print("\n1. DATA LOADED")
print("-" * 70)
print("Rows:", len(df))
print("Columns:", len(df.columns))


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
# 3. FEATURES
# ==============================================================
#
# NOTE:
# progress_5m_change is intentionally excluded because
# Step 18 showed zero observed values in the selected
# training window.
#
# This keeps Step 19 comparable and avoids a useless feature.
# ==============================================================

features = [

    # Context
    "agency",
    "state",

    # Project history
    "project_observation_count",
    "months_since_first_observation",

    # Progress trajectory
    "progress_current",
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",
    "progress_stalled",
    "stall_count_to_date",

    # Expenditure trajectory
    "expenditure_current",
    "expenditure_velocity",
    "expenditure_3m_change",

    # Cost
    "cost_ratio",
    "revised_cost_change",
    "revised_cost_ratio",

    # Schedule
    "months_to_revised_doc",
    "months_from_original_doc",

    # Data-quality / history
    "progress_first_observation",
    "large_progress_jump",
    "very_large_progress_jump",
    "progress_decrease_flag",
    "expenditure_decrease_flag",
    "large_expenditure_change",
    "very_large_expenditure_change",
    "long_observation_gap",

    # Availability indicators
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
# 4. FEATURE CHECK
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
    for f in missing_features:
        print(" -", f)

    raise SystemExit(1)


if missing_targets:

    print("\nERROR - Missing targets:")
    for t in missing_targets:
        print(" -", t)

    raise SystemExit(1)


print("\n2. FEATURE CHECK")
print("-" * 70)
print("Features:", len(features))
print("Targets:", len(targets))
print("Feature/target check: PASS")


# ==============================================================
# 5. TEMPORAL SPLIT
# ==============================================================

# Candidate 4
#
# TRAIN      : 2025-07 -> 2025-10
# VALIDATION : 2025-11 -> 2025-12
# TEST       : 2026-01 -> 2026-06
#
# IMPORTANT:
# No random splitting.
# ==============================================================

train_mask = (
    (df["reporting_month"] >= "2025-07-01") &
    (df["reporting_month"] <= "2025-10-01")
)

validation_mask = (
    (df["reporting_month"] >= "2025-11-01") &
    (df["reporting_month"] <= "2025-12-01")
)

test_mask = (
    (df["reporting_month"] >= "2026-01-01") &
    (df["reporting_month"] <= "2026-06-01")
)


train_df = df.loc[train_mask].copy()
validation_df = df.loc[validation_mask].copy()
test_df = df.loc[test_mask].copy()


print("\n3. TEMPORAL SPLIT")
print("-" * 70)

print(
    "TRAIN      : 2025-07 -> 2025-10",
    "| rows=", len(train_df)
)

print(
    "VALIDATION : 2025-11 -> 2025-12",
    "| rows=", len(validation_df)
)

print(
    "TEST       : 2026-01 -> 2026-06",
    "| rows=", len(test_df)
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


print("\n4. FEATURE TYPES")
print("-" * 70)
print("Categorical:", categorical_features)
print("Numeric:", len(numeric_features))


# ==============================================================
# 7. PREPROCESSING
# ==============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            )
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            )
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
# 8. RANDOM FOREST MODEL
# ==============================================================

rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            rf_model
        )
    ]
)


# ==============================================================
# 9. RESULTS STORAGE
# ==============================================================

results = []


# ==============================================================
# 10. HORIZON-WISE TRAINING
# ==============================================================

print("\n5. HORIZON-WISE RANDOM FOREST TRAINING")
print("=" * 70)


for horizon in targets:

    print("\n" + "-" * 70)
    print(horizon)
    print("-" * 70)


    # ----------------------------------------------------------
    # Keep only observable labels
    # ----------------------------------------------------------

    train_known = train_df[
        train_df[horizon].notna()
    ].copy()

    validation_known = validation_df[
        validation_df[horizon].notna()
    ].copy()

    test_known = test_df[
        test_df[horizon].notna()
    ].copy()


    # ----------------------------------------------------------
    # X and y
    # ----------------------------------------------------------

    X_train = train_known[features]
    y_train = train_known[horizon].astype(int)

    X_validation = validation_known[features]
    y_validation = validation_known[horizon].astype(int)

    X_test = test_known[features]
    y_test = test_known[horizon].astype(int)


    # ----------------------------------------------------------
    # Sample counts
    # ----------------------------------------------------------

    train_positive = int(y_train.sum())
    train_negative = int((y_train == 0).sum())

    validation_positive = int(y_validation.sum())
    validation_negative = int(
        (y_validation == 0).sum()
    )

    test_positive = int(y_test.sum())
    test_negative = int(
        (y_test == 0).sum()
    )


    print(
        f"Train:      n={len(y_train)}, "
        f"positive={train_positive}, "
        f"negative={train_negative}"
    )

    print(
        f"Validation: n={len(y_validation)}, "
        f"positive={validation_positive}, "
        f"negative={validation_negative}"
    )

    print(
        f"Test:       n={len(y_test)}, "
        f"positive={test_positive}, "
        f"negative={test_negative}"
    )


    # ----------------------------------------------------------
    # Safety checks
    # ----------------------------------------------------------

    if y_train.nunique() < 2:

        print(
            "SKIPPED - training contains only one class."
        )

        continue


    if y_validation.nunique() < 2:

        print(
            "WARNING - validation contains only one class."
        )


    if y_test.nunique() < 2:

        print(
            "WARNING - test contains only one class."
        )


    # ==========================================================
    # TRAIN RANDOM FOREST
    # ==========================================================

    print("\nTraining Random Forest...")

    pipeline.fit(
        X_train,
        y_train
    )

    print("Training complete.")


    # ==========================================================
    # PREDICTIONS
    # ==========================================================

    validation_probability = (
        pipeline.predict_proba(
            X_validation
        )[:, 1]
    )

    test_probability = (
        pipeline.predict_proba(
            X_test
        )[:, 1]
    )


    # Default threshold = 0.50
    validation_prediction = (
        validation_probability >= 0.50
    ).astype(int)

    test_prediction = (
        test_probability >= 0.50
    ).astype(int)


    # ==========================================================
    # VALIDATION METRICS
    # ==========================================================

    validation_accuracy = accuracy_score(
        y_validation,
        validation_prediction
    )

    validation_precision = precision_score(
        y_validation,
        validation_prediction,
        zero_division=0
    )

    validation_recall = recall_score(
        y_validation,
        validation_prediction,
        zero_division=0
    )

    validation_f1 = f1_score(
        y_validation,
        validation_prediction,
        zero_division=0
    )


    if y_validation.nunique() == 2:

        validation_roc_auc = roc_auc_score(
            y_validation,
            validation_probability
        )

        validation_pr_auc = average_precision_score(
            y_validation,
            validation_probability
        )

        validation_brier = brier_score_loss(
            y_validation,
            validation_probability
        )

    else:

        validation_roc_auc = np.nan
        validation_pr_auc = np.nan
        validation_brier = np.nan


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

    confusion = confusion_matrix(
        y_test,
        test_prediction,
        labels=[0, 1]
    )

    tn, fp, fn, tp = confusion.ravel()


    # ==========================================================
    # PRINT VALIDATION RESULTS
    # ==========================================================

    print("\nVALIDATION")

    print(
        f"Accuracy : {validation_accuracy:.4f}"
    )

    print(
        f"Precision: {validation_precision:.4f}"
    )

    print(
        f"Recall   : {validation_recall:.4f}"
    )

    print(
        f"F1       : {validation_f1:.4f}"
    )

    print(
        f"ROC-AUC  : {validation_roc_auc:.4f}"
    )

    print(
        f"PR-AUC   : {validation_pr_auc:.4f}"
    )

    print(
        f"Brier    : {validation_brier:.4f}"
    )


    # ==========================================================
    # PRINT TEST RESULTS
    # ==========================================================

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


    # ==========================================================
    # CONFUSION MATRIX
    # ==========================================================

    print("\nTEST CONFUSION MATRIX")

    print(confusion)

    print(
        f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
    )


    # ==========================================================
    # SAVE RESULT
    # ==========================================================

    results.append({

        "model": "RandomForest",

        "horizon": horizon,

        "train_n": len(y_train),
        "train_positive": train_positive,
        "train_negative": train_negative,

        "validation_n": len(y_validation),
        "validation_positive": validation_positive,
        "validation_negative": validation_negative,

        "test_n": len(y_test),
        "test_positive": test_positive,
        "test_negative": test_negative,

        "validation_accuracy":
            validation_accuracy,

        "validation_precision":
            validation_precision,

        "validation_recall":
            validation_recall,

        "validation_f1":
            validation_f1,

        "validation_roc_auc":
            validation_roc_auc,

        "validation_pr_auc":
            validation_pr_auc,

        "validation_brier":
            validation_brier,

        "test_accuracy":
            test_accuracy,

        "test_precision":
            test_precision,

        "test_recall":
            test_recall,

        "test_f1":
            test_f1,

        "test_roc_auc":
            test_roc_auc,

        "test_pr_auc":
            test_pr_auc,

        "test_brier":
            test_brier,

        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp
    })


# ==============================================================
# 11. SAVE RESULTS
# ==============================================================

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==============================================================
# 12. FINAL SUMMARY
# ==============================================================

print("\n" + "=" * 70)
print("STEP 19 COMPLETE")
print("=" * 70)

print("\nFINAL RANDOM FOREST TEST RESULTS")
print("-" * 70)

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
print("1. Candidate 4 temporal split used.")
print("2. Unknown/censored labels remained NaN.")
print("3. No random train/test split.")
print("4. Numeric missing values median-imputed.")
print("5. Agency/state one-hot encoded.")
print("6. Random Forest uses class_weight='balanced'.")
print("7. progress_5m_change excluded due zero training availability.")
print("8. T+5 remains subject to limited observability.")
