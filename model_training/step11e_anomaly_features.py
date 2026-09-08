import pandas as pd
import numpy as np

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed/"

INPUT = BASE + "project_month_features_v3.csv"
OUTPUT = BASE + "project_month_features_v4.csv"

print("=" * 60)
print("PRAHARI STEP 11E - ANOMALY FLAGS")
print("=" * 60)

df = pd.read_csv(INPUT, low_memory=False)

print("Rows loaded:", len(df))

# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_cols = [
    "reported_physical_progress",
    "progress_previous",
    "progress_change",
    "progress_velocity",
    "reported_cumulative_expenditure",
    "expenditure_previous",
    "expenditure_change",
    "expenditure_velocity",
    "actual_month_gap"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# ============================================================
# 1. FIRST OBSERVED PROGRESS
# ============================================================

df["progress_first_observation"] = np.where(
    df["reported_physical_progress"].notna()
    & df["progress_previous"].isna(),
    1,
    0
)

# ============================================================
# 2. LARGE PROGRESS JUMP
# ============================================================

df["large_progress_jump"] = np.where(
    df["progress_change"].notna()
    & (df["progress_change"].abs() >= 20),
    1,
    0
)

# ============================================================
# 3. VERY LARGE PROGRESS JUMP
# ============================================================

df["very_large_progress_jump"] = np.where(
    df["progress_change"].notna()
    & (df["progress_change"].abs() >= 50),
    1,
    0
)

# ============================================================
# 4. PROGRESS DECREASE
# ============================================================

df["progress_decrease_flag"] = np.where(
    df["progress_change"].notna()
    & (df["progress_change"] < 0),
    1,
    0
)

# ============================================================
# 5. EXPENDITURE DECREASE
# ============================================================

df["expenditure_decrease_flag"] = np.where(
    df["expenditure_change"].notna()
    & (df["expenditure_change"] < 0),
    1,
    0
)

# ============================================================
# 6. LARGE EXPENDITURE CHANGE
# ============================================================

df["large_expenditure_change"] = np.where(
    df["expenditure_change"].notna()
    & (
        df["expenditure_change"].abs()
        > 1000
    ),
    1,
    0
)

# ============================================================
# 7. VERY LARGE EXPENDITURE CHANGE
# ============================================================

df["very_large_expenditure_change"] = np.where(
    df["expenditure_change"].notna()
    & (
        df["expenditure_change"].abs()
        > 10000
    ),
    1,
    0
)

# ============================================================
# 8. POSSIBLE LATE ENTRY
# ============================================================
#
# A project that first becomes observable with very high
# physical progress may not have a true 0 -> 100 trajectory.
#

df["possible_late_entry"] = np.where(
    (
        df["progress_first_observation"] == 1
    )
    & (
        df["reported_physical_progress"] >= 80
    ),
    1,
    0
)

# ============================================================
# 9. LONG OBSERVATION GAP
# ============================================================

df["long_observation_gap"] = np.where(
    df["actual_month_gap"].notna()
    & (df["actual_month_gap"] >= 3),
    1,
    0
)

# ============================================================
# 10. PROGRESS DATA AVAILABLE
# ============================================================

df["progress_available"] = np.where(
    df["reported_physical_progress"].notna(),
    1,
    0
)

# ============================================================
# 11. EXPENDITURE DATA AVAILABLE
# ============================================================

df["expenditure_available"] = np.where(
    df["reported_cumulative_expenditure"].notna(),
    1,
    0
)

# ============================================================
# 12. DATA QUALITY SUMMARY SCORE
# ============================================================
#
# This is NOT a "bad row" score.
# It simply counts unusual reporting conditions.
#

flag_cols = [
    "large_progress_jump",
    "very_large_progress_jump",
    "progress_decrease_flag",
    "expenditure_decrease_flag",
    "large_expenditure_change",
    "very_large_expenditure_change",
    "possible_late_entry",
    "long_observation_gap"
]

df["data_quality_flag_count"] = (
    df[flag_cols].sum(axis=1)
)

# ============================================================
# AUDIT
# ============================================================

print()
print("=" * 60)
print("ANOMALY FLAG COUNTS")
print("=" * 60)

for col in flag_cols:
    print(
        "{:<35} {:>8}".format(
            col,
            int(df[col].sum())
        )
    )

print()
print("=" * 60)
print("DATA AVAILABILITY")
print("=" * 60)

print(
    "Progress available:",
    int(df["progress_available"].sum())
)

print(
    "Expenditure available:",
    int(df["expenditure_available"].sum())
)

print()
print("=" * 60)
print("QUALITY FLAG DISTRIBUTION")
print("=" * 60)

print(
    df["data_quality_flag_count"]
    .value_counts()
    .sort_index()
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
print("STEP 11E COMPLETE")
print("=" * 60)

print("Saved:", OUTPUT)
print("Rows:", len(df))
print("Columns:", len(df.columns))
