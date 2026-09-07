"""Capture local Ollama metadata without downloading anything."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from llm.service import OllamaClient


def capture(output: Path, client: OllamaClient | None = None) -> dict:
    client = client or OllamaClient(); records = []
    for listed in client.list_models():
        name = listed.get("name") or listed.get("model")
        try: shown, error = client.show_model(name), None
        except Exception as exc: shown, error = {}, f"{type(exc).__name__}: {exc}"
        details = shown.get("details", {})
        info = shown.get("model_info", {})
        context_keys = [k for k in info if k.endswith(".context_length")]
        license_lines = [line.strip() for line in (shown.get("license") or "").splitlines() if line.strip()][:3]
        records.append({"name": name, "size_bytes": listed.get("size"), "digest": listed.get("digest"), "modified_at": listed.get("modified_at"), "family": details.get("family") or "UNKNOWN", "parameter_size": details.get("parameter_size") or "UNKNOWN", "quantization": details.get("quantization_level") or "UNKNOWN", "context_length": info.get(context_keys[0]) if context_keys else None, "template": shown.get("template") or "UNKNOWN", "license_reference": " | ".join(license_lines) or "UNKNOWN", "metadata_error": error})
    result = {"captured_at_utc": datetime.now(timezone.utc).isoformat(), "source": "local Ollama API", "models": records}
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=Path("outputs/llm/model_inventory.json")); args = parser.parse_args()
    print(json.dumps(capture(args.output), indent=2))
