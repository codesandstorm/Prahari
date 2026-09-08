import pandas as pd
import numpy as np

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_features_v4.csv"

OUTPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_labels_v2.csv"

print("=" * 70)
print("PRAHARI STEP 13 - ANCHOR-BASED FUTURE RISK LABELS")
print("=" * 70)

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT, low_memory=False)

print(f"\nRows loaded: {len(df)}")

# ------------------------------------------------------------
# 2. PARSE DATES
# ------------------------------------------------------------

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

df["revised_doc_date"] = pd.to_datetime(
    df["revised_doc_date"],
    errors="coerce"
)

df = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).reset_index(drop=True)

# ------------------------------------------------------------
# 3. REMOVE OLD LABELS
# ------------------------------------------------------------

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

for col in label_columns:
    if col in df.columns:
        df.drop(columns=col, inplace=True)

# ------------------------------------------------------------
# 4. CREATE ANCHOR BASELINE
# ------------------------------------------------------------
#
# At anchor month T:
#
# baseline_revised_doc =
#     latest revised DOC known as of T
#
# We use forward fill within each project.
#
# IMPORTANT:
# This is information available at T.
# ------------------------------------------------------------

df["anchor_baseline_revised_doc"] = (
    df.groupby("canonical_project_id")["revised_doc_date"]
      .ffill()
)

# ------------------------------------------------------------
# 5. CREATE FUTURE LABELS
# ------------------------------------------------------------

for h in range(1, 6):

    event_col = f"event_t_plus_{h}"
    risk_col = f"risk_by_t_plus_{h}"

    events = []
    risks = []

    for project_id, group in df.groupby(
        "canonical_project_id",
        sort=False
    ):

        group = group.sort_values("reporting_month")

        dates = group["reporting_month"].tolist()
        revised_docs = group["revised_doc_date"].tolist()

        for i in range(len(group)):

            anchor_date = dates[i]
            baseline = group.iloc[i]["anchor_baseline_revised_doc"]

            # ------------------------------------------------
            # No baseline known at T
            # ------------------------------------------------

            if pd.isna(baseline):

                events.append(np.nan)
                risks.append(np.nan)
                continue

            # ------------------------------------------------
            # Target future calendar month
            # ------------------------------------------------

            target_month = (
                anchor_date
                + pd.DateOffset(months=h)
            )

            # ------------------------------------------------
            # Find exact future observation
            # ------------------------------------------------

            future_idx = None

            for j in range(i + 1, len(group)):

                if dates[j] == target_month:

                    future_idx = j
                    break

                if dates[j] > target_month:
                    break

            # ------------------------------------------------
            # Future month unavailable
            # ------------------------------------------------

            if future_idx is None:

                events.append(np.nan)
                risks.append(np.nan)
                continue

            # ------------------------------------------------
            # Check future observations from T+1 to T+h
            # ------------------------------------------------

            first_event = False
            cumulative_event = False

            for k in range(i + 1, future_idx + 1):

                future_doc = revised_docs[k]

                if pd.isna(future_doc):
                    continue

                revision_months = (
                    (future_doc.year - baseline.year) * 12
                    + (future_doc.month - baseline.month)
                )

                if revision_months >= 3:

                    cumulative_event = True

                    if k == future_idx:
                        first_event = True

                    break

            # ------------------------------------------------
            # Exact event at T+h
            # ------------------------------------------------

            if first_event:
                events.append(1.0)
            else:
                events.append(0.0)

            # ------------------------------------------------
            # Cumulative event by T+h
            # ------------------------------------------------

            if cumulative_event:
                risks.append(1.0)
            else:
                risks.append(0.0)

    df[event_col] = events
    df[risk_col] = risks

# ------------------------------------------------------------
# 6. CURRENT MATERIAL DETERIORATION
# ------------------------------------------------------------
#
# This is retained only as descriptive information.
# It is NOT used as a predictor.
# ------------------------------------------------------------

df["material_deterioration"] = np.nan

valid_current = (
    df["revised_doc_date"].notna()
    & df["anchor_baseline_revised_doc"].notna()
)

df.loc[valid_current, "material_deterioration"] = 0.0

# ------------------------------------------------------------
# 7. SAVE
# ------------------------------------------------------------

df.to_csv(OUTPUT, index=False)

# ------------------------------------------------------------
# 8. SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ANCHOR LABEL SUMMARY")
print("=" * 70)

for h in range(1, 6):

    event_col = f"event_t_plus_{h}"
    risk_col = f"risk_by_t_plus_{h}"

    known_event = df[event_col].notna().sum()
    event_count = (df[event_col] == 1).sum()

    known_risk = df[risk_col].notna().sum()
    risk_count = (df[risk_col] == 1).sum()

    print(
        f"\nT+{h}"
        f"\n  Exact event: known={known_event}, "
        f"events={event_count}"
        f"\n  Cumulative:  known={known_risk}, "
        f"events={risk_count}"
    )

    if known_event > 0:
        print(
            f"  Exact event rate: "
            f"{event_count / known_event * 100:.2f}%"
        )

    if known_risk > 0:
        print(
            f"  Cumulative risk rate: "
            f"{risk_count / known_risk * 100:.2f}%"
        )

print("\n" + "=" * 70)
print("STEP 13 COMPLETE")
print("=" * 70)

print(f"\nSaved: {OUTPUT}")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
