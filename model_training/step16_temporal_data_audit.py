import pandas as pd
import numpy as np

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_ml_ready.csv"

print("=" * 70)
print("PRAHARI STEP 16 - TEMPORAL DATA AUDIT")
print("=" * 70)

# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT, low_memory=False)

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

print("\nRows:", len(df))
print("Columns:", len(df.columns))

# ============================================================
# 1. BASIC DATE CHECK
# ============================================================

print("\n" + "=" * 70)
print("1. DATE RANGE")
print("=" * 70)

print("Earliest month:", df["reporting_month"].min())
print("Latest month  :", df["reporting_month"].max())

print(
    "Missing reporting months:",
    df["reporting_month"].isna().sum()
)

# ============================================================
# 2. DUPLICATE PROJECT-MONTH CHECK
# ============================================================

print("\n" + "=" * 70)
print("2. DUPLICATE PROJECT-MONTH CHECK")
print("=" * 70)

duplicates = df.duplicated(
    subset=["canonical_project_id", "reporting_month"],
    keep=False
)

duplicate_rows = duplicates.sum()

print("Duplicate project-month rows:", duplicate_rows)

if duplicate_rows == 0:
    print("PASS - no duplicate project-month rows")
else:
    print("WARNING - duplicate project-month rows detected")

# ============================================================
# 3. PROJECT CHRONOLOGY
# ============================================================

print("\n" + "=" * 70)
print("3. PROJECT CHRONOLOGY CHECK")
print("=" * 70)

df_sorted = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).copy()

previous_month = (
    df_sorted
    .groupby("canonical_project_id")["reporting_month"]
    .shift(1)
)

month_gap = (
    (df_sorted["reporting_month"].dt.year -
     previous_month.dt.year) * 12
    +
    (df_sorted["reporting_month"].dt.month -
     previous_month.dt.month)
)

negative_gaps = (month_gap < 0).sum()

zero_gaps = (month_gap == 0).sum()

print("Negative chronological gaps:", negative_gaps)
print("Zero-month gaps:", zero_gaps)

if negative_gaps == 0:
    print("PASS - project observations are chronological")
else:
    print("FAIL - chronological problem detected")

# ============================================================
# 4. TEMPORAL DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("4. ROWS BY REPORTING MONTH")
print("=" * 70)

monthly_counts = (
    df.groupby(df["reporting_month"].dt.to_period("M"))
      .size()
)

print(monthly_counts.to_string())

# ============================================================
# 5. PROPOSE TEMPORAL SPLIT
# ============================================================

print("\n" + "=" * 70)
print("5. TEMPORAL SPLIT CANDIDATE")
print("=" * 70)

# Candidate split:
# TRAIN      : through 2024-12
# VALIDATION : 2025-01 through 2025-12
# TEST       : 2026-01 through 2026-06

train_end = pd.Timestamp("2024-12-01")
validation_end = pd.Timestamp("2025-12-01")

train_mask = df["reporting_month"] <= train_end

validation_mask = (
    (df["reporting_month"] > train_end)
    &
    (df["reporting_month"] <= validation_end)
)

test_mask = df["reporting_month"] > validation_end

print(
    "TRAIN:",
    df.loc[train_mask, "reporting_month"].min(),
    "to",
    df.loc[train_mask, "reporting_month"].max()
)

print(
    "VALIDATION:",
    df.loc[validation_mask, "reporting_month"].min(),
    "to",
    df.loc[validation_mask, "reporting_month"].max()
)

print(
    "TEST:",
    df.loc[test_mask, "reporting_month"].min(),
    "to",
    df.loc[test_mask, "reporting_month"].max()
)

print("\nRows:")
print("TRAIN      :", train_mask.sum())
print("VALIDATION :", validation_mask.sum())
print("TEST       :", test_mask.sum())

# ============================================================
# 6. PROJECT OVERLAP CHECK
# ============================================================

print("\n" + "=" * 70)
print("6. PROJECT OVERLAP CHECK")
print("=" * 70)

train_projects = set(
    df.loc[train_mask, "canonical_project_id"].dropna()
)

validation_projects = set(
    df.loc[validation_mask, "canonical_project_id"].dropna()
)

test_projects = set(
    df.loc[test_mask, "canonical_project_id"].dropna()
)

train_val_overlap = train_projects & validation_projects
train_test_overlap = train_projects & test_projects
val_test_overlap = validation_projects & test_projects

print(
    "TRAIN projects:",
    len(train_projects)
)

print(
    "VALIDATION projects:",
    len(validation_projects)
)

print(
    "TEST projects:",
    len(test_projects)
)

print(
    "\nTRAIN ∩ VALIDATION:",
    len(train_val_overlap)
)

print(
    "TRAIN ∩ TEST:",
    len(train_test_overlap)
)

print(
    "VALIDATION ∩ TEST:",
    len(val_test_overlap)
)

print(
    "\nNOTE:"
)

print(
    "Project overlap across time is EXPECTED for a "
    "project-month forecasting problem."
)

# ============================================================
# 7. TARGET COVERAGE BY SPLIT
# ============================================================

print("\n" + "=" * 70)
print("7. TARGET COVERAGE BY SPLIT")
print("=" * 70)

targets = [
    "event_t_plus_1",
    "event_t_plus_2",
    "event_t_plus_3",
    "event_t_plus_4",
    "event_t_plus_5",

    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

split_info = {
    "TRAIN": train_mask,
    "VALIDATION": validation_mask,
    "TEST": test_mask
}

for split_name, mask in split_info.items():

    print("\n" + split_name)

    subset = df.loc[mask]

    for target in targets:

        known = subset[target].notna().sum()
        positive = (
            subset[target]
            .eq(1)
            .sum()
        )

        if known > 0:
            rate = positive / known * 100
        else:
            rate = np.nan

        print(
            f"{target}: "
            f"known={known}, "
            f"positive={positive}, "
            f"rate={rate:.2f}%"
        )

# ============================================================
# 8. CLASS BALANCE
# ============================================================

print("\n" + "=" * 70)
print("8. CLASS BALANCE")
print("=" * 70)

for target in targets:

    known_mask = df[target].notna()

    known_values = df.loc[
        known_mask,
        target
    ]

    if len(known_values) == 0:
        continue

    positives = (known_values == 1).sum()
    negatives = (known_values == 0).sum()

    print(
        f"\n{target}"
    )

    print(
        "  Positive:",
        positives
    )

    print(
        "  Negative:",
        negatives
    )

    print(
        "  Positive rate:",
        f"{positives / len(known_values) * 100:.2f}%"
    )

# ============================================================
# 9. FEATURE MISSINGNESS BY SPLIT
# ============================================================

print("\n" + "=" * 70)
print("9. FEATURE MISSINGNESS")
print("=" * 70)

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

for split_name, mask in split_info.items():

    subset = df.loc[mask]

    print("\n" + split_name)

    for feature in features:

        if feature not in subset.columns:
            continue

        missing_pct = (
            subset[feature].isna().mean() * 100
        )

        print(
            f"{feature}: "
            f"{missing_pct:.2f}% missing"
        )

# ============================================================
# 10. TARGET AVAILABILITY BY MONTH
# ============================================================

print("\n" + "=" * 70)
print("10. TARGET AVAILABILITY BY MONTH")
print("=" * 70)

for target in [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]:

    print("\n", target)

    monthly = (
        df.assign(
            month=df["reporting_month"].dt.to_period("M")
        )
        .groupby("month")[target]
        .agg(
            known="count",
            positive=lambda x: (x == 1).sum()
        )
    )

    monthly["positive_rate"] = (
        monthly["positive"]
        / monthly["known"]
        * 100
    )

    print(
        monthly.to_string()
    )

# ============================================================
# 11. CENSORING CHECK
# ============================================================

print("\n" + "=" * 70)
print("11. CENSORING CHECK")
print("=" * 70)

for horizon in range(1, 6):

    target = f"risk_by_t_plus_{horizon}"

    unknown = df[target].isna().sum()

    known = df[target].notna().sum()

    print(
        f"{target}: "
        f"known={known}, "
        f"censored/unknown={unknown}"
    )

print(
    "\nIMPORTANT:"
)

print(
    "Unknown future outcomes are NOT treated as negative cases."
)

# ============================================================
# 12. FINAL DECISION
# ============================================================

print("\n" + "=" * 70)
print("STEP 16 FINAL AUDIT")
print("=" * 70)

problems = []

if df["reporting_month"].isna().sum() > 0:
    problems.append("missing reporting_month")

if negative_gaps > 0:
    problems.append("negative chronological gaps")

if duplicate_rows > 0:
    problems.append("duplicate project-month rows")

for target in targets:

    if target not in df.columns:
        problems.append(
            f"missing target: {target}"
        )

if problems:

    print("\n❌ TEMPORAL AUDIT REQUIRES REVIEW")

    print("\nProblems:")

    for problem in problems:
        print("-", problem)

else:

    print(
        "\n✅ BASIC TEMPORAL AUDIT PASSED"
    )

    print(
        "\nCandidate split:"
    )

    print(
        "TRAIN      : 2023-07 to 2024-12"
    )

    print(
        "VALIDATION : 2025-01 to 2025-12"
    )

    print(
        "TEST       : 2026-01 to 2026-06"
    )

    print(
        "\nProject overlap across time is retained "
        "because the task is longitudinal forecasting."
    )

print("\n" + "=" * 70)
print("STEP 16 COMPLETE")
print("=" * 70)
