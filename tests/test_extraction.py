from pathlib import Path

from src.extraction.pdf_inspector import compute_sha256
from src.extraction.schema_detector import detect_schema


def test_sha256_is_deterministic(tmp_path):
    path = tmp_path / "source.bin"
    path.write_bytes(b"deterministic")
    assert compute_sha256(path) == compute_sha256(path)
    assert len(compute_sha256(path)) == 64


def test_unknown_schema_for_unrelated_text():
    result = detect_schema(
        Path("unused.pdf"),
        {"schema_versions": {}},
        _extract_fn=lambda path, limit: [(1, "unrelated text")],
    )
    assert result.detected_schema == "UNKNOWN_SCHEMA"

