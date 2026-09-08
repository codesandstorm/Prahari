import pandas as pd

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_ml_ready.csv"

print("=" * 70)
print("PRAHARI STEP 15 - FINAL LEAKAGE GATE")
print("=" * 70)

df = pd.read_csv(INPUT, low_memory=False)

print("\nRows:", len(df))
print("Columns:", len(df.columns))

# ------------------------------------------------------------
# 1. DEFINE FEATURES
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# 2. DEFINE TARGETS
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# 3. CHECK FEATURES EXIST
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FEATURE EXISTENCE CHECK")
print("=" * 70)

missing_features = []

for col in features:

    if col in df.columns:
        print("OK   ", col)
    else:
        print("MISS ", col)
        missing_features.append(col)

# ------------------------------------------------------------
# 4. CHECK TARGETS EXIST
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TARGET EXISTENCE CHECK")
print("=" * 70)

missing_targets = []

for col in targets:

    if col in df.columns:
        print("OK   ", col)
    else:
        print("MISS ", col)
        missing_targets.append(col)

# ------------------------------------------------------------
# 5. CHECK SUSPICIOUS COLUMNS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SUSPICIOUS COLUMN CHECK")
print("=" * 70)

suspicious_keywords = [
    "event",
    "risk_by",
    "t_plus",
    "future",
    "completion",
    "actual_",
    "label",
    "target",
    "next_project",
    "months_to_next",
    "source_",
    "observation_id",
    "raw_row"
]

suspicious = []

for col in df.columns:

    col_lower = col.lower()

    if any(
        keyword in col_lower
        for keyword in suspicious_keywords
    ):

        if col not in targets:
            suspicious.append(col)

            print(
                "REVIEW:",
                col
            )

# ------------------------------------------------------------
# 6. EXPLICIT FORBIDDEN FEATURES
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FORBIDDEN FEATURE CHECK")
print("=" * 70)

forbidden = [
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

    "months_to_next_project_observation",
    "next_project_observation_month",

    "actual_completion_date",

    "observation_id",
    "source_id",
    "source_sha256",
    "raw_row_locator",
    "printed_page_number",
    "source_table_number"
]

leakage_found = []

for col in forbidden:

    if col in features:

        leakage_found.append(col)

        print(
            "LEAKAGE:",
            col
        )

if not leakage_found:
    print("PASS - no forbidden feature is in predictor list")

# ------------------------------------------------------------
# 7. CHECK ID / DATE SEPARATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("IDENTIFIER / DATE CHECK")
print("=" * 70)

if "canonical_project_id" in features:
    print("WARNING: project ID is being used as a predictor")
else:
    print("PASS - canonical_project_id excluded")

if "reporting_month" in features:
    print("WARNING: reporting_month is being used directly")
else:
    print("PASS - reporting_month excluded as direct predictor")

# ------------------------------------------------------------
# 8. FEATURE/TARGET OVERLAP
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FEATURE / TARGET OVERLAP")
print("=" * 70)

overlap = set(features).intersection(set(targets))

if overlap:

    print("FAIL - overlap detected:")
    for col in overlap:
        print("  ", col)

else:

    print("PASS - no feature/target overlap")

# ------------------------------------------------------------
# 9. FINAL MATRIX CHECK
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL MATRIX CHECK")
print("=" * 70)

print(
    "Expected predictors:",
    len(features)
)

print(
    "Expected targets:",
    len(targets)
)

print(
    "Actual dataset columns:",
    len(df.columns)
)

# ------------------------------------------------------------
# 10. FINAL DECISION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL LEAKAGE DECISION")
print("=" * 70)

if (
    missing_features
    or missing_targets
    or leakage_found
    or overlap
):

    print("\n❌ LEAKAGE GATE FAILED")

    if missing_features:
        print(
            "Missing features:",
            missing_features
        )

    if missing_targets:
        print(
            "Missing targets:",
            missing_targets
        )

    if leakage_found:
        print(
            "Forbidden features:",
            leakage_found
        )

    if overlap:
        print(
            "Feature/target overlap:",
            overlap
        )

else:

    print("\n✅ LEAKAGE GATE PASSED")

    print(
        "\nThe selected predictor set contains no "
        "explicit future labels or forbidden outcome fields."
    )

print("\n" + "=" * 70)
print("STEP 15 COMPLETE")
print("=" * 70)
