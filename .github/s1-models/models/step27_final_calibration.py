import os
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss
)

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed"

DATA_FILE = os.path.join(
    BASE,
    "project_month_ml_ready.csv"
)

OUTPUT_CAL = os.path.join(
    BASE,
    "step27_calibration_results.csv"
)

OUTPUT_BINS = os.path.join(
    BASE,
    "step27_risk_bins.csv"
)

OUTPUT_TRAJ = os.path.join(
    BASE,
    "step27_risk_trajectory.csv"
)


# ============================================================
# SETTINGS
# ============================================================

TRAIN_START = "2025-07-01"
TRAIN_END = "2025-10-01"

VAL_START = "2025-11-01"
VAL_END = "2025-12-01"

TEST_START = "2026-01-01"
TEST_END = "2026-06-01"

TARGETS = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

FEATURES = [
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

# Same robust feature set used previously
ROBUST_FEATURES = [
    x for x in FEATURES
    if x not in [
        "months_to_revised_doc",
        "months_from_original_doc"
    ]
]

CATEGORICAL = [
    "agency",
    "state"
]

NUMERIC_FULL = [
    x for x in FEATURES
    if x not in CATEGORICAL
]

NUMERIC_ROBUST = [
    x for x in ROBUST_FEATURES
    if x not in CATEGORICAL
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 75)
print("PRAHARI STEP 27 - FINAL CALIBRATION")
print("=" * 75)

df = pd.read_csv(DATA_FILE)

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

print("\nRows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# TEMPORAL SPLIT
# ============================================================

train = df[
    (df["reporting_month"] >= TRAIN_START)
    &
    (df["reporting_month"] <= TRAIN_END)
].copy()

validation = df[
    (df["reporting_month"] >= VAL_START)
    &
    (df["reporting_month"] <= VAL_END)
].copy()

test = df[
    (df["reporting_month"] >= TEST_START)
    &
    (df["reporting_month"] <= TEST_END)
].copy()

print("\nTemporal split:")
print(
    "TRAIN:",
    len(train),
    TRAIN_START,
    "to",
    TRAIN_END
)

print(
    "VALIDATION:",
    len(validation),
    VAL_START,
    "to",
    VAL_END
)

print(
    "TEST:",
    len(test),
    TEST_START,
    "to",
    TEST_END
)


# ============================================================
# MODEL FUNCTION
# ============================================================

def create_model(features):

    categorical = [
        x for x in CATEGORICAL
        if x in features
    ]

    numeric = [
        x for x in features
        if x not in categorical
    ]

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
                "num",
                numeric_pipeline,
                numeric
            ),
            (
                "cat",
                categorical_pipeline,
                categorical
            )
        ]
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )


# ============================================================
# STORAGE
# ============================================================

calibration_results = []
risk_bins = []
trajectory = []


# ============================================================
# TRAIN EACH HORIZON
# ============================================================

for target in TARGETS:

    horizon = target.replace(
        "risk_by_t_plus_",
        "T+"
    )

    print("\n")
    print("=" * 75)
    print(horizon)
    print("=" * 75)

    train_valid = train[
        train[target].notna()
    ].copy()

    val_valid = validation[
        validation[target].notna()
    ].copy()

    test_valid = test[
        test[target].notna()
    ].copy()

    print(
        "Train:",
        len(train_valid),
        "| positives:",
        int(train_valid[target].sum())
    )

    print(
        "Validation:",
        len(val_valid),
        "| positives:",
        int(val_valid[target].sum())
    )

    print(
        "Test:",
        len(test_valid),
        "| positives:",
        int(test_valid[target].sum())
    )

    if (
        len(train_valid) == 0
        or train_valid[target].nunique() < 2
        or len(test_valid) == 0
    ):
        print("SKIPPED - insufficient labels")
        continue


    # ========================================================
    # FULL RF
    # ========================================================

    model = create_model(FEATURES)

    model.fit(
        train_valid[FEATURES],
        train_valid[target]
    )

    test_probability = model.predict_proba(
        test_valid[FEATURES]
    )[:, 1]

    y_test = test_valid[target].astype(int).values


    # ========================================================
    # METRICS
    # ========================================================

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

    mean_prediction = float(
        np.mean(test_probability)
    )

    actual_rate = float(
        np.mean(y_test)
    )

    calibration_gap = (
        mean_prediction - actual_rate
    )

    print(
        f"ROC-AUC: {roc:.4f}"
    )

    print(
        f"PR-AUC: {pr:.4f}"
    )

    print(
        f"Brier: {brier:.4f}"
    )

    print(
        f"Mean predicted risk: {mean_prediction:.4f}"
    )

    print(
        f"Actual event rate: {actual_rate:.4f}"
    )

    print(
        f"Calibration gap: {calibration_gap:.4f}"
    )


    calibration_results.append(
        {
            "horizon": horizon,
            "test_n": len(test_valid),
            "positive": int(y_test.sum()),
            "negative": int(
                len(y_test) - y_test.sum()
            ),
            "roc_auc": roc,
            "pr_auc": pr,
            "brier": brier,
            "mean_predicted_risk": mean_prediction,
            "actual_event_rate": actual_rate,
            "calibration_gap": calibration_gap
        }
    )


    # ========================================================
    # RISK BINS
    # ========================================================

    bins = [
        0.00,
        0.20,
        0.40,
        0.60,
        0.80,
        1.01
    ]

    labels = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "VERY_HIGH",
        "EXTREME"
    ]

    risk_category = pd.cut(
        test_probability,
        bins=bins,
        labels=labels,
        right=False
    )

    bin_df = pd.DataFrame(
        {
            "horizon": horizon,
            "risk_probability": test_probability,
            "actual_event": y_test,
            "risk_category": risk_category
        }
    )

    grouped = bin_df.groupby(
        "risk_category",
        observed=False
    )

    for category, group in grouped:

        if len(group) == 0:
            continue

        risk_bins.append(
            {
                "horizon": horizon,
                "risk_category": str(category),
                "n": len(group),
                "mean_predicted_risk": group[
                    "risk_probability"
                ].mean(),
                "actual_event_rate": group[
                    "actual_event"
                ].mean(),
                "positive_count": int(
                    group["actual_event"].sum()
                )
            }
        )


    # ========================================================
    # TRAJECTORY
    # ========================================================

    trajectory.append(
        {
            "horizon": horizon,
            "mean_predicted_risk": mean_prediction,
            "actual_event_rate": actual_rate
        }
    )


# ============================================================
# SAVE CALIBRATION
# ============================================================

calibration_df = pd.DataFrame(
    calibration_results
)

calibration_df.to_csv(
    OUTPUT_CAL,
    index=False
)


# ============================================================
# SAVE RISK BINS
# ============================================================

risk_bins_df = pd.DataFrame(
    risk_bins
)

risk_bins_df.to_csv(
    OUTPUT_BINS,
    index=False
)


# ============================================================
# SAVE TRAJECTORY
# ============================================================

trajectory_df = pd.DataFrame(
    trajectory
)

trajectory_df.to_csv(
    OUTPUT_TRAJ,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n")
print("=" * 75)
print("FINAL CALIBRATION SUMMARY")
print("=" * 75)

if len(calibration_df) > 0:

    print(
        calibration_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

print("\n")
print("=" * 75)
print("RISK BIN SUMMARY")
print("=" * 75)

if len(risk_bins_df) > 0:

    print(
        risk_bins_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

print("\n")
print("=" * 75)
print("RISK TRAJECTORY")
print("=" * 75)

if len(trajectory_df) > 0:

    print(
        trajectory_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}"
        )
    )

print("\n")
print("=" * 75)
print("FILES SAVED")
print("=" * 75)

print(OUTPUT_CAL)
print(OUTPUT_BINS)
print(OUTPUT_TRAJ)

print("\n")
print("=" * 75)
print("STEP 27 COMPLETE")
print("=" * 75)
