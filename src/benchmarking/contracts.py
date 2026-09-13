"""Strict, frontend-ready Peer Benchmarking V1 contracts."""
from __future__ import annotations

from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, ConfigDict

POLICY_VERSION = "peer-benchmark-v1.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BenchmarkMode(StrEnum):
    REAL_CURRENT = "REAL_CURRENT"
    REAL_HISTORICAL_AS_OF = "REAL_HISTORICAL_AS_OF"
    SYNTHETIC_SANDBOX = "SYNTHETIC_SANDBOX"


class BenchmarkStatus(StrEnum):
    AVAILABLE = "BENCHMARK_AVAILABLE"
    INSUFFICIENT_PEERS = "BENCHMARK_INSUFFICIENT_PEERS"
    FIELD_UNAVAILABLE = "BENCHMARK_FIELD_UNAVAILABLE"
    SECTOR_UNKNOWN = "BENCHMARK_SECTOR_UNKNOWN"
    DATA_INSUFFICIENT = "BENCHMARK_DATA_INSUFFICIENT"
    SYNTHETIC = "BENCHMARK_SYNTHETIC"


class BenchmarkMetric(StrictModel):
    metric: str
    project_value: float | None
    peer_median: float | None
    peer_mean: float | None
    peer_p25: float | None
    peer_p75: float | None
    percentile: float | None
    peer_count: int
    peer_group_definition: str
    benchmark_status: BenchmarkStatus
    data_origin: Literal["HISTORICAL_FLASH_REPORT", "SYNTHETIC_CUF_PROTOTYPE"]
    directionality: str
    interpretation: str | None


class BenchmarkResult(StrictModel):
    canonical_project_id: str
    as_of_month: str
    mode: BenchmarkMode
    peer_group: dict[str, str]
    peer_group_level: int | None
    peer_count: int
    benchmark_status: BenchmarkStatus
    metrics: list[BenchmarkMetric]
    limitations: list[str]
    data_origin: Literal["HISTORICAL_FLASH_REPORT", "SYNTHETIC_CUF_PROTOTYPE"]
    policy_version: str = POLICY_VERSION
