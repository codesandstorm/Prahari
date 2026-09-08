from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    api_prefix: str
    log_level: str
    cors_origins: tuple[str, ...]
    llm_enabled: bool
    rag_index_dir: Path
    processed_data_dir: Path


@lru_cache
def get_settings() -> Settings:
    origins = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if x.strip())
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", f"sqlite:///{(ROOT / 'data' / 'prahari.db').as_posix()}"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        cors_origins=origins,
        llm_enabled=os.getenv("LLM_ENABLED", "true").lower() in {"1", "true", "yes"},
        rag_index_dir=Path(os.getenv("RAG_INDEX_DIR", ROOT / "outputs/llm/rag/index/rag-v1-src-2026-06-frontmatter-p1-21")),
        processed_data_dir=Path(os.getenv("PROCESSED_DATA_DIR", ROOT / "data/processed/longitudinal_2023_07_2026_06_mixed")),
    )
