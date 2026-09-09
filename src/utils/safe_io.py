"""Repository-scoped safe writing helpers.

All repository writers must resolve their destination through this module.  The
raw source directory is an immutable input store, including through case
aliases, ``..`` traversal, and resolved junction/symlink aliases.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Any


class UnsafeWritePathError(ValueError):
    """Raised when a write would target the immutable raw source tree."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _canonical(path: Path) -> Path:
    """Resolve existing ancestors and normalize case for containment checks."""
    return Path(os.path.normcase(str(path.resolve(strict=False))))


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Case-insensitive containment for security semantics on every host."""
    path_parts = tuple(part.casefold() for part in path.parts)
    parent_parts = tuple(part.casefold() for part in parent.parts)
    return path_parts[: len(parent_parts)] == parent_parts


def safe_destination(destination: Path | str, repo_root: Path | None = None) -> Path:
    """Return a resolved writable destination, rejecting anything under raw.

    Relative destinations are interpreted from ``repo_root``. Absolute paths
    are allowed when outside raw so callers may use temporary test locations.
    """
    root = _canonical(repo_root or repository_root())
    requested = Path(destination)
    resolved = _canonical(requested if requested.is_absolute() else root / requested)
    raw_root = _canonical(root / "data" / "raw")
    if _is_relative_to(resolved, raw_root):
        raise UnsafeWritePathError(f"Write to immutable raw source tree forbidden: {resolved}")
    return resolved


def ensure_parent(destination: Path | str, repo_root: Path | None = None) -> Path:
    resolved = safe_destination(destination, repo_root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def write_json(destination: Path | str, payload: Any, repo_root: Path | None = None) -> Path:
    path = ensure_parent(destination, repo_root)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str, ensure_ascii=False)
    return path


def write_json_replace(destination: Path | str, payload: Any, repo_root: Path | None = None) -> Path:
    path = ensure_parent(destination, repo_root)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str, ensure_ascii=False)
    return path


def append_dataframe_csv(frame, destination: Path | str, repo_root: Path | None = None) -> Path:
    path = ensure_parent(destination, repo_root)
    exists = path.exists()
    frame.to_csv(path, mode="a" if exists else "w", header=not exists, index=False)
    return path


def write_csv_rows(
    destination: Path | str,
    fieldnames: Iterable[str],
    rows: Iterable[Mapping[str, Any]],
    repo_root: Path | None = None,
) -> Path:
    path = ensure_parent(destination, repo_root)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)
    return path

