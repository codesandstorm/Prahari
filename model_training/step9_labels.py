import pandas as pd

path = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv"

df = pd.read_csv(path, low_memory=False)

# Convert dates
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

# Sort by project and month
df = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).copy()

# Previous known revised DOC
df["previous_known_revised_doc"] = (
    df.groupby("canonical_project_id")["revised_doc_date"]
      .ffill()
      .groupby(df["canonical_project_id"])
      .shift(1)
)

# Calculate schedule change in months
df["schedule_change_months"] = (
    (df["revised_doc_date"].dt.year -
     df["previous_known_revised_doc"].dt.year) * 12
    +
    (df["revised_doc_date"].dt.month -
     df["previous_known_revised_doc"].dt.month)
)

# Candidate material deterioration:
# revised completion date moves 3+ months later
df["material_deterioration"] = (
    df["schedule_change_months"] >= 3
).astype("Int64")

# If comparison is impossible, outcome is unknown
df.loc[
    df["revised_doc_date"].isna()
    | df["previous_known_revised_doc"].isna(),
    "material_deterioration"
] = pd.NA

# Create T+1 to T+5 exact-event labels
event_data = df[
    [
        "canonical_project_id",
        "reporting_month",
        "material_deterioration"
    ]
].copy()

for h in range(1, 6):

    future = event_data.copy()

    future["reporting_month"] = (
        future["reporting_month"]
        - pd.DateOffset(months=h)
    )

    future = future.rename(
        columns={
            "material_deterioration":
                f"label_t_plus_{h}"
        }
    )

    future = future[
        [
            "canonical_project_id",
            "reporting_month",
            f"label_t_plus_{h}"
        ]
    ]

    df = df.merge(
        future,
        on=[
            "canonical_project_id",
            "reporting_month"
        ],
        how="left"
    )

# SUMMARY

print("=" * 70)
print("PRAHARI T+1 TO T+5 LABEL AUDIT")
print("=" * 70)

print("\nTotal rows:", len(df))

print("\nCurrent material deterioration:")
print(
    df["material_deterioration"]
    .value_counts(dropna=False)
    .sort_index()
)

for h in range(1, 6):

    col = f"label_t_plus_{h}"

    known = df[col].notna().sum()
    events = (df[col] == 1).sum()
    unknown = df[col].isna().sum()

    print("\n" + "-" * 50)
    print(f"T+{h}")
    print("-" * 50)

    print("Known outcomes:", known)
    print("Events:", events)
    print("Unknown:", unknown)

    if known > 0:
        print(
            "Event rate:",
            round(events / known * 100, 2),
            "%"
        )

# Anchor month summary

print("\n" + "=" * 70)
print("LABEL AVAILABILITY BY ANCHOR MONTH")
print("=" * 70)

summary = []

for month, group in df.groupby("reporting_month"):

    row = {
        "anchor_month": month.strftime("%Y-%m"),
        "rows": len(group)
    }

    for h in range(1, 6):

        col = f"label_t_plus_{h}"

        row[f"T+{h}_known"] = group[col].notna().sum()
        row[f"T+{h}_events"] = (group[col] == 1).sum()

    summary.append(row)

summary = pd.DataFrame(summary)

print(
    summary.tail(15).to_string(index=False)
)

print("\n" + "=" * 70)
print("STEP 9 COMPLETE")
print("=" * 70)
