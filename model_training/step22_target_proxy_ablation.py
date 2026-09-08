import warnings
import os
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, recall_score, f1_score, brier_score_loss

warnings.filterwarnings("ignore")

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed"
INPUT = os.path.join(BASE, "project_month_ml_ready.csv")
OUTPUT = os.path.join(BASE, "step22_target_proxy_ablation_results.csv")

df = pd.read_csv(INPUT, low_memory=False)

print("=" * 70)
print("PRAHARI STEP 22 - TARGET PROXY ABLATION")
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

FEATURES = [x for x in FEATURES if x in df.columns]

PROXY = [
    "months_to_revised_doc",
    "months_from_original_doc"
]

ABLATION_FEATURES = [
    x for x in FEATURES if x not in PROXY
]

TARGETS = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

CATEGORICAL = ["agency", "state"]

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

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

def make_model(features):

    categorical = [
        x for x in CATEGORICAL
        if x in features
    ]

    numeric = [
        x for x in features
        if x not in categorical
    ]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, categorical)
    ])

    rf = RandomForestClassifier(
        n_estimators=300,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", rf)
    ])

def evaluate(model, X_train, y_train, X_test, y_test):

    model.fit(X_train, y_train)

    probability = model.predict_proba(X_test)[:, 1]

    prediction = (probability >= 0.50).astype(int)

    return {
        "roc_auc": roc_auc_score(y_test, probability),
        "pr_auc": average_precision_score(y_test, probability),
        "recall": recall_score(y_test, prediction, zero_division=0),
        "f1": f1_score(y_test, prediction, zero_division=0),
        "brier": brier_score_loss(y_test, probability)
    }

print()
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Full features:", len(FEATURES))
print("Ablation features:", len(ABLATION_FEATURES))

results = []

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
        int(validation[target].sum())
    )

    print(
        "Test:",
        len(test),
        "Positive:",
        int(y_test.sum())
    )

    print()
    print("MODEL A - FULL FEATURES")

    model_a = make_model(FEATURES)

    result_a = evaluate(
        model_a,
        train[FEATURES],
        y_train,
        test[FEATURES],
        y_test
    )

    print("ROC-AUC:", round(result_a["roc_auc"], 4))
    print("PR-AUC :", round(result_a["pr_auc"], 4))
    print("Recall :", round(result_a["recall"], 4))
    print("F1     :", round(result_a["f1"], 4))
    print("Brier  :", round(result_a["brier"], 4))

    results.append({
        "horizon": target,
        "model": "FULL_FEATURES",
        **result_a
    })

    print()
    print("MODEL B - WITHOUT SCHEDULE PROXY")

    model_b = make_model(ABLATION_FEATURES)

    result_b = evaluate(
        model_b,
        train[ABLATION_FEATURES],
        y_train,
        test[ABLATION_FEATURES],
        y_test
    )

    print("ROC-AUC:", round(result_b["roc_auc"], 4))
    print("PR-AUC :", round(result_b["pr_auc"], 4))
    print("Recall :", round(result_b["recall"], 4))
    print("F1     :", round(result_b["f1"], 4))
    print("Brier  :", round(result_b["brier"], 4))

    results.append({
        "horizon": target,
        "model": "WITHOUT_SCHEDULE_PROXY",
        **result_b
    })

results_df = pd.DataFrame(results)

results_df.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 70)
print("FINAL STEP 22 RESULTS")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print()
print("=" * 70)
print("STEP 22 COMPLETE")
print("=" * 70)

print()
print("Interpretation:")
print("If performance drops substantially after removing the")
print("schedule variables, the original model relied heavily")
print("on current schedule information.")
print()
print("If performance remains strong, the model has evidence")
print("of learning broader project-risk signals.")
print()
print("This ablation does NOT prove causality.")
print()
print("Saved:")
print(OUTPUT)
