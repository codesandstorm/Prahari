# ================================================================
# PRAHARI STEP 21 - FEATURE IMPORTANCE + SHAP ANALYSIS
# ================================================================

import os
import warnings
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")

# SHAP
try:
    import shap
except ImportError:
    print("SHAP is not installed.")
    print("Run:")
    print("pip install shap")
    raise


# ================================================================
# 1. PATHS
# ================================================================

BASE = (
    "data/processed/"
    "longitudinal_2023_07_2026_06_mixed"
)

INPUT_FILE = os.path.join(
    BASE,
    "project_month_ml_ready.csv"
)

OUTPUT_FEATURE_IMPORTANCE = os.path.join(
    BASE,
    "step21_random_forest_feature_importance.csv"
)

OUTPUT_PERMUTATION = os.path.join(
    BASE,
    "step21_random_forest_permutation_importance.csv"
)

OUTPUT_SHAP = os.path.join(
    BASE,
    "step21_random_forest_shap_importance.csv"
)


# ================================================================
# 2. LOAD DATA
# ================================================================

print("=" * 70)
print("PRAHARI STEP 21 - FEATURE IMPORTANCE + SHAP")
print("=" * 70)

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

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
    print("Missing features:")
    for x in missing_features:
        print(" -", x)
    raise ValueError("Feature check failed.")

if missing_targets:
    print("Missing targets:")
    for x in missing_targets:
        print(" -", x)
    raise ValueError("Target check failed.")

print("Features:", len(FEATURES))
print("Targets :", len(TARGETS))
print("Feature/target check: PASS")


# ================================================================
# 5. CANDIDATE 4 TEMPORAL SPLIT
# ================================================================

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
    "TRAIN      : 2025-07 -> 2025-10",
    "| rows =", len(train_df)
)

print(
    "VALIDATION : 2025-11 -> 2025-12",
    "| rows =", len(val_df)
)

print(
    "TEST       : 2026-01 -> 2026-06",
    "| rows =", len(test_df)
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
# 8. RANDOM FOREST
# ================================================================

rf = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


# ================================================================
# 9. HORIZON-WISE ANALYSIS
# ================================================================

all_imp = []
all_perm = []
all_shap = []

print("\n5. HORIZON-WISE FEATURE ANALYSIS")
print("=" * 70)


for target in TARGETS:

    print("\n")
    print("-" * 70)
    print(target)
    print("-" * 70)

    # ------------------------------------------------------------
    # TRAIN DATA
    # ------------------------------------------------------------

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
        "Train:",
        len(y_train),
        "| Positive:",
        int(y_train.sum())
    )

    print(
        "Validation:",
        len(y_val)
    )

    print(
        "Test:",
        len(y_test),
        "| Positive:",
        int(y_test.sum())
    )


    # ============================================================
    # FIT PREPROCESSOR
    # ============================================================

    X_train_processed = preprocessor.fit_transform(
        X_train
    )

    X_test_processed = preprocessor.transform(
        X_test
    )


    # ============================================================
    # FEATURE NAMES
    # ============================================================

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )


    # ============================================================
    # CONVERT SPARSE MATRIX
    # ============================================================

    if hasattr(
        X_train_processed,
        "toarray"
    ):
        X_train_dense = (
            X_train_processed.toarray()
        )
    else:
        X_train_dense = (
            X_train_processed
        )

    if hasattr(
        X_test_processed,
        "toarray"
    ):
        X_test_dense = (
            X_test_processed.toarray()
        )
    else:
        X_test_dense = (
            X_test_processed
        )


    # ============================================================
    # TRAIN RANDOM FOREST
    # ============================================================

    print("\nTraining Random Forest...")

    rf.fit(
        X_train_dense,
        y_train
    )

    print("Training complete.")


    # ============================================================
    # 5A. BUILT-IN RANDOM FOREST IMPORTANCE
    # ============================================================

    importance = rf.feature_importances_

    importance_df = pd.DataFrame(
        {
            "encoded_feature": feature_names,
            "importance": importance,
            "horizon": target
        }
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False
        )
    )

    # ------------------------------------------------------------
    # Save encoded-level importance
    # ------------------------------------------------------------

    all_imp.append(
        importance_df
    )

    print("\nTOP 15 RANDOM FOREST FEATURES")
    print("-" * 70)

    print(
        importance_df
        .head(15)
        .to_string(index=False)
    )


    # ============================================================
    # 5B. PERMUTATION IMPORTANCE
    # ============================================================

    print(
        "\nCalculating permutation importance..."
    )

    # Use TEST only for interpretive analysis.
    #
    # IMPORTANT:
    # This does NOT change model selection,
    # threshold selection, or hyperparameters.
    #
    # It is used only to understand the final
    # held-out predictions.

    perm = permutation_importance(
        rf,
        X_test_dense,
        y_test,
        scoring="average_precision",
        n_repeats=10,
        random_state=42,
        n_jobs=-1
    )

    perm_df = pd.DataFrame(
        {
            "encoded_feature": feature_names,
            "permutation_mean": perm.importances_mean,
            "permutation_std": perm.importances_std,
            "horizon": target
        }
    )

    perm_df = (
        perm_df
        .sort_values(
            "permutation_mean",
            ascending=False
        )
    )

    all_perm.append(
        perm_df
    )

    print("\nTOP 15 PERMUTATION FEATURES")
    print("-" * 70)

    print(
        perm_df
        .head(15)
        .to_string(index=False)
    )


    # ============================================================
    # 5C. SHAP
    # ============================================================

    print("\nCalculating SHAP values...")

    # Sample the test data for SHAP to keep computation reasonable.
    #
    # Maximum 500 observations per horizon.

    shap_n = min(
        500,
        len(X_test_dense)
    )

    rng = np.random.RandomState(42)

    if len(X_test_dense) > shap_n:

        shap_indices = rng.choice(
            len(X_test_dense),
            size=shap_n,
            replace=False
        )

        X_shap = X_test_dense[
            shap_indices
        ]

    else:

        X_shap = X_test_dense


    explainer = shap.TreeExplainer(
        rf
    )

    shap_values = explainer.shap_values(
        X_shap
    )

    # ------------------------------------------------------------
    # SHAP version compatibility
    # ------------------------------------------------------------

    if isinstance(
        shap_values,
        list
    ):

        # Binary classifier:
        # class 1 = risk

        shap_matrix = shap_values[1]

    elif len(shap_values.shape) == 3:

        # Newer SHAP format:
        # samples x features x classes

        shap_matrix = shap_values[
            :, :, 1
        ]

    else:

        shap_matrix = shap_values


    mean_abs_shap = np.mean(
        np.abs(shap_matrix),
        axis=0
    )

    mean_signed_shap = np.mean(
        shap_matrix,
        axis=0
    )

    shap_df = pd.DataFrame(
        {
            "encoded_feature": feature_names,
            "mean_abs_shap": mean_abs_shap,
            "mean_signed_shap": mean_signed_shap,
            "horizon": target
        }
    )

    shap_df = (
        shap_df
        .sort_values(
            "mean_abs_shap",
            ascending=False
        )
    )

    all_shap.append(
        shap_df
    )

    print("\nTOP 15 SHAP FEATURES")
    print("-" * 70)

    print(
        shap_df
        .head(15)
        .to_string(index=False)
    )


# ================================================================
# 10. SAVE ALL RESULTS
# ================================================================

print("\n")
print("=" * 70)
print("6. SAVING RESULTS")
print("=" * 70)


if all_imp:

    final_imp = pd.concat(
        all_imp,
        ignore_index=True
    )

    final_imp.to_csv(
        OUTPUT_FEATURE_IMPORTANCE,
        index=False
    )

    print(
        "Random Forest importance saved:"
    )

    print(
        OUTPUT_FEATURE_IMPORTANCE
    )


if all_perm:

    final_perm = pd.concat(
        all_perm,
        ignore_index=True
    )

    final_perm.to_csv(
        OUTPUT_PERMUTATION,
        index=False
    )

    print(
        "Permutation importance saved:"
    )

    print(
        OUTPUT_PERMUTATION
    )


if all_shap:

    final_shap = pd.concat(
        all_shap,
        ignore_index=True
    )

    final_shap.to_csv(
        OUTPUT_SHAP,
        index=False
    )

    print(
        "SHAP importance saved:"
    )

    print(
        OUTPUT_SHAP
    )


# ================================================================
# 11. HORIZON COMPARISON
# ================================================================

print("\n")
print("=" * 70)
print("7. TOP SHAP FEATURES BY HORIZON")
print("=" * 70)

if all_shap:

    for target in TARGETS:

        subset = final_shap[
            final_shap["horizon"] == target
        ].head(10)

        print("\n")
        print(target)
        print("-" * 50)

        print(
            subset[
                [
                    "encoded_feature",
                    "mean_abs_shap",
                    "mean_signed_shap"
                ]
            ].to_string(index=False)
        )


# ================================================================
# 12. RESEARCH INTERPRETATION NOTES
# ================================================================

print("\n")
print("=" * 70)
print("STEP 21 COMPLETE")
print("=" * 70)

print("\nResearch interpretation rules:")
print("1. Random Forest feature importance is model-specific.")
print("2. Permutation importance measures predictive contribution.")
print("3. SHAP measures contribution to individual predictions.")
print("4. High SHAP importance does not automatically imply causality.")
print("5. Correlated features can split importance.")
print("6. Agency/state effects require domain interpretation.")
print("7. Future/outcome variables must never be treated as predictors.")
print("8. Feature importance must be interpreted with leakage audit.")
print("9. T+5 interpretation remains limited by observability.")
print("10. Importance does not prove that a feature causes project delay.")

print("\nOutput files:")
print(OUTPUT_FEATURE_IMPORTANCE)
print(OUTPUT_PERMUTATION)
print(OUTPUT_SHAP)
