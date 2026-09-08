import pandas as pd

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed/"

project_file = BASE + "project_month.csv"
obs_file = BASE + "horizon_observability.csv"
output_file = BASE + "project_month_labels.csv"

print("=" * 60)
print("PRAHARI STEP 10 - CORRECT LABELS")
print("=" * 60)

df = pd.read_csv(project_file, low_memory=False)
obs = pd.read_csv(obs_file)

print("Rows loaded:", len(df))

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

obs["anchor_month"] = pd.to_datetime(
    obs["anchor_month"],
    format="%Y-%m",
    errors="coerce"
)

df = df.sort_values(
    ["canonical_project_id", "reporting_month"]
).copy()

df["previous_known_revised_doc"] = (
    df.groupby("canonical_project_id")["revised_doc_date"]
      .ffill()
      .groupby(df["canonical_project_id"])
      .shift(1)
)

df["schedule_change_months"] = (
    (df["revised_doc_date"].dt.year -
     df["previous_known_revised_doc"].dt.year) * 12
    +
    (df["revised_doc_date"].dt.month -
     df["previous_known_revised_doc"].dt.month)
)

df["material_deterioration"] = (
    df["schedule_change_months"] >= 3
).astype("Int64")

df.loc[
    df["revised_doc_date"].isna()
    | df["previous_known_revised_doc"].isna(),
    "material_deterioration"
] = pd.NA

print()
print("Current material deterioration:")
print(
    df["material_deterioration"]
    .value_counts(dropna=False)
    .sort_index()
)

events = df[
    [
        "canonical_project_id",
        "reporting_month",
        "material_deterioration"
    ]
].copy()

events = events.rename(
    columns={"material_deterioration": "event"}
)

df = df.set_index(
    ["canonical_project_id", "reporting_month"]
)

for h in range(1, 6):

    future = events.copy()

    future["reporting_month"] = (
        future["reporting_month"]
        - pd.DateOffset(months=h)
    )

    future = future.rename(
        columns={"event": f"event_t_plus_{h}"}
    )

    future = future.set_index(
        ["canonical_project_id", "reporting_month"]
    )

    df = df.join(
        future[[f"event_t_plus_{h}"]],
        how="left"
    )

df = df.reset_index()

obs2 = obs[
    ["anchor_month", "horizon_months", "observability_status"]
].pivot(
    index="anchor_month",
    columns="horizon_months",
    values="observability_status"
)

obs2.columns = [
    f"obs_t_plus_{int(x)}"
    for x in obs2.columns
]

df = df.merge(
    obs2.reset_index(),
    left_on="reporting_month",
    right_on="anchor_month",
    how="left"
)

df = df.drop(
    columns=["anchor_month"],
    errors="ignore"
)

for h in range(1, 6):

    event_col = f"event_t_plus_{h}"
    obs_col = f"obs_t_plus_{h}"

    if obs_col in df.columns:

        df.loc[
            df[obs_col] != "FULLY_OBSERVABLE",
            event_col
        ] = pd.NA

for h in range(1, 6):

    risk_col = f"risk_by_t_plus_{h}"

    cols = [
        f"event_t_plus_{j}"
        for j in range(1, h + 1)
    ]

    values = df[cols]

    any_event = (
        values.fillna(0).sum(axis=1) > 0
    )

    all_known = values.notna().all(axis=1)

    df[risk_col] = pd.NA

    df.loc[any_event, risk_col] = 1

    df.loc[
        all_known & (~any_event),
        risk_col
    ] = 0

    df[risk_col] = df[risk_col].astype("Int64")

print()
print("=" * 60)
print("EXACT EVENT LABELS")
print("=" * 60)

for h in range(1, 6):

    col = f"event_t_plus_{h}"

    known = df[col].notna().sum()
    event_count = (df[col] == 1).sum()
    unknown = df[col].isna().sum()

    print(
        "T+{}: known={}, events={}, unknown={}".format(
            h, known, event_count, unknown
        )
    )

    if known > 0:
        print(
            "     event rate: {:.2f}%".format(
                event_count / known * 100
            )
        )

print()
print("=" * 60)
print("CUMULATIVE RISK LABELS")
print("=" * 60)

for h in range(1, 6):

    col = f"risk_by_t_plus_{h}"

    known = df[col].notna().sum()
    event_count = (df[col] == 1).sum()
    unknown = df[col].isna().sum()

    print(
        "By T+{}: known={}, events={}, unknown={}".format(
            h, known, event_count, unknown
        )
    )

    if known > 0:
        print(
            "     event rate: {:.2f}%".format(
                event_count / known * 100
            )
        )

df.to_csv(output_file, index=False)

print()
print("=" * 60)
print("STEP 10 COMPLETE")
print("=" * 60)
print("Saved:", output_file)
print("Rows:", len(df))
print("Columns:", len(df.columns))
