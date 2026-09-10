from pathlib import Path
import random
import csv

from src.ml.provisional_research import (
    build_s1_cohort,
    month_index,
    read_csv,
)

# ============================================================
# PATHS
# ============================================================

DATASET = Path(
    "data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv"
)

# Use the same authoritative coverage file as the frozen S1 pipeline.
COVERAGE_FILE = Path(
    "data/metadata/source_coverage_2023_07_2026_06.csv"
)

OUTPUT = Path(
    "validation/s1/s1_human_validation_sample.csv"
)


# SETTINGS
# ============================================================

SEED = 26103
CASES_PER_CLASS_PER_REGIME = 10

# 3 temporal regimes
REGIMES = {
    "APR_JUN_2025": {
        "months": {"2025-04", "2025-05", "2025-06"},
        "events": 10,
        "non_events": 10,
    },
    "JUL_NOV_2025": {
        "months": {
            "2025-07", "2025-08", "2025-09",
            "2025-10", "2025-11"
        },
        "events": 10,
        "non_events": 10,
    },
    "DEC_2025_MAR_2026": {
        "months": {
            "2025-12", "2026-01", "2026-02", "2026-03"
        },
        "events": 10,
        "non_events": 10,
    },
}


# ============================================================
# HELPERS
# ============================================================

def safe_value(row, *names):
    """
    Return the first non-empty value among possible column names.
    """
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return value
    return ""


def read_coverage(path):
    """
    Read the authoritative S1 coverage file and return:

        reporting_month -> coverage_class
    """
    rows = read_csv(path)

    return {
        row["reporting_month"]: row["coverage_class"]
        for row in rows
    }


def get_row_for_month(project_rows, month):
    """
    Find one project observation for a specific reporting month.
    """
    for row in project_rows:
        if str(row.get("reporting_month", "")).strip() == month:
            return row

    return None


def get_project_history(rows, project_id):
    """
    Return all observations belonging to one canonical project.
    """
    history = [
        row
        for row in rows
        if str(row.get("canonical_project_id", "")).strip()
        == str(project_id).strip()
    ]

    history.sort(
        key=lambda x: str(x.get("reporting_month", ""))
    )

    return history


def build_case_row(
    anchor,
    future_rows,
    label,
    regime,
    report_month,
):
    """
    Convert one S1 case into a human-review row.
    """

    output = {
        # ----------------------------------------------------
        # CASE IDENTIFICATION
        # ----------------------------------------------------
        "regime": regime,
        "machine_label": label,
        "canonical_project_id": safe_value(
            anchor,
            "canonical_project_id",
        ),
        "anchor_month": safe_value(
            anchor,
            "reporting_month",
        ),

        # ----------------------------------------------------
        # ANCHOR INFORMATION
        # ----------------------------------------------------
        "anchor_project_code": safe_value(
            anchor,
            "project_code",
        ),
        "anchor_project_name": safe_value(
            anchor,
            "project_name_raw",
            "project_name",
            "reported_project_name",
        ),
        "anchor_agency": safe_value(
            anchor,
            "agency_raw",
            "agency",
            "reported_agency",
        ),
        "anchor_original_target_doc": safe_value(
            anchor,
            "original_target_doc_raw",
            "reported_original_target_doc",
        ),
        "anchor_revised_doc": safe_value(
            anchor,
            "revised_doc_raw",
            "reported_revised_doc",
        ),
        "anchor_physical_progress": safe_value(
            anchor,
            "physical_progress_raw",
            "physical_progress",
            "reported_physical_progress",
        ),
        "anchor_cumulative_expenditure": safe_value(
            anchor,
            "cumulative_expenditure_raw",
            "cumulative_expenditure",
            "reported_cumulative_expenditure",
        ),
        "anchor_source_id": safe_value(
            anchor,
            "source_id",
        ),
        "anchor_source_sha256": safe_value(
            anchor,
            "source_sha256",
        ),
        "anchor_pdf_page_index": safe_value(
            anchor,
            "pdf_page_index",
        ),
        "anchor_printed_page_number": safe_value(
            anchor,
            "printed_page_number",
        ),
        "anchor_source_table": safe_value(
            anchor,
            "source_table",
        ),
        "anchor_raw_row_locator": safe_value(
            anchor,
            "raw_row_locator",
        ),

        # ----------------------------------------------------
        # FUTURE MONTH 1
        # ----------------------------------------------------
        "future_1_month": "",
        "future_1_project_code": "",
        "future_1_project_name": "",
        "future_1_original_target_doc": "",
        "future_1_revised_doc": "",
        "future_1_physical_progress": "",
        "future_1_cumulative_expenditure": "",
        "future_1_source_id": "",
        "future_1_source_sha256": "",
        "future_1_pdf_page_index": "",
        "future_1_printed_page_number": "",
        "future_1_source_table": "",
        "future_1_raw_row_locator": "",

        # ----------------------------------------------------
        # FUTURE MONTH 2
        # ----------------------------------------------------
        "future_2_month": "",
        "future_2_project_code": "",
        "future_2_project_name": "",
        "future_2_original_target_doc": "",
        "future_2_revised_doc": "",
        "future_2_physical_progress": "",
        "future_2_cumulative_expenditure": "",
        "future_2_source_id": "",
        "future_2_source_sha256": "",
        "future_2_pdf_page_index": "",
        "future_2_printed_page_number": "",
        "future_2_source_table": "",
        "future_2_raw_row_locator": "",

        # ----------------------------------------------------
        # FUTURE MONTH 3
        # ----------------------------------------------------
        "future_3_month": "",
        "future_3_project_code": "",
        "future_3_project_name": "",
        "future_3_original_target_doc": "",
        "future_3_revised_doc": "",
        "future_3_physical_progress": "",
        "future_3_cumulative_expenditure": "",
        "future_3_source_id": "",
        "future_3_source_sha256": "",
        "future_3_pdf_page_index": "",
        "future_3_printed_page_number": "",
        "future_3_source_table": "",
        "future_3_raw_row_locator": "",

        # ----------------------------------------------------
        # HUMAN REVIEW FIELDS
        # ----------------------------------------------------
        "manual_label": "",
        "manual_event_month": "",
        "manual_identity_confirmed": "",
        "manual_anchor_date_confirmed": "",
        "manual_future_change_confirmed": "",
        "manual_approval_evidence": "",
        "manual_issue_type": "",
        "reviewer": "",
        "review_notes": "",
    }

    # --------------------------------------------------------
    # Fill future observations
    # --------------------------------------------------------

    for i, future in enumerate(future_rows[:3], start=1):

        prefix = f"future_{i}_"

        output[prefix + "month"] = safe_value(
            future,
            "reporting_month",
        )

        output[prefix + "project_code"] = safe_value(
            future,
            "project_code",
        )

        output[prefix + "project_name"] = safe_value(
            future,
            "project_name_raw",
            "project_name",
            "reported_project_name",
        )

        output[prefix + "original_target_doc"] = safe_value(
            future,
            "original_target_doc_raw",
            "reported_original_target_doc",
        )

        output[prefix + "revised_doc"] = safe_value(
            future,
            "revised_doc_raw",
            "reported_revised_doc",
        )

        output[prefix + "physical_progress"] = safe_value(
            future,
            "physical_progress_raw",
            "physical_progress",
            "reported_physical_progress",
        )

        output[prefix + "cumulative_expenditure"] = safe_value(
            future,
            "cumulative_expenditure_raw",
            "cumulative_expenditure",
            "reported_cumulative_expenditure",
        )

        output[prefix + "source_id"] = safe_value(
            future,
            "source_id",
        )

        output[prefix + "source_sha256"] = safe_value(
            future,
            "source_sha256",
        )

        output[prefix + "pdf_page_index"] = safe_value(
            future,
            "pdf_page_index",
        )

        output[prefix + "printed_page_number"] = safe_value(
            future,
            "printed_page_number",
        )

        output[prefix + "source_table"] = safe_value(
            future,
            "source_table",
        )

        output[prefix + "raw_row_locator"] = safe_value(
            future,
            "raw_row_locator",
        )

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    print("Loading dataset...")

    if not DATASET.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATASET}"
        )

    if not COVERAGE_FILE.exists():
        raise FileNotFoundError(
            f"Coverage file not found:\n{COVERAGE_FILE}"
        )

    # --------------------------------------------------------
    # Load project-month dataset
    # --------------------------------------------------------

    rows = read_csv(DATASET)

    print(f"Loaded {len(rows):,} project-month rows.")

    # --------------------------------------------------------
    # Load monthly coverage metadata
    # --------------------------------------------------------

    coverage = read_coverage(COVERAGE_FILE)

    print(
        f"Loaded coverage information for "
        f"{len(coverage)} reporting months."
    )

    # --------------------------------------------------------
    # Build frozen S1 cohort
    # --------------------------------------------------------

    print("Building frozen S1 cohort...")

    cohort = build_s1_cohort(rows, coverage, 3)

    print(
        f"S1 cohort contains {len(cohort):,} anchors."
    )

    if not cohort:
        raise RuntimeError(
            "S1 cohort is empty. "
            "Check the frozen S1 implementation."
        )

    # --------------------------------------------------------
    # Convert cohort into regime buckets
    # --------------------------------------------------------

    buckets = {}

    for regime, config in REGIMES.items():
        months = config["months"]

        buckets[regime] = {
            "event": [],
            "non_event": [],
        }

        for case in cohort:
            anchor_month = str(
                case.get("anchor_month", "")
            ).strip()

            if anchor_month not in months:
                continue

            event = int(case.get("event", 0))

            if event == 1:
                buckets[regime]["event"].append(case)
            else:
                buckets[regime]["non_event"].append(case)

    # --------------------------------------------------------
    # Print available cases
    # --------------------------------------------------------

    print()
    print("Available S1 cases by regime:")

    for regime in REGIMES:

        events = len(buckets[regime]["event"])
        non_events = len(buckets[regime]["non_event"])

        print(
            f"  {regime}: "
            f"{events} events, "
            f"{non_events} non-events"
        )

    # --------------------------------------------------------
    # Stratified sampling
    # --------------------------------------------------------

    rng = random.Random(SEED)

    selected = []

    print()
    print("Selecting validation cases...")

    for regime in REGIMES:

        event_cases = buckets[regime]["event"]
        non_event_cases = buckets[regime]["non_event"]

        if len(event_cases) < CASES_PER_CLASS_PER_REGIME:
            raise RuntimeError(
                f"Not enough event cases in {regime}. "
                f"Available={len(event_cases)}, "
                f"required={CASES_PER_CLASS_PER_REGIME}"
            )

        if len(non_event_cases) < CASES_PER_CLASS_PER_REGIME:
            raise RuntimeError(
                f"Not enough non-event cases in {regime}. "
                f"Available={len(non_event_cases)}, "
                f"required={CASES_PER_CLASS_PER_REGIME}"
            )

        sampled_events = rng.sample(
            event_cases,
            CASES_PER_CLASS_PER_REGIME,
        )

        sampled_non_events = rng.sample(
            non_event_cases,
            CASES_PER_CLASS_PER_REGIME,
        )

        for case in sampled_events:
            selected.append(
                (
                    regime,
                    "EVENT",
                    case,
                )
            )

        for case in sampled_non_events:
            selected.append(
                (
                    regime,
                    "NON_EVENT",
                    case,
                )
            )

    # --------------------------------------------------------
    # Sort selected cases
    # --------------------------------------------------------

    selected.sort(
        key=lambda x: (
            x[0],
            x[1],
            str(
                x[2].get(
                    "reporting_month",
                    "",
                )
            ),
            str(
                x[2].get(
                    "canonical_project_id",
                    "",
                )
            ),
        )
    )

    # --------------------------------------------------------
    # Build output rows
    # --------------------------------------------------------

    output_rows = []

    for regime, label_text, case in selected:

        project_id = case.get(
            "canonical_project_id",
            "",
        )

        anchor_month = case.get(
            "anchor_month",
            "",
        )

        # --------------------------------------------
        # Find project history
        # --------------------------------------------

        history = get_project_history(
            rows,
            project_id,
        )

        # --------------------------------------------
        # Find the actual dataset row for the anchor
        # --------------------------------------------

        anchor = next(
            (
                row
                for row in history
                if str(row.get("reporting_month", "")).strip()
                == str(anchor_month).strip()
            ),
            None,
        )

        if anchor is None:
            raise RuntimeError(
                f"Anchor row not found for "
                f"project={project_id}, "
                f"anchor_month={anchor_month}"
            )

        # --------------------------------------------
        # Get exact next 3 calendar months
        # --------------------------------------------

        future_months = []

        current_month = str(
            anchor_month
        ).strip()

        for step in range(1, 4):

            current_index = month_index(current_month)
            next_index = current_index + step
            year = (next_index - 1) // 12
            month_num = (next_index - 1) % 12 + 1
            next_month = f"{year:04d}-{month_num:02d}"

            future_months.append(next_month)

        future_rows = []

        for month in future_months:

            row = get_row_for_month(
                history,
                month,
            )

            if row is not None:
                future_rows.append(row)

        # --------------------------------------------
        # Build human-review row
        # --------------------------------------------

        output_row = build_case_row(
            anchor=anchor,
            future_rows=future_rows,
            label=label_text,
            regime=regime,
            report_month=coverage,
        )

        output_rows.append(output_row)

    # --------------------------------------------------------
    # Write CSV
    # --------------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not output_rows:
        raise RuntimeError(
            "No validation rows were generated."
        )

    fieldnames = list(
        output_rows[0].keys()
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        writer.writerows(output_rows)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("S1 HUMAN VALIDATION SAMPLE CREATED")
    print("=" * 60)

    print(
        f"Output: {OUTPUT}"
    )

    print(
        f"Total cases: {len(output_rows)}"
    )

    print()

    for regime in REGIMES:

        regime_rows = [
            row
            for row in output_rows
            if row["regime"] == regime
        ]

        events = sum(
            row["machine_label"] == "EVENT"
            for row in regime_rows
        )

        non_events = sum(
            row["machine_label"] == "NON_EVENT"
            for row in regime_rows
        )

        print(
            f"{regime}: "
            f"{len(regime_rows)} cases "
            f"({events} events, "
            f"{non_events} non-events)"
        )

    print()
    print(
        "Next step: manually verify each selected "
        "case against its cited source pages/rows."
    )


if __name__ == "__main__":
    main()
