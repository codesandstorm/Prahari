import os
import pandas as pd

BASE = "data/processed/longitudinal_2023_07_2026_06_mixed"

RF_FULL_FILE = os.path.join(
    BASE,
    "step19_random_forest_results.csv"
)

RF_ROBUST_FILE = os.path.join(
    BASE,
    "step22_target_proxy_ablation_results.csv"
)

XGB_FILE = os.path.join(
    BASE,
    "step25_xgboost_threshold_results.csv"
)

OUTPUT = os.path.join(
    BASE,
    "step26_final_model_comparison.csv"
)


def horizon_number(horizon):
    text = str(horizon)

    if "t_plus_" in text:
        return int(text.split("t_plus_")[-1])

    if "+" in text:
        return int(text.split("+")[-1].split()[0])

    return 999


print("=" * 75)
print("PRAHARI STEP 26 - FINAL MODEL COMPARISON")
print("=" * 75)


# ============================================================
# LOAD RESULTS
# ============================================================

rf_full_raw = pd.read_csv(RF_FULL_FILE)
rf_robust_raw = pd.read_csv(RF_ROBUST_FILE)
xgb_raw = pd.read_csv(XGB_FILE)

print("\nFiles loaded successfully.")


# ============================================================
# RF FULL
# ============================================================

rf_full = rf_full_raw.copy()

rf_full["model"] = "RF_FULL"
rf_full["threshold"] = 0.50

rf_full = rf_full[
    [
        "horizon",
        "model",
        "threshold",
        "test_recall",
        "test_f1",
        "test_roc_auc",
        "test_pr_auc",
        "test_brier"
    ]
].copy()

rf_full.columns = [
    "horizon",
    "model",
    "threshold",
    "recall",
    "f1",
    "roc_auc",
    "pr_auc",
    "brier"
]


# ============================================================
# RF ROBUST
# ============================================================

rf_robust = rf_robust_raw[
    rf_robust_raw["model"] == "WITHOUT_SCHEDULE_PROXY"
].copy()

if len(rf_robust) == 0:
    raise SystemExit(
        "ERROR: WITHOUT_SCHEDULE_PROXY not found."
    )

rf_robust["model"] = "RF_ROBUST"
rf_robust["threshold"] = 0.50

rf_robust = rf_robust[
    [
        "horizon",
        "model",
        "threshold",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
        "brier"
    ]
].copy()


# ============================================================
# XGBOOST ROBUST
# ============================================================

xgb = xgb_raw.copy()

xgb["model"] = "XGBOOST_ROBUST"

xgb = xgb[
    [
        "horizon",
        "model",
        "threshold",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
        "brier"
    ]
].copy()


# ============================================================
# COMBINE
# ============================================================

comparison = pd.concat(
    [
        rf_full,
        rf_robust,
        xgb
    ],
    ignore_index=True
)


# ============================================================
# SORT
# ============================================================

comparison["horizon_number"] = comparison[
    "horizon"
].apply(horizon_number)

comparison = comparison.sort_values(
    [
        "horizon_number",
        "model"
    ]
)

comparison = comparison.drop(
    columns=["horizon_number"]
)


# ============================================================
# SAVE
# ============================================================

comparison.to_csv(
    OUTPUT,
    index=False
)


# ============================================================
# FINAL MODEL COMPARISON
# ============================================================

print("\n")
print("=" * 75)
print("FINAL MODEL COMPARISON")
print("=" * 75)

print(
    comparison.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# BEST MODEL BY ROC-AUC
# ============================================================

print("\n")
print("=" * 75)
print("BEST MODEL BY ROC-AUC")
print("=" * 75)

for horizon in sorted(
    comparison["horizon"].unique(),
    key=horizon_number
):

    subset = comparison[
        comparison["horizon"] == horizon
    ]

    best = subset.loc[
        subset["roc_auc"].idxmax()
    ]

    print(
        f"{horizon} -> {best['model']} "
        f"| ROC-AUC = {best['roc_auc']:.4f}"
    )


# ============================================================
# BEST MODEL BY PR-AUC
# ============================================================

print("\n")
print("=" * 75)
print("BEST MODEL BY PR-AUC")
print("=" * 75)

for horizon in sorted(
    comparison["horizon"].unique(),
    key=horizon_number
):

    subset = comparison[
        comparison["horizon"] == horizon
    ]

    best = subset.loc[
        subset["pr_auc"].idxmax()
    ]

    print(
        f"{horizon} -> {best['model']} "
        f"| PR-AUC = {best['pr_auc']:.4f}"
    )


# ============================================================
# BEST MODEL BY F1
# ============================================================

print("\n")
print("=" * 75)
print("BEST MODEL BY F1")
print("=" * 75)

for horizon in sorted(
    comparison["horizon"].unique(),
    key=horizon_number
):

    subset = comparison[
        comparison["horizon"] == horizon
    ]

    best = subset.loc[
        subset["f1"].idxmax()
    ]

    print(
        f"{horizon} -> {best['model']} "
        f"| F1 = {best['f1']:.4f}"
    )


# ============================================================
# ROBUST RF VS XGBOOST
# ============================================================

print("\n")
print("=" * 75)
print("ROBUST RF VS XGBOOST")
print("=" * 75)

robust = comparison[
    comparison["model"].isin(
        [
            "RF_ROBUST",
            "XGBOOST_ROBUST"
        ]
    )
]

for horizon in sorted(
    robust["horizon"].unique(),
    key=horizon_number
):

    subset = robust[
        robust["horizon"] == horizon
    ]

    rf = subset[
        subset["model"] == "RF_ROBUST"
    ]

    xgb_row = subset[
        subset["model"] == "XGBOOST_ROBUST"
    ]

    if len(rf) == 1 and len(xgb_row) == 1:

        rf = rf.iloc[0]
        xgb_row = xgb_row.iloc[0]

        print(f"\n{horizon}")

        print(
            f"RF Robust      "
            f"ROC={rf['roc_auc']:.4f} "
            f"PR={rf['pr_auc']:.4f} "
            f"Recall={rf['recall']:.4f} "
            f"F1={rf['f1']:.4f}"
        )

        print(
            f"XGBoost Robust "
            f"ROC={xgb_row['roc_auc']:.4f} "
            f"PR={xgb_row['pr_auc']:.4f} "
            f"Recall={xgb_row['recall']:.4f} "
            f"F1={xgb_row['f1']:.4f}"
        )


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================

print("\n")
print("=" * 75)
print("RESEARCH INTERPRETATION")
print("=" * 75)

print("""
RF_FULL
-------
Operational model using schedule information.

RF_ROBUST
---------
Robust research model with schedule-proxy variables removed.

XGBOOST_ROBUST
--------------
Advanced boosting benchmark using robust features.

MODEL SELECTION
---------------
Model selection should consider:

1. ROC-AUC
2. PR-AUC
3. Recall
4. F1
5. Brier score
6. Early-warning objective
7. Robustness after schedule-proxy removal

IMPORTANT
---------
T+5 has limited test observability.

The 2026 period is the temporal held-out evaluation period.

No random train/test split was used.
""")


print("\nResults saved to:")
print(OUTPUT)

print("\n")
print("=" * 75)
print("STEP 26 COMPLETE")
print("=" * 75)
