"""Narrow adapter from Watch evidence to Officer Decision inputs.

This does not create alerts and does not replace the governed decision policy.
"""
from .contracts import ImplementationWatchResult


def officer_reason_codes(watch: ImplementationWatchResult) -> list[str]:
    reasons = []
    if watch.status in {"WATCH", "ELEVATED"}:
        reasons.append("IMPLEMENTATION_PRESSURE_SIGNAL")
    if any(signal.family in {"REPORTING", "DATA_QUALITY"} and signal.status.value == "DETECTED" for signal in watch.signals):
        reasons.append("DATA_VERIFICATION_REQUIRED")
    return reasons

