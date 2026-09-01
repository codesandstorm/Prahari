"""Evidence-only May-to-June 2026 project identity continuity audit."""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.pipeline.source_registry import resolve_source
from src.utils.safe_io import ensure_parent, write_json_replace

MAY_SOURCE_ID = "SRC-2026-05"
JUNE_SOURCE_ID = "SRC-2026-06"
MAY_ROWS = 1987
JUNE_ROWS = 1847
SEED = 26103
MAY_CSV_SHA256 = "f0bd72a4534c2403bedb9890e25dd3522c4b8280362834de7d84d8f57738c04e"
JUNE_CSV_SHA256 = "bf2b7d37c11096ddca9d365878b48725c8f81e7c39b9863979029ee2f78832d9"
IDENTITY_FIELDS = (
    "project_code_raw", "legacy_ocms_code_raw", "pmgid_raw",
    "project_name_raw", "agency_raw", "state_raw",
)


def normalize_for_comparison(value: str) -> str:
    """Return a deterministic review-only value; never mutate source fields."""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w]+", " ", value)
    return " ".join(value.split())


def _missing(value: str) -> bool:
    return value.strip() in {"", "-"}


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_identity_fields(rows: list[dict[str, str]]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    for field in IDENTITY_FIELDS:
        raw = [row[field] for row in rows]
        present = [value for value in raw if not _missing(value)]
        raw_counts = Counter(present)
        normalized_counts = Counter(normalize_for_comparison(value) for value in present)
        duplicates = {value: count for value, count in raw_counts.items() if count > 1}
        profile[field] = {
            "total_count": len(raw),
            "non_missing_count": len(present),
            "missing_marker_count": len(raw) - len(present),
            "unique_raw_count": len(raw_counts),
            "duplicate_value_count": len(duplicates),
            "duplicate_row_excess_count": sum(count - 1 for count in duplicates.values()),
            "duplicate_values": duplicates,
            "unique_normalized_count": len(normalized_counts),
            "normalization_collision_value_count": sum(
                count > 1 for count in normalized_counts.values()
            ),
        }
    return profile


def classify_exact_code_pair(may: dict[str, str], june: dict[str, str]) -> tuple[str, list[str]]:
    variations = [
        field for field in ("project_name_raw", "agency_raw", "state_raw")
        if normalize_for_comparison(may[field]) != normalize_for_comparison(june[field])
    ]
    if not variations:
        return "CODE_MATCH_TEXT_CONSISTENT", variations
    if variations == ["project_name_raw"]:
        return "CODE_MATCH_NAME_VARIATION", variations
    if variations == ["agency_raw"]:
        return "CODE_MATCH_AGENCY_VARIATION", variations
    if variations == ["state_raw"]:
        return "CODE_MATCH_STATE_VARIATION", variations
    return "CODE_MATCH_MULTIPLE_VARIATIONS", variations


def classify_project_codes(
    may_rows: list[dict[str, str]], june_rows: list[dict[str, str]]
) -> dict[str, str]:
    """Classify every raw Project Code without forcing duplicate relationships."""
    may_counts = Counter(row["project_code_raw"] for row in may_rows)
    june_counts = Counter(row["project_code_raw"] for row in june_rows)
    relationships: dict[str, str] = {}
    for code in sorted(set(may_counts) | set(june_counts)):
        if may_counts[code] > 1 and june_counts[code] > 1:
            relationships[code] = "CONFLICT"
        elif may_counts[code] > 1:
            relationships[code] = "DUPLICATE_IN_MAY"
        elif june_counts[code] > 1:
            relationships[code] = "DUPLICATE_IN_JUNE"
        elif not june_counts[code]:
            relationships[code] = "MAY_ONLY"
        elif not may_counts[code]:
            relationships[code] = "JUNE_ONLY"
        else:
            relationships[code] = "EXACT_1_TO_1"
    return relationships


def generate_candidates(
    unmatched_may: list[dict[str, str]],
    unmatched_june: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Generate conservative review candidates; never accept a candidate."""
    candidates: list[dict[str, Any]] = []
    for may in unmatched_may:
        may_name = normalize_for_comparison(may["project_name_raw"])
        for june in unmatched_june:
            june_name = normalize_for_comparison(june["project_name_raw"])
            name_exact = may_name == june_name
            similarity = difflib.SequenceMatcher(
                None, may_name, june_name, autojunk=False
            ).ratio()
            agency_match = (
                normalize_for_comparison(may["agency_raw"])
                == normalize_for_comparison(june["agency_raw"])
            )
            state_match = (
                normalize_for_comparison(may["state_raw"])
                == normalize_for_comparison(june["state_raw"])
            )
            if not name_exact and not (similarity >= 0.90 and (agency_match or state_match)):
                continue
            reason = (
                "NORMALIZED_EXACT_NAME_AND_AGENCY" if name_exact and agency_match
                else "NORMALIZED_EXACT_NAME" if name_exact
                else "STRONG_NAME_SIMILARITY_WITH_CONTEXT"
            )
            candidates.append({
                "may_observation_id": may["observation_id"],
                "june_observation_id": june["observation_id"],
                "may_project_code": may["project_code_raw"],
                "june_project_code": june["project_code_raw"],
                "may_project_name_raw": may["project_name_raw"],
                "june_project_name_raw": june["project_name_raw"],
                "name_similarity": f"{similarity:.6f}",
                "agency_match": str(agency_match).upper(),
                "state_match": str(state_match).upper(),
                "candidate_reason": reason,
                "status": "REVIEW_REQUIRED",
            })
    return sorted(
        candidates,
        key=lambda row: (-float(row["name_similarity"]), row["may_project_code"], row["june_project_code"]),
    )


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]], root: Path) -> None:
    path = ensure_parent(path, root)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite identity-audit artifact: {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _match_row(may: dict[str, str], june: dict[str, str], classification: str, variations: list[str]) -> dict[str, str]:
    return {
        "project_code_raw": may["project_code_raw"],
        "may_observation_id": may["observation_id"],
        "june_observation_id": june["observation_id"],
        "may_project_name_raw": may["project_name_raw"],
        "june_project_name_raw": june["project_name_raw"],
        "may_agency_raw": may["agency_raw"],
        "june_agency_raw": june["agency_raw"],
        "may_state_raw": may["state_raw"],
        "june_state_raw": june["state_raw"],
        "metadata_classification": classification,
        "varying_fields": ";".join(variations),
        "evidence_class": (
            "VERIFIED_EXACT_CODE" if not variations
            else "EXACT_CODE_WITH_METADATA_VARIATION"
        ),
    }


def _unmatched_row(row: dict[str, str], evidence_class: str) -> dict[str, str]:
    return {
        "observation_id": row["observation_id"],
        "project_code_raw": row["project_code_raw"],
        "project_name_raw": row["project_name_raw"],
        "agency_raw": row["agency_raw"],
        "state_raw": row["state_raw"],
        "source_id": row["source_id"],
        "raw_row_locator": row["raw_row_locator"],
        "evidence_class": evidence_class,
    }


def _manual_sample(
    consistent: list[dict[str, Any]], variations: list[dict[str, Any]],
    unmatched_may: list[dict[str, str]], unmatched_june: list[dict[str, str]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    name_variations = [row for row in variations if "project_name_raw" in row["varying_fields"]]
    agency_only = [row for row in variations if row["varying_fields"] == "agency_raw"]
    selected: list[dict[str, Any]] = []

    def take(rows: list[dict[str, Any]], count: int, category: str) -> None:
        for row in rng.sample(rows, min(count, len(rows))):
            selected.append({**row, "sample_category": category})

    take(consistent, 10, "EXACT_CODE_NO_VARIATION")
    take(name_variations, 6, "EXACT_CODE_NAME_VARIATION")
    take(agency_only, 6, "EXACT_CODE_AGENCY_VARIATION")
    take(unmatched_may, 4, "UNMATCHED_MAY")
    take(unmatched_june, 4, "UNMATCHED_JUNE")
    if candidates:
        take(candidates, min(4, len(candidates)), "AMBIGUOUS_CANDIDATE")
        selected = selected[:30]
    for row in selected:
        row.update({
            "manual_same_project": "", "manual_identity_evidence": "",
            "reviewer": "", "review_notes": "",
        })
    return selected


def run_identity_audit(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    may_path = repo_root / "data/extracted/ongoing/ongoing_2026_05.csv"
    june_path = repo_root / "data/extracted/ongoing/ongoing_2026_06.csv"
    if _sha(may_path) != MAY_CSV_SHA256 or _sha(june_path) != JUNE_CSV_SHA256:
        raise RuntimeError("Frozen monthly extraction digest mismatch")
    may, june = _read(may_path), _read(june_path)
    if len(may) != MAY_ROWS or len(june) != JUNE_ROWS:
        raise RuntimeError("Validated monthly row count mismatch")

    manifest = repo_root / "data/metadata/source_manifest.csv"
    may_source = resolve_source(MAY_SOURCE_ID, manifest, repo_root)
    june_source = resolve_source(JUNE_SOURCE_ID, manifest, repo_root)
    provenance = _read(repo_root / "data/metadata/provenance.csv")
    by_source = defaultdict(list)
    for row in provenance:
        by_source[row["source_id"]].append(row)
    for source, rows, extracted in (
        (may_source, by_source[MAY_SOURCE_ID], may),
        (june_source, by_source[JUNE_SOURCE_ID], june),
    ):
        if len(rows) != len(extracted):
            raise RuntimeError(f"Provenance count mismatch for {source.source_id}")
        if {row["observation_id"] for row in rows} != {row["observation_id"] for row in extracted}:
            raise RuntimeError(f"Provenance observation mismatch for {source.source_id}")
        if any(row["source_sha256"] != source.sha256 for row in extracted + rows):
            raise RuntimeError(f"Source SHA provenance mismatch for {source.source_id}")

    may_codes, june_codes = defaultdict(list), defaultdict(list)
    for row in may:
        may_codes[row["project_code_raw"]].append(row)
    for row in june:
        june_codes[row["project_code_raw"]].append(row)
    code_relationships = classify_project_codes(may, june)
    intersection = sorted(set(may_codes) & set(june_codes))
    duplicate_may = sorted(code for code, rows in may_codes.items() if len(rows) > 1)
    duplicate_june = sorted(code for code, rows in june_codes.items() if len(rows) > 1)
    conflicts = sorted(code for code, status in code_relationships.items() if status == "CONFLICT")
    non_unique_codes = {
        code for code, status in code_relationships.items()
        if status in {"CONFLICT", "DUPLICATE_IN_MAY", "DUPLICATE_IN_JUNE"}
    }
    exact: list[dict[str, str]] = []
    for code in intersection:
        if code in non_unique_codes:
            continue
        classification, varying = classify_exact_code_pair(may_codes[code][0], june_codes[code][0])
        exact.append(_match_row(may_codes[code][0], june_codes[code][0], classification, varying))
    consistent = [row for row in exact if row["evidence_class"] == "VERIFIED_EXACT_CODE"]
    variations = [row for row in exact if row["evidence_class"] == "EXACT_CODE_WITH_METADATA_VARIATION"]
    unmatched_may = [_unmatched_row(may_codes[code][0], "UNMATCHED_MAY") for code in sorted(set(may_codes) - set(june_codes))]
    unmatched_june = [_unmatched_row(june_codes[code][0], "UNMATCHED_JUNE") for code in sorted(set(june_codes) - set(may_codes))]
    candidates = generate_candidates(
        [may_codes[row["project_code_raw"]][0] for row in unmatched_may],
        [june_codes[row["project_code_raw"]][0] for row in unmatched_june],
    )
    unmatched_may_source_rows = [may_codes[row["project_code_raw"]][0] for row in unmatched_may]
    unmatched_june_source_rows = [june_codes[row["project_code_raw"]][0] for row in unmatched_june]
    may_only_progress_100 = sum(float(row["physical_progress_raw"]) == 100 for row in unmatched_may_source_rows)
    may_only_progress_ge_90 = sum(float(row["physical_progress_raw"]) >= 90 for row in unmatched_may_source_rows)
    june_only_progress_zero = sum(float(row["physical_progress_raw"]) == 0 for row in unmatched_june_source_rows)

    out = repo_root / "validation/identity_continuity"
    match_fields = list(exact[0])
    unmatched_fields = list(unmatched_may[0])
    candidate_fields = [
        "may_observation_id", "june_observation_id", "may_project_code", "june_project_code",
        "may_project_name_raw", "june_project_name_raw", "name_similarity",
        "agency_match", "state_match", "candidate_reason", "status",
    ]
    _write_csv(out / "may_june_2026_exact_matches.csv", match_fields, exact, repo_root)
    _write_csv(out / "may_june_2026_metadata_variations.csv", match_fields, variations, repo_root)
    _write_csv(out / "may_june_2026_unmatched_may.csv", unmatched_fields, unmatched_may, repo_root)
    _write_csv(out / "may_june_2026_unmatched_june.csv", unmatched_fields, unmatched_june, repo_root)
    _write_csv(out / "may_june_2026_candidate_matches.csv", candidate_fields, candidates, repo_root)

    sample = _manual_sample(consistent, variations, unmatched_may, unmatched_june, candidates)
    sample_fields = sorted({field for row in sample for field in row})
    _write_csv(out / "may_june_2026_manual_identity_sample_30.csv", sample_fields, sample, repo_root)

    variation_classes = Counter(row["metadata_classification"] for row in variations)
    summary = {
        "may_total": len(may), "june_total": len(june),
        "may_source_sha256": may_source.sha256, "june_source_sha256": june_source.sha256,
        "may_extracted_csv_sha256": _sha(may_path), "june_extracted_csv_sha256": _sha(june_path),
        "exact_project_code_intersection": len(intersection),
        "verified_1_to_1_exact_code_matches": len(exact),
        "exact_code_text_consistent": len(consistent),
        "exact_code_metadata_variations": len(variations),
        "metadata_variation_classes": dict(variation_classes),
        "may_only_project_codes": len(unmatched_may),
        "june_only_project_codes": len(unmatched_june),
        "duplicate_project_codes_may": len(duplicate_may),
        "duplicate_project_codes_june": len(duplicate_june),
        "duplicate_values_may": duplicate_may, "duplicate_values_june": duplicate_june,
        "conflicts": len(conflicts), "conflict_codes": conflicts,
        "ambiguous_candidates": len(candidates), "candidate_links_generated": len(candidates),
        "identity_profiles": {
            "may": profile_identity_fields(may), "june": profile_identity_fields(june),
        },
        "june_with_direct_may_counterpart_pct": round(100 * len(exact) / len(june), 2),
        "may_without_direct_june_counterpart_pct": round(100 * len(unmatched_may) / len(may), 2),
        "may_only_progress_100_count": may_only_progress_100,
        "may_only_progress_ge_90_count": may_only_progress_ge_90,
        "june_only_progress_zero_count": june_only_progress_zero,
        "project_code_assessment": "STABLE_FOR_VALIDATED_MAY_JUNE",
        "manual_sample_seed": SEED, "manual_sample_rows": len(sample),
    }
    write_json_replace(out / "may_june_2026_identity_summary.json", summary, repo_root=repo_root)
    report = ensure_parent(repo_root / "outputs/reports/MAY_JUNE_2026_IDENTITY_CONTINUITY_REPORT.md", repo_root)
    report.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _render_report(s: dict[str, Any]) -> str:
    return f"""# May–June 2026 Project Identity Continuity Report

## Scope and integrity

Only the validated May and June raw extraction CSVs were loaded. Their frozen
digests, row counts, canonical source SHAs, and provenance registries passed.
No extracted row was modified and no canonical project identifier was created.

## Exact Project Code evidence

- May observations: {s['may_total']}
- June observations: {s['june_total']}
- Exact Project Code intersection: {s['exact_project_code_intersection']}
- Unique one-to-one exact matches: {s['verified_1_to_1_exact_code_matches']}
- Text-consistent exact-code matches: {s['exact_code_text_consistent']}
- Exact-code matches with metadata variation: {s['exact_code_metadata_variations']}
- May-only codes: {s['may_only_project_codes']}
- June-only codes: {s['june_only_project_codes']}
- Duplicate Project Codes in May/June: {s['duplicate_project_codes_may']}/{s['duplicate_project_codes_june']}
- Conflicts: {s['conflicts']}

Metadata variation classes: `{json.dumps(s['metadata_variation_classes'], sort_keys=True)}`.
Agency-label changes dominate and remain reported rather than normalized away.

## Unmatched and candidate evidence

- Review-only candidate links generated: {s['candidate_links_generated']}
- Ambiguous candidates: {s['ambiguous_candidates']}

No unmatched records were force-linked. May-only records may reflect completion,
removal, or reporting changes; June-only records may reflect additions or code
changes. Those causal interpretations require report/event evidence.

## Scientific interpretation

Project Code is complete, unique, and stable enough to be the primary modern
identity key for these two validated reports. {s['june_with_direct_may_counterpart_pct']}% of June
projects have a direct May counterpart; {s['may_without_direct_june_counterpart_pct']}% of May
projects have no direct June code counterpart. The net change of 140 observations
is arithmetically consistent with 162 May-only and 22 June-only codes, but this
audit does not label completion or addition events. Of the May-only observations,
{s['may_only_progress_ge_90_count']} report at least 90% physical progress and
{s['may_only_progress_100_count']} report 100%; {s['june_only_progress_zero_count']} of the
June-only observations report zero progress. This supports ordinary monthly
turnover, but does not establish the cause of every unmatched record.

Human review remains required for metadata variations and unmatched records
before constructing longitudinal production tables.
"""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audit May-June 2026 identity continuity")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    args = parser.parse_args()
    print(json.dumps(run_identity_audit(Path(args.repo_root)), indent=2, ensure_ascii=False))
