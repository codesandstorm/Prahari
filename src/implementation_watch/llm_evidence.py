"""Lossless, deterministic evidence view for Ask PRAHARI."""
from .contracts import ImplementationWatchResult


def assistant_evidence(watch: ImplementationWatchResult) -> dict:
    return {
        "status": watch.status,
        "as_of": watch.as_of.isoformat(),
        "trend": watch.trend,
        "reason_codes": watch.reason_codes,
        "signals": [
            {
                "code": item.code,
                "family": item.family,
                "status": item.status.value,
                "value": item.value,
                "unit": item.unit,
                "explanation": item.plain_language_explanation,
                "source_refs": item.source_refs,
                "availability": item.availability.value,
                "causal_claim": False,
            }
            for item in watch.signals
        ],
        "unavailable_families": watch.unavailable_families,
        "limitations": watch.data_quality_notes + ["Implementation Watch is deterministic, non-predictive, and non-causal."],
        "policy_version": watch.policy_version,
    }
