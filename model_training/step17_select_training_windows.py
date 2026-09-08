import pandas as pd
import numpy as np

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_ml_ready.csv"

print("=" * 70)
print("PRAHARI STEP 17 - TRAINING WINDOW SELECTION")
print("=" * 70)

df = pd.read_csv(INPUT, low_memory=False)

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

# ------------------------------------------------------------
# TARGETS
# ------------------------------------------------------------

targets = [
    "risk_by_t_plus_1",
    "risk_by_t_plus_2",
    "risk_by_t_plus_3",
    "risk_by_t_plus_4",
    "risk_by_t_plus_5"
]

# ------------------------------------------------------------
# 1. SUPERVISED PERIOD
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("1. SUPERVISED DATA PERIOD")
print("=" * 70)

for target in targets:

    known = df[df[target].notna()]["reporting_month"]

    print(
        f"{target}: "
        f"{known.min().strftime('%Y-%m')} "
        f"to "
        f"{known.max().strftime('%Y-%m')} "
        f"| n={len(known)}"
    )

# ------------------------------------------------------------
# 2. MONTHLY LABEL AVAILABILITY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("2. MONTHLY LABEL AVAILABILITY")
print("=" * 70)

monthly = (
    df.assign(
        month=df["reporting_month"].dt.to_period("M")
    )
    .groupby("month")
    .agg(
        t1=("risk_by_t_plus_1", "count"),
        t2=("risk_by_t_plus_2", "count"),
        t3=("risk_by_t_plus_3", "count"),
        t4=("risk_by_t_plus_4", "count"),
        t5=("risk_by_t_plus_5", "count")
    )
)

print(monthly.to_string())

# ------------------------------------------------------------
# 3. CANDIDATE WINDOWS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("3. CANDIDATE TEMPORAL SPLITS")
print("=" * 70)

candidates = [

    # Short supervised history
    ("2025-07", "2025-10", "2025-11", "2025-12", "2026-01"),

    # Slightly larger training period
    ("2025-07", "2025-11", "2025-12", "2026-01", "2026-02"),

    # Larger training period
    ("2025-07", "2025-12", "2026-01", "2026-02", "2026-03"),

    # Rolling evaluation
    ("2025-07", "2025-10", "2025-11", "2025-12", "2026-01"),

    # Conservative test
    ("2025-07", "2025-11", "2025-12", "2025-12", "2026-01")
]

# ------------------------------------------------------------
# 4. EVALUATE CANDIDATES
# ------------------------------------------------------------

for i, candidate in enumerate(candidates, start=1):

    train_start = pd.Timestamp(candidate[0] + "-01")
    train_end = pd.Timestamp(candidate[1] + "-01")

    val_start = pd.Timestamp(candidate[2] + "-01")
    val_end = pd.Timestamp(candidate[3] + "-01")

    test_start = pd.Timestamp(candidate[4] + "-01")

    # Test through final available month
    test_end = df["reporting_month"].max()

    train = df[
        (df["reporting_month"] >= train_start)
        &
        (df["reporting_month"] <= train_end)
    ]

    validation = df[
        (df["reporting_month"] >= val_start)
        &
        (df["reporting_month"] <= val_end)
    ]

    test = df[
        (df["reporting_month"] >= test_start)
        &
        (df["reporting_month"] <= test_end)
    ]

    print("\n" + "-" * 70)
    print(f"CANDIDATE {i}")

    print(
        f"TRAIN      : {candidate[0]} → {candidate[1]}"
    )

    print(
        f"VALIDATION : {candidate[2]} → {candidate[3]}"
    )

    print(
        f"TEST       : {candidate[4]} → "
        f"{test_end.strftime('%Y-%m')}"
    )

    print(
        "Rows:",
        len(train),
        len(validation),
        len(test)
    )

    for split_name, subset in [
        ("TRAIN", train),
        ("VALIDATION", validation),
        ("TEST", test)
    ]:

        print(f"\n{split_name}")

        for target in targets:

            known = subset[target].dropna()

            if len(known) == 0:

                print(
                    f"{target}: "
                    f"known=0"
                )

                continue

            positive = (known == 1).sum()
            negative = (known == 0).sum()

            print(
                f"{target}: "
                f"known={len(known)}, "
                f"positive={positive}, "
                f"negative={negative}, "
                f"rate={positive / len(known) * 100:.2f}%"
            )

# ------------------------------------------------------------
# 5. FEATURE AVAILABILITY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("5. FEATURE AVAILABILITY IN SUPERVISED PERIOD")
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

supervised = df[
    df["risk_by_t_plus_1"].notna()
].copy()

print(
    "Rows with T+1 labels:",
    len(supervised)
)

for feature in features:

    missing = supervised[feature].isna().mean() * 100

    available = 100 - missing

    print(
        f"{feature}: "
        f"available={available:.2f}%"
    )

# ------------------------------------------------------------
# 6. PROJECT COUNTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("6. PROJECT COUNTS")
print("=" * 70)

for period_name, start, end in [
    ("2025 supervised", "2025-07", "2025-12"),
    ("2026 test", "2026-01", "2026-06")
]:

    start_date = pd.Timestamp(start + "-01")
    end_date = pd.Timestamp(end + "-01")

    subset = df[
        (df["reporting_month"] >= start_date)
        &
        (df["reporting_month"] <= end_date)
    ]

    print(
        period_name,
        ":",
        subset["canonical_project_id"].nunique(),
        "projects"
    )

# ------------------------------------------------------------
# 7. FINAL WARNING
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("7. RESEARCH RULES")
print("=" * 70)

print(
    "1. Unknown labels remain NaN."
)

print(
    "2. No random train/test split."
)

print(
    "3. Training must contain actual positive AND negative labels."
)

print(
    "4. Each horizon is evaluated only where that horizon is observable."
)

print(
    "5. T+5 should not be claimed as robust if test observations are insufficient."
)

print(
    "6. Temporal distribution shift must be reported."
)

print("\n" + "=" * 70)
print("STEP 17 COMPLETE")
print("=" * 70)
