"""Manifest-backed source resolution and metadata validation."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from src.extraction.pdf_inspector import compute_sha256

ELIGIBLE_STATUSES = frozenset({"CANONICAL", "MULTIPART_SOURCE"})
EXCLUDED_STATUSES = frozenset({"REJECTED_DUPLICATE", "MISSING"})
COMPLETENESS_STATES = frozenset({
    "SINGLE_FILE", "MULTIPART_PARTIAL", "MULTIPART_COMPLETE", "MULTIPART_UNKNOWN"
})


class SourceRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedSource:
    source_id: str
    source_group_id: str
    source_part: str
    path: Path
    filename: str
    report_year: int
    report_month: int
    sha256: str
    file_status: str
    completeness_status: str
    manifest_row: dict[str, str]


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_part(value: str) -> str:
    value = value.strip().upper()
    if value in {"", "DUP"}:
        return value
    if not re.fullmatch(r"\d+", value):
        raise SourceRegistryError(f"Invalid source_part: {value!r}")
    return f"{int(value):02d}"


def validate_manifest(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_parts: set[tuple[str, str]] = set()
    group_periods: dict[str, tuple[str, str]] = {}
    group_hashes: dict[str, dict[str, str]] = {}

    for line, row in enumerate(rows, start=2):
        sid = row.get("source_id", "").strip()
        group = row.get("source_group_id", "").strip()
        status = row.get("file_status", "").strip()
        completeness = row.get("completeness_status", "").strip()
        if not sid or sid in seen_ids:
            errors.append(f"line {line}: empty or duplicate source_id {sid!r}")
        seen_ids.add(sid)
        if status not in ELIGIBLE_STATUSES | EXCLUDED_STATUSES:
            errors.append(f"line {line}: invalid file_status {status!r}")
        if completeness not in COMPLETENESS_STATES:
            errors.append(f"line {line}: invalid completeness_status {completeness!r}")
        try:
            part = _normalize_part(row.get("source_part", ""))
        except SourceRegistryError as exc:
            errors.append(f"line {line}: {exc}")
            part = row.get("source_part", "")
        if group and part and status != "REJECTED_DUPLICATE":
            key = (group, part)
            if key in seen_parts:
                errors.append(f"line {line}: duplicate source group/part {key}")
            seen_parts.add(key)
        period = (row.get("report_year", "").strip(), row.get("report_month", "").strip())
        if group and all(period):
            if group in group_periods and group_periods[group] != period:
                errors.append(f"line {line}: group {group} has mismatched reporting period")
            group_periods[group] = period
        digest = row.get("sha256", "").strip().lower()
        if group and digest and status in ELIGIBLE_STATUSES:
            prior = group_hashes.setdefault(group, {})
            if digest in prior:
                errors.append(
                    f"line {line}: duplicate hash within multipart group {group}: {sid} and {prior[digest]}"
                )
            prior[digest] = sid
    return errors


def resolve_source(
    source_id: str,
    manifest_path: Path,
    repo_root: Path,
    eligible_statuses: frozenset[str] = ELIGIBLE_STATUSES,
) -> ResolvedSource:
    rows = load_manifest(manifest_path)
    manifest_errors = validate_manifest(rows)
    if manifest_errors:
        raise SourceRegistryError("Invalid source manifest: " + "; ".join(manifest_errors))
    matches = [row for row in rows if row.get("source_id", "").strip() == source_id]
    if len(matches) != 1:
        raise SourceRegistryError(f"source_id must resolve exactly once: {source_id!r}")
    row = matches[0]
    status = row.get("file_status", "").strip()
    if status not in eligible_statuses:
        raise SourceRegistryError(f"Source {source_id} is not extraction-eligible: {status}")
    relative = Path(row.get("relative_path", ""))
    if not relative.as_posix().strip():
        raise SourceRegistryError(f"Source {source_id} has no relative_path")
    root = repo_root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SourceRegistryError(f"Source path escapes repository: {relative}") from exc
    if not path.is_file():
        raise SourceRegistryError(f"Source file not found: {path}")
    expected = row.get("sha256", "").strip().lower()
    actual = compute_sha256(path)
    if not expected or actual != expected:
        raise SourceRegistryError(f"SHA-256 mismatch for {source_id}: expected={expected}, actual={actual}")
    try:
        year = int(row["report_year"])
        month = int(row["report_month"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceRegistryError(f"Invalid report period for {source_id}") from exc
    if not 1 <= month <= 12:
        raise SourceRegistryError(f"Invalid report month for {source_id}: {month}")
    return ResolvedSource(
        source_id=source_id,
        source_group_id=row.get("source_group_id", "").strip(),
        source_part=_normalize_part(row.get("source_part", "")),
        path=path,
        filename=row.get("filename", "").strip(),
        report_year=year,
        report_month=month,
        sha256=actual,
        file_status=status,
        completeness_status=row.get("completeness_status", "").strip(),
        manifest_row=row,
    )


def resolve_primary_target(config: dict, repo_root: Path) -> ResolvedSource:
    """Resolve and cross-check the configured first extraction target."""
    target = config.get("extraction", {}).get("primary_target")
    if not isinstance(target, dict):
        raise SourceRegistryError("CONFIG_ERROR: extraction.primary_target must be a mapping")
    source_id = str(target.get("source_id", "")).strip()
    if not source_id:
        raise SourceRegistryError("CONFIG_ERROR: primary_target.source_id is required")
    manifest_rel = config.get("manifest", {}).get("file", "data/metadata/source_manifest.csv")
    resolved = resolve_source(source_id, repo_root / manifest_rel, repo_root)
    expected_period = f"{resolved.report_year:04d}-{resolved.report_month:02d}"
    if str(target.get("report_month", "")).strip() != expected_period:
        raise SourceRegistryError(
            f"CONFIG_ERROR: primary target month does not match manifest: {target.get('report_month')!r} != {expected_period}"
        )
    configured_filename = str(target.get("source_file", "")).strip()
    if configured_filename and configured_filename != resolved.filename:
        raise SourceRegistryError(
            f"CONFIG_ERROR: primary target filename does not match resolved source: "
            f"{configured_filename!r} != {resolved.filename!r}"
        )
    return resolved


def multipart_overlap_warnings(records: list[dict[str, str]]) -> list[str]:
    """Warn when the same raw observation locator appears in two group parts.

    This is a pre-union guard for future extraction; it does not merge rows.
    """
    seen: dict[tuple[str, str], str] = {}
    warnings: list[str] = []
    for record in records:
        group = str(record.get("source_group_id", "")).strip()
        locator = str(record.get("raw_observation_identity", "")).strip()
        source_id = str(record.get("source_id", "")).strip()
        if not group or not locator:
            continue
        key = (group, locator)
        prior = seen.get(key)
        if prior and prior != source_id:
            warnings.append(
                f"possible multipart overlap in {group}: {locator!r} occurs in {prior} and {source_id}"
            )
        else:
            seen[key] = source_id
    return warnings
