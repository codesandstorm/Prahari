import pandas as pd
import numpy as np

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed/"

INPUT = BASE + "project_month_labels.csv"
OUTPUT = BASE + "project_month_features_v3.csv"

print("=" * 60)
print("PRAHARI STEP 11C - CORRECT FEATURE ENGINEERING")
print("=" * 60)

df = pd.read_csv(INPUT, low_memory=False)

print("Rows loaded:", len(df))

# ============================================================
# DATE PARSING
# ============================================================

# Reporting month is actually YYYY-MM-DD
df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

# DOC fields are MM/YYYY, with "-" for unavailable
df["revised_doc_date"] = pd.to_datetime(
    df["reported_revised_doc"]
        .astype(str)
        .str.strip()
        .replace("-", pd.NA),
    format="%m/%Y",
    errors="coerce"
)

df["original_doc_date"] = pd.to_datetime(
    df["reported_original_target_doc"]
        .astype(str)
        .str.strip()
        .replace("-", pd.NA),
    format="%m/%Y",
    errors="coerce"
)

# ============================================================
# NUMERIC CONVERSION
# ============================================================

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

# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).copy()

g = df.groupby(
    "canonical_project_id",
    sort=False
)

# ============================================================
# ACTUAL CALENDAR MONTH GAP
# ============================================================

previous_month = g["reporting_month"].shift(1)

df["actual_month_gap"] = (
    (
        df["reporting_month"].dt.year
        - previous_month.dt.year
    ) * 12
    +
    (
        df["reporting_month"].dt.month
        - previous_month.dt.month
    )
)

# ============================================================
# PROGRESS FEATURES
# ============================================================

df["progress_current"] = (
    df["reported_physical_progress"]
)

df["progress_previous"] = (
    g["reported_physical_progress"].shift(1)
)

df["progress_change"] = (
    df["progress_current"]
    - df["progress_previous"]
)

df["progress_velocity"] = np.where(
    (
        df["actual_month_gap"] > 0
    )
    & df["progress_current"].notna()
    & df["progress_previous"].notna(),
    df["progress_change"]
    / df["actual_month_gap"],
    np.nan
)

# Previous velocity
df["previous_progress_velocity"] = (
    g["progress_velocity"].shift(1)
)

# Acceleration / deceleration
df["progress_acceleration"] = (
    df["progress_velocity"]
    - df["previous_progress_velocity"]
)

# ============================================================
# LONGER-TERM PROGRESS TREND
# ============================================================

df["progress_3m_change"] = (
    df["progress_current"]
    - g["reported_physical_progress"].shift(3)
)

df["progress_5m_change"] = (
    df["progress_current"]
    - g["reported_physical_progress"].shift(5)
)

# ============================================================
# PROGRESS STALL
# ============================================================

df["progress_stalled"] = np.where(
    df["progress_velocity"].notna(),
    (
        df["progress_velocity"].abs() < 0.5
    ).astype(int),
    np.nan
)

# ============================================================
# EXPENDITURE FEATURES
# ============================================================

df["expenditure_current"] = (
    df["reported_cumulative_expenditure"]
)

df["expenditure_previous"] = (
    g["reported_cumulative_expenditure"].shift(1)
)

df["expenditure_change"] = (
    df["expenditure_current"]
    - df["expenditure_previous"]
)

df["expenditure_velocity"] = np.where(
    (
        df["actual_month_gap"] > 0
    )
    & df["expenditure_current"].notna()
    & df["expenditure_previous"].notna(),
    df["expenditure_change"]
    / df["actual_month_gap"],
    np.nan
)

df["expenditure_3m_change"] = (
    df["expenditure_current"]
    - g["reported_cumulative_expenditure"].shift(3)
)

# ============================================================
# COST FEATURES
# ============================================================

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

df["revised_cost_ratio"] = np.where(
    df["reported_original_cost"] > 0,
    df["reported_revised_cost"]
    / df["reported_original_cost"],
    np.nan
)

# ============================================================
# SCHEDULE FEATURES
# ============================================================

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

# ============================================================
# PROJECT HISTORY
# ============================================================

df["project_observation_count"] = (
    g.cumcount() + 1
)

first_month = g["reporting_month"].transform("min")

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

# ============================================================
# STALL HISTORY
# ============================================================

df["stall_event"] = df["progress_stalled"]

df["stall_count_to_date"] = (
    df.groupby("canonical_project_id")
      ["stall_event"]
      .transform(
          lambda x: x.fillna(0).cumsum()
      )
)

# ============================================================
# CLEAN INF
# ============================================================

feature_cols = [
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",
    "progress_5m_change",
    "expenditure_velocity",
    "expenditure_3m_change",
    "cost_ratio",
    "revised_cost_change",
    "revised_cost_ratio",
    "months_to_revised_doc",
    "months_from_original_doc"
]

for col in feature_cols:
    df[col] = df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )

# ============================================================
# AUDIT
# ============================================================

print()
print("=" * 60)
print("DATE AUDIT")
print("=" * 60)

print(
    "Reporting month valid:",
    df["reporting_month"].notna().sum()
)

print(
    "Original DOC valid:",
    df["original_doc_date"].notna().sum()
)

print(
    "Revised DOC valid:",
    df["revised_doc_date"].notna().sum()
)

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
print("=" * 60)
print("VELOCITY STATISTICS")
print("=" * 60)

print(
    df["progress_velocity"].describe()
)

print()
print(
    df["expenditure_velocity"].describe()
)

# ============================================================
# SHOW REAL TRAJECTORY
# ============================================================

print()
print("=" * 60)
print("EXAMPLE PROJECT TRAJECTORY")
print("=" * 60)

project_counts = (
    df.groupby("canonical_project_id")
      .size()
      .sort_values(ascending=False)
)

project_id = project_counts.index[0]

sample = df[
    df["canonical_project_id"] == project_id
][
    [
        "canonical_project_id",
        "reporting_month",
        "actual_month_gap",
        "reported_physical_progress",
        "progress_change",
        "progress_velocity",
        "reported_cumulative_expenditure",
        "expenditure_change",
        "expenditure_velocity",
        "reported_original_target_doc",
        "reported_revised_doc",
        "months_to_revised_doc"
    ]
].head(15)

print(
    sample.to_string(index=False)
)

# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT,
    index=False
)

print()
print("=" * 60)
print("STEP 11C COMPLETE")
print("=" * 60)

print("Saved:", OUTPUT)
print("Rows:", len(df))
print("Columns:", len(df.columns))
