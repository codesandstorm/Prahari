"""Production validation for observation-to-source provenance."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Any

from src.pipeline.source_registry import ELIGIBLE_STATUSES, load_manifest, validate_manifest

REQUIRED_PROVENANCE_FIELDS = (
    "source_id",
    "source_sha256",
    "pdf_page_index",
    "source_table",
    "extraction_method",
    "extractor_version",
    "raw_row_locator",
)


def validate_provenance_record(
    record: Mapping[str, Any],
    manifest_path: Path,
) -> list[str]:
    """Return actionable validation errors for one future observation."""
    errors: list[str] = []
    for field in REQUIRED_PROVENANCE_FIELDS:
        value = record.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"missing required provenance field: {field}")

    rows = load_manifest(manifest_path)
    manifest_errors = validate_manifest(rows)
    if manifest_errors:
        return errors + [f"manifest invalid: {error}" for error in manifest_errors]

    source_id = str(record.get("source_id", "")).strip()
    matches = [row for row in rows if row.get("source_id", "").strip() == source_id]
    if len(matches) != 1:
        errors.append(f"unknown or non-unique source_id: {source_id!r}")
    else:
        source = matches[0]
        if source.get("file_status", "").strip() not in ELIGIBLE_STATUSES:
            errors.append(f"source_id is not eligible: {source_id}")
        expected = source.get("sha256", "").strip().lower()
        actual = str(record.get("source_sha256", "")).strip().lower()
        if not actual or actual != expected:
            errors.append(f"source_sha256 does not match manifest for {source_id}")

    page = record.get("pdf_page_index")
    try:
        if int(page) < 1:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(f"invalid pdf_page_index: {page!r}")
    return errors


def validate_empty_provenance_registry(path: Path) -> list[str]:
    """Validate that the pre-extraction registry has the exact header and no rows."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    missing = [field for field in REQUIRED_PROVENANCE_FIELDS if field not in fields]
    errors = [f"missing provenance column: {field}" for field in missing]
    if rows:
        errors.append(f"provenance registry must be empty before extraction; found {len(rows)} rows")
    return errors


def validate_provenance_registry(
    path: Path,
    manifest_path: Path,
    *,
    expected_rows: int | None = None,
) -> list[str]:
    """Validate a populated registry, including row count and unique locators."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []

    errors = [
        f"missing provenance column: {field}"
        for field in REQUIRED_PROVENANCE_FIELDS
        if field not in fields
    ]
    if expected_rows is not None and len(rows) != expected_rows:
        errors.append(f"provenance row count {len(rows)} != expected {expected_rows}")

    observation_ids: set[str] = set()
    raw_locators: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        errors.extend(
            f"provenance row {index}: {error}"
            for error in validate_provenance_record(row, manifest_path)
        )
        observation_id = row.get("observation_id", "").strip()
        if not observation_id:
            errors.append(f"provenance row {index}: missing observation_id")
        elif observation_id in observation_ids:
            errors.append(f"provenance row {index}: duplicate observation_id {observation_id}")
        observation_ids.add(observation_id)
        locator = row.get("raw_row_locator", "").strip()
        locator_key = (row.get("source_id", "").strip(), locator)
        if locator_key in raw_locators:
            errors.append(
                f"provenance row {index}: duplicate source/raw_row_locator {locator_key}"
            )
        raw_locators.add(locator_key)
    return errors
