import pandas as pd
import numpy as np

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_labels_v2.csv"

OUTPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_ml_ready.csv"

print("=" * 70)
print("PRAHARI STEP 14 - FINAL ML FEATURE MATRIX")
print("=" * 70)

# ------------------------------------------------------------
# 1. LOAD
# ------------------------------------------------------------

df = pd.read_csv(INPUT, low_memory=False)

print("\nRows loaded:", len(df))
print("Columns loaded:", len(df.columns))

# ------------------------------------------------------------
# 2. RESTORE CONTEXT FEATURES
# ------------------------------------------------------------

# Use the cleanest available source column.
# These are current/project context fields, not future outcomes.

def first_available(df, columns):
    for col in columns:
        if col in df.columns:
            return df[col]
    return pd.Series(np.nan, index=df.index)


df["agency"] = first_available(
    df,
    ["agency", "reported_agency", "agency_raw"]
)

df["state"] = first_available(
    df,
    ["state", "reported_state", "state_raw"]
)

df["sector"] = first_available(
    df,
    ["sector", "sector_raw"]
)

df["project_name"] = first_available(
    df,
    ["project_name", "reported_project_name", "project_name_raw"]
)

# ------------------------------------------------------------
# 3. NORMALIZE TEXT
# ------------------------------------------------------------

for col in ["agency", "state", "sector", "project_name"]:

    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .replace({
            "": pd.NA,
            "-": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "None": pd.NA
        })
    )

# ------------------------------------------------------------
# 4. CURRENT PREDICTOR COLUMNS
# ------------------------------------------------------------

safe_features = [

    # Identity/context
    "agency",
    "state",
    "sector",

    # Project history
    "project_observation_count",
    "months_since_first_observation",

    # Progress trajectory
    "progress_current",
    "progress_velocity",
    "progress_acceleration",
    "progress_3m_change",
    "progress_5m_change",
    "progress_stalled",
    "stall_count_to_date",

    # Expenditure trajectory
    "expenditure_current",
    "expenditure_velocity",
    "expenditure_3m_change",

    # Cost
    "cost_ratio",
    "revised_cost_change",
    "revised_cost_ratio",

    # Schedule
    "months_to_revised_doc",
    "months_from_original_doc",

    # Data quality / observation behavior
    "progress_first_observation",
    "large_progress_jump",
    "very_large_progress_jump",
    "progress_decrease_flag",
    "expenditure_decrease_flag",
    "large_expenditure_change",
    "very_large_expenditure_change",
    "long_observation_gap",

    # Current data availability indicators
    "progress_available",
    "expenditure_available"
]

# ------------------------------------------------------------
# 5. CHECK FEATURES
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FEATURE AVAILABILITY")
print("=" * 70)

available_features = []
missing_features = []

for col in safe_features:

    if col in df.columns:
        available_features.append(col)
        print("OK   ", col)
    else:
        missing_features.append(col)
        print("MISS ", col)

# ------------------------------------------------------------
# 6. IMPORTANT LEAKAGE EXCLUSIONS
# ------------------------------------------------------------

forbidden_features = [

    # Future labels
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

    # Future observation information
    "months_to_next_project_observation",
    "next_project_observation_month",

    # Current/previous schedule revision diagnostic
    # Keep only if explicitly audited later.
    "schedule_change_months",

    # Outcome / completion information
    "actual_completion_date",

    # Provenance / identifiers
    "observation_id",
    "source_id",
    "source_sha256",
    "raw_row_locator",
    "printed_page_number",
    "source_table_number"
]

print("\n" + "=" * 70)
print("FORBIDDEN FEATURE CHECK")
print("=" * 70)

for col in forbidden_features:

    if col in df.columns:
        print("EXCLUDE:", col)

# ------------------------------------------------------------
# 7. FINAL TARGETS
# ------------------------------------------------------------

target_columns = [

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
# 8. FINAL DATASET
# ------------------------------------------------------------

metadata_columns = [
    "canonical_project_id",
    "reporting_month"
]

metadata_columns = [
    c for c in metadata_columns
    if c in df.columns
]

final_columns = (
    metadata_columns
    + available_features
    + target_columns
)

# Remove duplicates while preserving order
final_columns = list(dict.fromkeys(final_columns))

final_df = df[final_columns].copy()

# ------------------------------------------------------------
# 9. SORT
# ------------------------------------------------------------

if "reporting_month" in final_df.columns:

    final_df["reporting_month"] = pd.to_datetime(
        final_df["reporting_month"],
        errors="coerce"
    )

    final_df = final_df.sort_values(
        ["reporting_month", "canonical_project_id"]
    )

# ------------------------------------------------------------
# 10. SAVE
# ------------------------------------------------------------

final_df.to_csv(
    OUTPUT,
    index=False
)

# ------------------------------------------------------------
# 11. SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL FEATURE MATRIX SUMMARY")
print("=" * 70)

print("\nRows:", len(final_df))
print("Columns:", len(final_df.columns))

print("\nFeatures:", len(available_features))

print("\nTargets:", len(target_columns))

print("\nFinal columns:")
for col in final_df.columns:
    print("  ", col)

# ------------------------------------------------------------
# 12. CONTEXT AVAILABILITY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("CONTEXT FEATURE COVERAGE")
print("=" * 70)

for col in ["agency", "state", "sector", "project_name"]:

    if col in final_df.columns:

        present = final_df[col].notna().sum()

        print(
            f"{col}: "
            f"{present}/{len(final_df)} "
            f"({present / len(final_df) * 100:.2f}%)"
        )

# ------------------------------------------------------------
# 13. TARGET COVERAGE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TARGET COVERAGE")
print("=" * 70)

for col in target_columns:

    known = final_df[col].notna().sum()
    positive = (final_df[col] == 1).sum()

    print(
        f"{col}: "
        f"known={known}, "
        f"positive={positive}"
    )

print("\n" + "=" * 70)
print("STEP 14 COMPLETE")
print("=" * 70)

print("\nSaved:")
print(OUTPUT)
