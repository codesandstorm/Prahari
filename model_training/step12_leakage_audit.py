import pandas as pd

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed/"

INPUT = BASE + "project_month_features_v4.csv"

print("=" * 70)
print("PRAHARI STEP 12 - FEATURE LEAKAGE AUDIT")
print("=" * 70)

df = pd.read_csv(INPUT, low_memory=False)

print("Rows:", len(df))
print("Columns:", len(df.columns))

# ============================================================
# DEFINITELY FORBIDDEN FEATURES
# ============================================================

forbidden = [
    "actual_completion_date",
    "reported_cumulative_expenditure",
    "reported_physical_progress",
    "reported_revised_doc",
]

# NOTE:
# These raw fields are not necessarily forbidden from historical
# feature engineering. They are listed here for review because
# their CURRENT ROW value may contain information that must be
# interpreted carefully depending on the anchor time.

# ============================================================
# LABEL / OUTCOME COLUMNS
# ============================================================

label_columns = [
    "material_deterioration",
    "event_t_plus_1",
    "event_t_plus_2",
    "event_t_plus_3",
    "event_t_plus_4",
    "event_t_plus_5",
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5",
]

print()
print("=" * 70)
print("LABEL COLUMNS PRESENT")
print("=" * 70)

for col in label_columns:
    if col in df.columns:
        print("FOUND:", col)

# ============================================================
# POTENTIALLY DANGEROUS COLUMNS
# ============================================================

danger_keywords = [
    "future",
    "completion",
    "event",
    "label",
    "risk_by",
    "t_plus",
    "target",
]

print()
print("=" * 70)
print("POTENTIALLY DANGEROUS COLUMNS")
print("=" * 70)

for col in df.columns:

    lower = col.lower()

    if any(
        keyword in lower
        for keyword in danger_keywords
    ):
        print(col)

# ============================================================
# CURRENT FEATURE INVENTORY
# ============================================================

print()
print("=" * 70)
print("TRAJECTORY FEATURES")
print("=" * 70)

trajectory_keywords = [
    "velocity",
    "acceleration",
    "change",
    "ratio",
    "stall",
    "observation",
    "gap",
    "progress",
    "expenditure"
]

for col in df.columns:

    lower = col.lower()

    if any(
        keyword in lower
        for keyword in trajectory_keywords
    ):
        print(col)

# ============================================================
# CHECK COMPLETION DATE
# ============================================================

print()
print("=" * 70)
print("COMPLETION DATE CHECK")
print("=" * 70)

if "actual_completion_date" in df.columns:

    print(
        "actual_completion_date present:",
        True
    )

    print(
        "Non-null:",
        df["actual_completion_date"].notna().sum()
    )

    print(
        "IMPORTANT: This must NOT be used as a predictor."
    )

else:

    print(
        "actual_completion_date not present."
    )

# ============================================================
# CHECK FOR OBVIOUS LABEL LEAKAGE
# ============================================================

print()
print("=" * 70)
print("OBVIOUS LEAKAGE CHECK")
print("=" * 70)

leakage_terms = [
    "actual_completion",
    "future",
    "event_t_plus",
    "risk_by_t_plus"
]

for col in df.columns:

    lower = col.lower()

    if any(
        term in lower
        for term in leakage_terms
    ):
        print(
            "REVIEW:",
            col
        )

# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("RECOMMENDED SAFE FEATURE GROUPS")
print("=" * 70)

safe_groups = {
    "Identity/context": [
        "agency",
        "state",
        "sector",
        "project_name"
    ],

    "Project history": [
        "project_observation_count",
        "months_since_first_observation"
    ],

    "Progress trajectory": [
        "progress_current",
        "progress_velocity",
        "progress_acceleration",
        "progress_3m_change",
        "progress_5m_change",
        "progress_stalled",
        "stall_count_to_date"
    ],

    "Expenditure trajectory": [
        "expenditure_current",
        "expenditure_velocity",
        "expenditure_3m_change"
    ],

    "Cost": [
        "cost_ratio",
        "revised_cost_change",
        "revised_cost_ratio"
    ],

    "Schedule": [
        "months_to_revised_doc",
        "months_from_original_doc"
    ],

    "Data quality / observability": [
        "progress_first_observation",
        "large_progress_jump",
        "very_large_progress_jump",
        "progress_decrease_flag",
        "expenditure_decrease_flag",
        "large_expenditure_change",
        "very_large_expenditure_change",
        "possible_late_entry",
        "long_observation_gap"
    ]
}

for group, columns in safe_groups.items():

    print()
    print(group)

    for col in columns:

        if col in df.columns:
            print("  OK   ", col)
        else:
            print("  MISS ", col)

print()
print("=" * 70)
print("STEP 12 AUDIT COMPLETE")
print("=" * 70)
