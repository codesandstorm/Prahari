import warnings
import os
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed"

INPUT = os.path.join(BASE, "project_month_ml_ready.csv")
OUTPUT = os.path.join(
    BASE,
    "step23_robust_feature_importance.csv"
)

df = pd.read_csv(INPUT, low_memory=False)

print("=" * 70)
print("PRAHARI STEP 23 - ROBUST FEATURE IMPORTANCE")
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

train_mask = (
    (df["reporting_month"] >= "2025-07-01")
    & (df["reporting_month"] <= "2025-10-01")
)

test_mask = (
    (df["reporting_month"] >= "2026-01-01")
    & (df["reporting_month"] <= "2026-06-01")
)

print()
print("Features:", len(FEATURES))
print("Schedule proxy features removed.")
print("Train: 2025-07 to 2025-10")
print("Test : 2026-01 to 2026-06")

results = []

for target in TARGETS:

    print()
    print("=" * 70)
    print("TARGET:", target)
    print("=" * 70)

    train = df.loc[
        train_mask & df[target].notna()
    ].copy()

    test = df.loc[
        test_mask & df[target].notna()
    ].copy()

    y_train = train[target].astype(int)
    y_test = test[target].astype(int)

    print(
        "Train:",
        len(train),
        "Positive:",
        int(y_train.sum())
    )

    print(
        "Test:",
        len(test),
        "Positive:",
        int(y_test.sum())
    )

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

    model = Pipeline([
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=300,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1
            )
        )
    ])

    model.fit(
        train[FEATURES],
        y_train
    )

    # --------------------------------------------------------
    # Built-in feature importance
    # --------------------------------------------------------

    rf = model.named_steps["model"]

    transformed_names = (
        model
        .named_steps["preprocessor"]
        .get_feature_names_out()
    )

    importance = rf.feature_importances_

    importance_df = pd.DataFrame({
        "transformed_feature": transformed_names,
        "importance": importance
    })

    importance_df["base_feature"] = (
        importance_df["transformed_feature"]
        .str.replace(
            r"^(numeric|categorical)__",
            "",
            regex=True
        )
    )

    grouped = (
        importance_df
        .groupby("base_feature", as_index=False)["importance"]
        .sum()
        .sort_values(
            "importance",
            ascending=False
        )
    )

    print()
    print("TOP 10 RANDOM FOREST FEATURES")

    print(
        grouped.head(10).to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}"
        )
    )

    # --------------------------------------------------------
    # Permutation importance on test
    # --------------------------------------------------------

    print()
    print("Calculating permutation importance...")

    permutation = permutation_importance(
        model,
        test[FEATURES],
        y_test,
        scoring="average_precision",
        n_repeats=5,
        random_state=42,
        n_jobs=-1
    )

    permutation_df = pd.DataFrame({
        "feature": FEATURES,
        "permutation_mean": permutation.importances_mean,
        "permutation_std": permutation.importances_std
    })

    permutation_df = permutation_df.sort_values(
        "permutation_mean",
        ascending=False
    )

    print()
    print("TOP 10 PERMUTATION FEATURES")

    print(
        permutation_df.head(10).to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}"
        )
    )

    # --------------------------------------------------------
    # Save both importance types
    # --------------------------------------------------------

    grouped["horizon"] = target
    grouped["importance_type"] = "random_forest"

    permutation_df["horizon"] = target
    permutation_df["importance_type"] = "permutation"

    grouped = grouped.rename(
        columns={
            "base_feature": "feature",
            "importance": "importance_value"
        }
    )

    permutation_df = permutation_df.rename(
        columns={
            "permutation_mean": "importance_value"
        }
    )

    combined = pd.concat(
        [
            grouped[
                [
                    "horizon",
                    "importance_type",
                    "feature",
                    "importance_value"
                ]
            ],
            permutation_df[
                [
                    "horizon",
                    "importance_type",
                    "feature",
                    "importance_value"
                ]
            ]
        ],
        ignore_index=True
    )

    results.append(combined)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

final_results = pd.concat(
    results,
    ignore_index=True
)

final_results.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 70)
print("STEP 23 COMPLETE")
print("=" * 70)

print()
print("Saved:")
print(OUTPUT)

print()
print(
    "Interpretation: these importance results show which "
    "non-schedule features contribute to prediction."
)

print(
    "Importance does NOT imply causality."
)
