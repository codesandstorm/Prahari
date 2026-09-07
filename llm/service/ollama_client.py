"""Minimal standard-library client for the local Ollama HTTP API."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class GenerationSettings:
    temperature: float = 0.0
    seed: int = 42
    num_predict: int = 500
    top_p: float = 0.9


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_seconds: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate(self, model: str, system: str, prompt: str, settings: GenerationSettings | None = None) -> dict[str, Any]:
        settings = settings or GenerationSettings()
        requested_at = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        try:
            body = self._post("/api/generate", {"model": model, "system": system, "prompt": prompt, "stream": False, "format": "json", "options": asdict(settings)})
            error = None
        except (OSError, TimeoutError, ValueError, urllib.error.URLError) as exc:
            body = {}
            error = f"{type(exc).__name__}: {exc}"
        latency = time.perf_counter() - started
        completed_at = datetime.now(timezone.utc).isoformat()
        eval_count = body.get("eval_count")
        eval_duration = body.get("eval_duration")
        tokens_per_second = eval_count / (eval_duration / 1e9) if eval_count and eval_duration else None
        raw = body.get("response", "")
        try:
            parsed = json.loads(raw) if raw else None
            parse_error = None if raw else "empty response"
        except json.JSONDecodeError as exc:
            parsed, parse_error = None, str(exc)
        return {
            "model_name": model, "request_timestamp": requested_at, "response_timestamp": completed_at,
            "latency_seconds": latency, "prompt_tokens": body.get("prompt_eval_count"),
            "output_tokens": eval_count, "eval_duration_ns": eval_duration,
            "load_duration_ns": body.get("load_duration"), "tokens_per_second": tokens_per_second,
            "raw_response": raw, "parsed_response": parsed, "parse_error": parse_error, "error": error,
        }

    def list_models(self) -> list[dict[str, Any]]:
        with urllib.request.urlopen(self.base_url + "/api/tags", timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8")).get("models", [])

    def show_model(self, name: str) -> dict[str, Any]:
        return self._post("/api/show", {"name": name, "verbose": True})
