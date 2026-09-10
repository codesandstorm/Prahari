from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.ml.provisional_research import (
    build_s1_cohort,
    FEATURES_B,
)


# ============================================================
# PRAHARI S1
# FEATURE–TARGET RELATIONSHIP STABILITY AUDIT
# ============================================================

REGIMES = {
    "APR-JUN-2025": ("2025-04", "2025-06"),
    "JUL-NOV-2025": ("2025-07", "2025-11"),
    "DEC-MAR-2026": ("2025-12", "2026-03"),
}


# ============================================================
# SOURCE COVERAGE
# ============================================================

def get_coverage():

    coverage = {}

    project_level_months = [
        "2023-07",
        "2023-08",
        "2023-09",
        "2023-10",
        "2023-11",
        "2024-01",
        "2024-02",
        "2024-03",
        "2024-06",
        "2024-07",
        "2024-10",
        "2024-11",
        "2024-12",
        "2025-01",
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06",
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]

    for month in project_level_months:
        coverage[month] = "PROJECT_LEVEL"

    aggregate_only_months = [
        "2023-12",
        "2024-04",
        "2024-05",
        "2024-08",
        "2024-09",
    ]

    for month in aggregate_only_months:
        coverage[month] = "AGGREGATE_ONLY"

    coverage["2025-02"] = "MISSING_SOURCE"

    return coverage


# ============================================================
# REGIME ASSIGNMENT
# ============================================================

def assign_regime(month):

    if pd.isna(month):
        return None

    month = str(month)

    for regime_name, (start, end) in REGIMES.items():

        if start <= month <= end:
            return regime_name

    return None


# ============================================================
# BIN EVENT RATE
# ============================================================

def calculate_bin_event_rates(
    df,
    feature,
    n_bins=5,
):

    work = df[
        [feature, "event"]
    ].copy()

    work[feature] = pd.to_numeric(
        work[feature],
        errors="coerce",
    )

    work = work.dropna()

    if len(work) < 20:
        return pd.DataFrame()

    # --------------------------------------------------------
    # qcut creates approximately equal-sized groups.
    # duplicates='drop' handles repeated values.
    # --------------------------------------------------------

    try:

        work["bin"] = pd.qcut(
            work[feature],
            q=n_bins,
            duplicates="drop",
        )

    except ValueError:

        return pd.DataFrame()

    result = (
        work
        .groupby(
            "bin",
            observed=False,
        )
        .agg(
            n=("event", "size"),
            events=("event", "sum"),
            event_rate=("event", "mean"),
            feature_mean=(feature, "mean"),
            feature_median=(feature, "median"),
        )
        .reset_index()
    )

    result["event_rate"] = (
        result["event_rate"] * 100
    )

    return result


# ============================================================
# SPEARMAN CORRELATION
# ============================================================

def calculate_spearman(
    df,
    feature,
):

    x = pd.to_numeric(
        df[feature],
        errors="coerce",
    )

    y = pd.to_numeric(
        df["event"],
        errors="coerce",
    )

    mask = (
        x.notna()
        & y.notna()
    )

    x = x[mask]
    y = y[mask]

    if len(x) < 10:
        return np.nan, np.nan, len(x)

    if x.nunique() <= 1:
        return np.nan, np.nan, len(x)

    correlation, p_value = spearmanr(
        x,
        y,
    )

    return (
        float(correlation),
        float(p_value),
        len(x),
    )


# ============================================================
# EVENT RATE DIFFERENCE
# ============================================================

def calculate_event_rate(df):

    if len(df) == 0:
        return np.nan

    return float(
        df["event"].mean() * 100
    )


# ============================================================
# MAIN
# ============================================================

def main():

    repo_root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    print()
    print("=" * 75)
    print(
        "PRAHARI S1 FEATURE-TARGET RELATIONSHIP "
        "STABILITY AUDIT"
    )
    print("=" * 75)

    # ========================================================
    # 1. LOAD DATA
    # ========================================================

    dataset_path = (
        repo_root
        / "data"
        / "processed"
        / "longitudinal_2023_07_2026_06_mixed"
        / "project_month.csv"
    )

    print()
    print("Dataset:")
    print(dataset_path)

    data = pd.read_csv(
        dataset_path
    )

    print()
    print(
        "Rows:",
        len(data),
    )

    # ========================================================
    # 2. BUILD EXACT S1 COHORT
    # ========================================================

    data = data.replace(
        {np.nan: ""}
    )

    rows = (
        data
        .astype(str)
        .to_dict("records")
    )

    coverage = get_coverage()

    cohort_rows = build_s1_cohort(
        rows,
        coverage,
        horizon=3,
    )

    df = pd.DataFrame(
        cohort_rows
    )

    print()
    print("=" * 75)
    print("EXACT S1 COHORT")
    print("=" * 75)

    print()
    print(
        "Anchors:",
        len(df),
    )

    print(
        "Events:",
        int(df["event"].sum()),
    )

    print(
        "Overall event rate:",
        f"{df['event'].mean() * 100:.2f}%",
    )

    # ========================================================
    # 3. ASSIGN REGIMES
    # ========================================================

    df["regime"] = (
        df["anchor_month"]
        .apply(assign_regime)
    )

    df = df[
        df["regime"].notna()
    ].copy()

    print()
    print("=" * 75)
    print("REGIME COUNTS")
    print("=" * 75)

    for regime_name in REGIMES:

        subset = df[
            df["regime"] == regime_name
        ]

        print(
            f"{regime_name:<20} "
            f"anchors={len(subset):<5} "
            f"events={int(subset['event'].sum()):<5} "
            f"event_rate="
            f"{subset['event'].mean() * 100:.2f}%"
        )

    # ========================================================
    # 4. SPEARMAN RELATIONSHIP
    # ========================================================

    correlation_results = []

    print()
    print("=" * 75)
    print("FEATURE–TARGET SPEARMAN RELATIONSHIP")
    print("=" * 75)

    for feature in FEATURES_B:

        print()
        print("-" * 75)
        print(feature)

        for regime_name in REGIMES:

            subset = df[
                df["regime"] == regime_name
            ]

            rho, p_value, n = (
                calculate_spearman(
                    subset,
                    feature,
                )
            )

            correlation_results.append(
                {
                    "feature": feature,
                    "regime": regime_name,
                    "n": n,
                    "spearman_rho": rho,
                    "p_value": p_value,
                }
            )

            if pd.isna(rho):

                print(
                    f"{regime_name:<20} "
                    f"rho=NA"
                )

            else:

                print(
                    f"{regime_name:<20} "
                    f"rho={rho:>7.4f} "
                    f"p={p_value:.6f} "
                    f"N={n}"
                )

    correlation_df = pd.DataFrame(
        correlation_results
    )

    # ========================================================
    # 5. RELATIONSHIP CHANGE
    # ========================================================

    print()
    print("=" * 75)
    print(
        "FEATURE–TARGET RELATIONSHIP CHANGE"
    )
    print("=" * 75)

    relationship_results = []

    for feature in FEATURES_B:

        values = {}

        for regime_name in REGIMES:

            row = correlation_df[
                (
                    correlation_df["feature"]
                    == feature
                )
                &
                (
                    correlation_df["regime"]
                    == regime_name
                )
            ]

            if len(row) == 0:
                values[regime_name] = np.nan
            else:
                values[regime_name] = (
                    row.iloc[0]["spearman_rho"]
                )

        apr = values["APR-JUN-2025"]
        jul = values["JUL-NOV-2025"]
        dec = values["DEC-MAR-2026"]

        apr_jul_change = (
            jul - apr
            if not pd.isna(apr)
            and not pd.isna(jul)
            else np.nan
        )

        jul_dec_change = (
            dec - jul
            if not pd.isna(jul)
            and not pd.isna(dec)
            else np.nan
        )

        apr_dec_change = (
            dec - apr
            if not pd.isna(apr)
            and not pd.isna(dec)
            else np.nan
        )

        relationship_results.append(
            {
                "feature": feature,
                "rho_apr_jun": apr,
                "rho_jul_nov": jul,
                "rho_dec_mar": dec,
                "change_apr_to_jul": apr_jul_change,
                "change_jul_to_dec": jul_dec_change,
                "change_apr_to_dec": apr_dec_change,
                "abs_change_apr_to_jul": (
                    abs(apr_jul_change)
                    if not pd.isna(apr_jul_change)
                    else np.nan
                ),
            }
        )

    relationship_df = pd.DataFrame(
        relationship_results
    )

    relationship_df = relationship_df.sort_values(
        "abs_change_apr_to_jul",
        ascending=False,
    )

    print()

    for _, row in relationship_df.iterrows():

        print(
            f"{row['feature']:<35} "
            f"Apr-Jun={row['rho_apr_jun']:>7.4f} "
            f"Jul-Nov={row['rho_jul_nov']:>7.4f} "
            f"Dec-Mar={row['rho_dec_mar']:>7.4f} "
            f"| "
            f"ΔApr→Jul="
            f"{row['change_apr_to_jul']:>7.4f}"
        )

    # ========================================================
    # 6. BINNED EVENT RATES
    # ========================================================

    bin_results = []

    print()
    print("=" * 75)
    print(
        "BINNED FEATURE → EVENT RELATIONSHIP"
    )
    print("=" * 75)

    for feature in FEATURES_B:

        print()
        print("=" * 75)
        print(feature)
        print("=" * 75)

        for regime_name in REGIMES:

            subset = df[
                df["regime"] == regime_name
            ]

            result = calculate_bin_event_rates(
                subset,
                feature,
                n_bins=5,
            )

            if result.empty:
                continue

            print()
            print(
                regime_name
            )

            for bin_number, (_, row) in enumerate(
                result.iterrows(),
                start=1,
            ):

                print(
                    f"  Bin {bin_number}: "
                    f"N={int(row['n']):<4} "
                    f"Events={int(row['events']):<4} "
                    f"EventRate="
                    f"{row['event_rate']:.2f}% "
                    f"Mean="
                    f"{row['feature_mean']:.4f}"
                )

                bin_results.append(
                    {
                        "feature": feature,
                        "regime": regime_name,
                        "bin": bin_number,
                        "n": int(row["n"]),
                        "events": int(row["events"]),
                        "event_rate_pct": (
                            row["event_rate"]
                        ),
                        "feature_mean": (
                            row["feature_mean"]
                        ),
                        "feature_median": (
                            row["feature_median"]
                        ),
                    }
                )

    bins_df = pd.DataFrame(
        bin_results
    )

    # ========================================================
    # 7. DIRECTIONAL STABILITY
    # ========================================================

    print()
    print("=" * 75)
    print(
        "DIRECTIONAL STABILITY CHECK"
    )
    print("=" * 75)

    directional_results = []

    for feature in FEATURES_B:

        feature_bins = bins_df[
            bins_df["feature"] == feature
        ]

        directions = {}

        for regime_name in REGIMES:

            regime_bins = feature_bins[
                feature_bins["regime"]
                == regime_name
            ]

            if len(regime_bins) < 3:
                directions[regime_name] = "INSUFFICIENT"
                continue

            first_rate = (
                regime_bins
                .sort_values("bin")
                .iloc[0]["event_rate_pct"]
            )

            last_rate = (
                regime_bins
                .sort_values("bin")
                .iloc[-1]["event_rate_pct"]
            )

            if last_rate > first_rate:
                direction = "POSITIVE"
            elif last_rate < first_rate:
                direction = "NEGATIVE"
            else:
                direction = "FLAT"

            directions[regime_name] = direction

        directional_results.append(
            {
                "feature": feature,
                "apr_jun_direction": directions[
                    "APR-JUN-2025"
                ],
                "jul_nov_direction": directions[
                    "JUL-NOV-2025"
                ],
                "dec_mar_direction": directions[
                    "DEC-MAR-2026"
                ],
            }
        )

    directional_df = pd.DataFrame(
        directional_results
    )

    print()

    for _, row in directional_df.iterrows():

        print(
            f"{row['feature']:<35} "
            f"Apr-Jun={row['apr_jun_direction']:<12} "
            f"Jul-Nov={row['jul_nov_direction']:<12} "
            f"Dec-Mar={row['dec_mar_direction']:<12}"
        )

    # ========================================================
    # 8. SAVE RESULTS
    # ========================================================

    output_dir = (
        repo_root
        / "outputs"
        / "ml"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    correlation_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_TARGET_CORRELATION.csv"
    )

    relationship_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_TARGET_RELATIONSHIP_STABILITY.csv"
    )

    bins_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_TARGET_BINS.csv"
    )

    direction_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_TARGET_DIRECTION.csv"
    )

    correlation_df.to_csv(
        correlation_file,
        index=False,
    )

    relationship_df.to_csv(
        relationship_file,
        index=False,
    )

    bins_df.to_csv(
        bins_file,
        index=False,
    )

    directional_df.to_csv(
        direction_file,
        index=False,
    )

    # ========================================================
    # 9. FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 75)
    print("FILES SAVED")
    print("=" * 75)

    print()
    print(correlation_file)
    print(relationship_file)
    print(bins_file)
    print(direction_file)

    print()
    print("=" * 75)
    print("AUDIT COMPLETE")
    print("=" * 75)
    print()


if __name__ == "__main__":
    main()
