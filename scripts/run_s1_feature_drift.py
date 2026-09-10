from pathlib import Path
import numpy as np
import pandas as pd

from src.ml.provisional_research import (
    build_s1_cohort,
    FEATURES_B,
)

SEED = 26103


# ============================================================
# SOURCE COVERAGE
# ============================================================

def get_coverage():

    coverage = {}

    project_level_months = [
        "2023-07", "2023-08", "2023-09", "2023-10", "2023-11",
        "2024-01", "2024-02", "2024-03",
        "2024-06", "2024-07",
        "2024-10", "2024-11", "2024-12",
        "2025-01",
        "2025-03", "2025-04", "2025-05", "2025-06",
        "2025-07", "2025-08", "2025-09", "2025-10", "2025-11",
        "2025-12",
        "2026-01", "2026-02", "2026-03",
        "2026-04", "2026-05", "2026-06",
    ]

    for month in project_level_months:
        coverage[month] = "PROJECT_LEVEL"

    for month in [
        "2023-12",
        "2024-04",
        "2024-05",
        "2024-08",
        "2024-09",
    ]:
        coverage[month] = "AGGREGATE_ONLY"

    coverage["2025-02"] = "MISSING_SOURCE"

    return coverage


# ============================================================
# PSI
# ============================================================

def calculate_psi(reference, current, bins=10):

    reference = pd.Series(reference).dropna().astype(float)
    current = pd.Series(current).dropna().astype(float)

    if len(reference) == 0 or len(current) == 0:
        return np.nan

    # If all values are identical
    if reference.nunique() <= 1:
        return 0.0

    # Quantile bins from reference population
    quantiles = np.linspace(
        0,
        1,
        bins + 1
    )

    edges = np.unique(
        reference.quantile(
            quantiles
        ).values
    )

    if len(edges) < 3:
        return 0.0

    # Extend boundaries
    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts, _ = np.histogram(
        reference,
        bins=edges
    )

    cur_counts, _ = np.histogram(
        current,
        bins=edges
    )

    ref_pct = (
        ref_counts / len(reference)
    )

    cur_pct = (
        cur_counts / len(current)
    )

    # Avoid log(0)
    ref_pct = np.where(
        ref_pct == 0,
        1e-6,
        ref_pct
    )

    cur_pct = np.where(
        cur_pct == 0,
        1e-6,
        cur_pct
    )

    psi = np.sum(
        (cur_pct - ref_pct)
        *
        np.log(cur_pct / ref_pct)
    )

    return float(psi)


# ============================================================
# STANDARDIZED MEAN DIFFERENCE
# ============================================================

def standardized_mean_difference(
    reference,
    current
):

    reference = pd.Series(
        reference
    ).dropna().astype(float)

    current = pd.Series(
        current
    ).dropna().astype(float)

    if len(reference) == 0 or len(current) == 0:
        return np.nan

    pooled_sd = np.sqrt(
        (
            reference.var()
            +
            current.var()
        )
        / 2
    )

    if pooled_sd == 0:
        return 0.0

    return float(
        (
            current.mean()
            -
            reference.mean()
        )
        /
        pooled_sd
    )


# ============================================================
# REGIMES
# ============================================================

REGIMES = {

    "APR-JUN-2025": (
        "2025-04",
        "2025-06",
    ),

    "JUL-NOV-2025": (
        "2025-07",
        "2025-11",
    ),

    "DEC-MAR-2026": (
        "2025-12",
        "2026-03",
    ),
}


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
    print("=" * 70)
    print("PRAHARI S1 FEATURE DISTRIBUTION / DRIFT AUDIT")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------

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
        len(data)
    )

    # --------------------------------------------------------
    # 2. BUILD EXACT S1 COHORT
    # --------------------------------------------------------

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
    print("=" * 70)
    print("EXACT S1 COHORT")
    print("=" * 70)

    print()
    print(
        "Anchors:",
        len(df)
    )

    print(
        "Events:",
        int(df["event"].sum())
    )

    # --------------------------------------------------------
    # 3. REGIME LABEL
    # --------------------------------------------------------

    def assign_regime(month):

        for regime_name, (
            start,
            end
        ) in REGIMES.items():

            if (
                month >= start
                and month <= end
            ):
                return regime_name

        return None

    df["regime"] = (
        df["anchor_month"]
        .apply(assign_regime)
    )

    df = df[
        df["regime"].notna()
    ].copy()

    print()
    print(
        "Regime counts:"
    )

    print(
        df["regime"]
        .value_counts()
        .reindex(
            REGIMES.keys()
        )
    )

    # --------------------------------------------------------
    # 4. BASIC DISTRIBUTION TABLE
    # --------------------------------------------------------

    distribution_results = []

    for feature in FEATURES_B:

        for regime_name in REGIMES:

            values = pd.to_numeric(
                df.loc[
                    df["regime"] == regime_name,
                    feature
                ],
                errors="coerce"
            )

            distribution_results.append(
                {
                    "feature": feature,
                    "regime": regime_name,
                    "n": int(values.notna().sum()),
                    "missing_pct": float(
                        values.isna().mean() * 100
                    ),
                    "mean": float(
                        values.mean()
                    )
                    if values.notna().any()
                    else np.nan,
                    "median": float(
                        values.median()
                    )
                    if values.notna().any()
                    else np.nan,
                    "std": float(
                        values.std()
                    )
                    if values.notna().sum() > 1
                    else np.nan,
                    "q25": float(
                        values.quantile(0.25)
                    )
                    if values.notna().any()
                    else np.nan,
                    "q75": float(
                        values.quantile(0.75)
                    )
                    if values.notna().any()
                    else np.nan,
                    "min": float(
                        values.min()
                    )
                    if values.notna().any()
                    else np.nan,
                    "max": float(
                        values.max()
                    )
                    if values.notna().any()
                    else np.nan,
                }
            )

    distribution_df = pd.DataFrame(
        distribution_results
    )

    # --------------------------------------------------------
    # 5. DRIFT: APR-JUN → JUL-NOV
    # --------------------------------------------------------

    drift_results = []

    reference_regime = "APR-JUN-2025"

    for feature in FEATURES_B:

        reference = pd.to_numeric(
            df.loc[
                df["regime"] == reference_regime,
                feature
            ],
            errors="coerce"
        )

        for current_regime in [
            "JUL-NOV-2025",
            "DEC-MAR-2026",
        ]:

            current = pd.to_numeric(
                df.loc[
                    df["regime"] == current_regime,
                    feature
                ],
                errors="coerce"
            )

            psi = calculate_psi(
                reference,
                current
            )

            smd = standardized_mean_difference(
                reference,
                current
            )

            drift_results.append(
                {
                    "feature": feature,
                    "comparison": (
                        f"{reference_regime} -> "
                        f"{current_regime}"
                    ),
                    "psi": psi,
                    "abs_smd": (
                        abs(smd)
                        if not pd.isna(smd)
                        else np.nan
                    ),
                    "smd": smd,
                }
            )

    drift_df = pd.DataFrame(
        drift_results
    )

    # --------------------------------------------------------
    # 6. PRINT DISTRIBUTIONS
    # --------------------------------------------------------

    print()
    print()
    print("=" * 70)
    print("FEATURE DISTRIBUTIONS BY REGIME")
    print("=" * 70)

    for feature in FEATURES_B:

        print()
        print(
            "-" * 70
        )

        print(
            feature
        )

        for regime_name in REGIMES:

            row = distribution_df[
                (
                    distribution_df["feature"]
                    == feature
                )
                &
                (
                    distribution_df["regime"]
                    == regime_name
                )
            ].iloc[0]

            print(
                f"{regime_name:<18} "
                f"N={int(row['n']):<5} "
                f"Missing={row['missing_pct']:.1f}% "
                f"Mean={row['mean']:.4f} "
                f"Median={row['median']:.4f} "
                f"Q25={row['q25']:.4f} "
                f"Q75={row['q75']:.4f}"
            )

    # --------------------------------------------------------
    # 7. PRINT DRIFT
    # --------------------------------------------------------

    print()
    print()
    print("=" * 70)
    print("FEATURE DRIFT")
    print("=" * 70)

    print()
    print(
        "Reference = APR-JUN-2025"
    )

    for feature in FEATURES_B:

        print()
        print(
            "-" * 70
        )

        print(
            feature
        )

        for comparison in [
            "APR-JUN-2025 -> JUL-NOV-2025",
            "APR-JUN-2025 -> DEC-MAR-2026",
        ]:

            row = drift_df[
                (
                    drift_df["feature"]
                    == feature
                )
                &
                (
                    drift_df["comparison"]
                    == comparison
                )
            ].iloc[0]

            print(
                f"{comparison:<35} "
                f"PSI={row['psi']:.4f} "
                f"SMD={row['smd']:.4f}"
            )

    # --------------------------------------------------------
    # 8. RANK FEATURES BY JUL-NOV DRIFT
    # --------------------------------------------------------

    jul_drift = drift_df[
        drift_df["comparison"]
        ==
        "APR-JUN-2025 -> JUL-NOV-2025"
    ].copy()

    jul_drift = jul_drift.sort_values(
        "psi",
        ascending=False
    )

    print()
    print()
    print("=" * 70)
    print("TOP FEATURES BY JUL-NOV DRIFT")
    print("=" * 70)

    print()

    for _, row in jul_drift.iterrows():

        print(
            f"{row['feature']:<35} "
            f"PSI={row['psi']:.4f} "
            f"|SMD|={row['abs_smd']:.4f}"
        )

    # --------------------------------------------------------
    # 9. SAVE RESULTS
    # --------------------------------------------------------

    output_dir = (
        repo_root
        / "outputs"
        / "ml"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    distribution_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_DISTRIBUTIONS.csv"
    )

    drift_file = (
        output_dir
        / "PRAHARI_S1_FEATURE_DRIFT.csv"
    )

    distribution_df.to_csv(
        distribution_file,
        index=False
    )

    drift_df.to_csv(
        drift_file,
        index=False
    )

    print()
    print()
    print("=" * 70)
    print("FILES SAVED")
    print("=" * 70)

    print()
    print(distribution_file)
    print(drift_file)

    print()


if __name__ == "__main__":
    main()
