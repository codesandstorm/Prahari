import pandas as pd
import numpy as np

INPUT = "data/processed/longitudinal_2023_07_2026_06_mixed/project_month_labels_v2.csv"

print("=" * 70)
print("PRAHARI STEP 13B - LABEL VALIDATION")
print("=" * 70)

df = pd.read_csv(INPUT, low_memory=False)

df["reporting_month"] = pd.to_datetime(
    df["reporting_month"],
    errors="coerce"
)

print("\nRows:", len(df))

# ------------------------------------------------------------
# 1. LABEL AVAILABILITY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("LABEL AVAILABILITY")
print("=" * 70)

for h in range(1, 6):

    event = f"event_t_plus_{h}"
    risk = f"risk_by_t_plus_{h}"

    print(
        f"T+{h}: "
        f"event known={df[event].notna().sum()}, "
        f"risk known={df[risk].notna().sum()}"
    )

# ------------------------------------------------------------
# 2. EVENT COUNTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EVENT COUNTS")
print("=" * 70)

for h in range(1, 6):

    event = f"event_t_plus_{h}"
    risk = f"risk_by_t_plus_{h}"

    event_count = (df[event] == 1).sum()
    risk_count = (df[risk] == 1).sum()

    print(
        f"T+{h}: "
        f"exact events={event_count}, "
        f"cumulative events={risk_count}"
    )

# ------------------------------------------------------------
# 3. MONOTONIC CUMULATIVE RISK CHECK
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("CUMULATIVE RISK MONOTONICITY")
print("=" * 70)

violations = {}

for h in range(1, 5):

    current = df[f"risk_by_t_plus_{h}"]
    future = df[f"risk_by_t_plus_{h+1}"]

    comparable = current.notna() & future.notna()

    violation = (
        (future[comparable] < current[comparable])
    ).sum()

    violations[f"T+{h} -> T+{h+1}"] = violation

    print(
        f"T+{h} -> T+{h+1}: "
        f"{violation} violations"
    )

# ------------------------------------------------------------
# 4. EXACT EVENT UNIQUENESS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EXACT EVENT UNIQUENESS")
print("=" * 70)

# A project/anchor should have at most one first event
# across T+1 ... T+5.

event_cols = [
    f"event_t_plus_{h}"
    for h in range(1, 6)
]

known = df[event_cols].notna().all(axis=1)

multiple_events = (
    df.loc[known, event_cols]
      .sum(axis=1)
      .gt(1)
      .sum()
)

print(
    "Anchors with more than one exact event:",
    multiple_events
)

# ------------------------------------------------------------
# 5. EVENT -> CUMULATIVE CONSISTENCY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EVENT / CUMULATIVE CONSISTENCY")
print("=" * 70)

consistency_violations = 0

for h in range(1, 6):

    event = df[f"event_t_plus_{h}"]
    risk = df[f"risk_by_t_plus_{h}"]

    comparable = event.notna() & risk.notna()

    bad = (
        (event[comparable] == 1)
        & (risk[comparable] != 1)
    ).sum()

    consistency_violations += bad

    print(
        f"T+{h}: event=1 but cumulative=0 -> {bad}"
    )

# ------------------------------------------------------------
# 6. EXAMPLE PROJECT TRAJECTORIES
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EXAMPLE PROJECT TRAJECTORIES")
print("=" * 70)

projects = (
    df["canonical_project_id"]
    .dropna()
    .drop_duplicates()
    .head(3)
    .tolist()
)

cols = [
    "canonical_project_id",
    "reporting_month",
    "anchor_baseline_revised_doc",
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

for project in projects:

    print("\nPROJECT:", project)

    sample = (
        df[df["canonical_project_id"] == project][cols]
        .head(10)
    )

    print(sample.to_string(index=False))

# ------------------------------------------------------------
# 7. FINAL
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("STEP 13B COMPLETE")
print("=" * 70)

print("\nMonotonicity violations:")
print(violations)

print(
    "\nEvent/cumulative consistency violations:",
    consistency_violations
)

print(
    "\nAnchors with multiple exact events:",
    multiple_events
)
