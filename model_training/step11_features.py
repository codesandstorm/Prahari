import pandas as pd
import numpy as np

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed/"

INPUT = BASE + "project_month_labels.csv"
OUTPUT = BASE + "project_month_features.csv"

print("=" * 60)
print("PRAHARI STEP 11 - FEATURE ENGINEERING")
print("=" * 60)

df = pd.read_csv(INPUT, low_memory=False)

print("Rows loaded:", len(df))

# ------------------------------------------------------------
# DATE CONVERSION
# ------------------------------------------------------------

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    format="%Y-%m",
    errors="coerce"
)

df["revised_doc_date"] = pd.to_datetime(
    df["reported_revised_doc"],
    format="%m/%Y",
    errors="coerce"
)

df["original_doc_date"] = pd.to_datetime(
    df["reported_original_target_doc"],
    format="%m/%Y",
    errors="coerce"
)

# ------------------------------------------------------------
# NUMERIC CONVERSION
# ------------------------------------------------------------

numeric_cols = [
    "reported_physical_progress",
    "reported_cumulative_expenditure",
    "reported_original_cost",
    "reported_revised_cost"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# ------------------------------------------------------------
# SORT
# ------------------------------------------------------------

df = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).copy()

g = df.groupby("canonical_project_id")

# ------------------------------------------------------------
# 1. CURRENT PROGRESS
# ------------------------------------------------------------

df["progress_current"] = (
    df["reported_physical_progress"]
)

# Previous progress
df["progress_previous"] = (
    g["reported_physical_progress"]
    .shift(1)
)

# Month gap
df["month_gap"] = (
    df["reporting_month"]
    .dt.to_period("M")
    .astype("int64")
    -
    df.groupby("canonical_project_id")[
        "reporting_month"
    ]
    .shift(1)
    .dt.to_period("M")
    .astype("int64")
)

# ------------------------------------------------------------
# 2. PROGRESS VELOCITY
# ------------------------------------------------------------

df["progress_velocity"] = (
    (
        df["progress_current"]
        - df["progress_previous"]
    )
    / df["month_gap"]
)

# ------------------------------------------------------------
# 3. PROGRESS ACCELERATION
# ------------------------------------------------------------

df["previous_velocity"] = (
    g["progress_velocity"]
    .shift(1)
)

df["progress_acceleration"] = (
    df["progress_velocity"]
    - df["previous_velocity"]
)

# ------------------------------------------------------------
# 4. 3-MONTH PROGRESS CHANGE
# ------------------------------------------------------------

df["progress_3m_change"] = (
    df["progress_current"]
    - g["reported_physical_progress"].shift(3)
)

# ------------------------------------------------------------
# 5. 5-MONTH PROGRESS CHANGE
# ------------------------------------------------------------

df["progress_5m_change"] = (
    df["progress_current"]
    - g["reported_physical_progress"].shift(5)
)

# ------------------------------------------------------------
# 6. STALLED PROGRESS
# ------------------------------------------------------------

df["progress_stalled"] = (
    df["progress_velocity"].abs() < 0.5
).astype("Int64")

# ------------------------------------------------------------
# 7. EXPENDITURE FEATURES
# ------------------------------------------------------------

df["expenditure_current"] = (
    df["reported_cumulative_expenditure"]
)

df["expenditure_previous"] = (
    g["reported_cumulative_expenditure"]
    .shift(1)
)

df["expenditure_velocity"] = (
    (
        df["expenditure_current"]
        - df["expenditure_previous"]
    )
    / df["month_gap"]
)

df["expenditure_3m_change"] = (
    df["expenditure_current"]
    - g["reported_cumulative_expenditure"].shift(3)
)

# ------------------------------------------------------------
# 8. COST FEATURES
# ------------------------------------------------------------

df["cost_ratio"] = np.where(
    df["reported_original_cost"] > 0,
    df["reported_cumulative_expenditure"]
    / df["reported_original_cost"],
    np.nan
)

df["revised_cost_change"] = (
    df["reported_revised_cost"]
    - df["reported_original_cost"]
)

# ------------------------------------------------------------
# 9. SCHEDULE FEATURES
# ------------------------------------------------------------

df["months_to_revised_doc"] = (
    (
        df["revised_doc_date"].dt.year
        - df["reporting_month"].dt.year
    ) * 12
    +
    (
        df["revised_doc_date"].dt.month
        - df["reporting_month"].dt.month
    )
)

df["months_from_original_doc"] = (
    (
        df["reporting_month"].dt.year
        - df["original_doc_date"].dt.year
    ) * 12
    +
    (
        df["reporting_month"].dt.month
        - df["original_doc_date"].dt.month
    )
)

# ------------------------------------------------------------
# 10. PROJECT HISTORY
# ------------------------------------------------------------

df["project_observation_count"] = (
    g.cumcount() + 1
)

first_month = (
    g["reporting_month"]
    .transform("min")
)

df["months_since_first_observation"] = (
    (
        df["reporting_month"].dt.year
        - first_month.dt.year
    ) * 12
    +
    (
        df["reporting_month"].dt.month
        - first_month.dt.month
    )
)

# Existing metadata field
if "months_since_previous_project_observation" in df.columns:

    df["months_since_previous_observation"] = (
        df["months_since_previous_project_observation"]
    )

# ------------------------------------------------------------
# 11. REVISION HISTORY
# ------------------------------------------------------------

df["schedule_revision_event"] = (
    df["material_deterioration"]
)

df["schedule_revision_count"] = (
    g["schedule_revision_event"]
    .transform(
        lambda x: x.fillna(0).cumsum()
    )
)

# ------------------------------------------------------------
# 12. CLEAN EXTREME NUMERICAL VALUES
# ------------------------------------------------------------

feature_cols = [
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",
    "progress_5m_change",
    "expenditure_velocity",
    "expenditure_3m_change",
    "cost_ratio",
    "revised_cost_change",
    "months_to_revised_doc",
    "months_from_original_doc"
]

for col in feature_cols:

    df[col] = df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print()
print("=" * 60)
print("FEATURE AVAILABILITY")
print("=" * 60)

for col in feature_cols:

    print(
        "{:<35} {:>8}".format(
            col,
            df[col].notna().sum()
        )
    )

print()
print("Total rows:", len(df))

print(
    "Total columns:",
    len(df.columns)
)

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

df.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 60)
print("STEP 11 COMPLETE")
print("=" * 60)

print("Saved:", OUTPUT)
