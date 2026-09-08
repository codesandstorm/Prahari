"""Conservative deterministic checks; not a substitute for human review."""

from __future__ import annotations

import json
import re
from typing import Any

from llm.schemas import BenchmarkCase, PrahariResponse


def _text(parsed: dict[str, Any] | None, raw: str) -> str:
    return json.dumps(parsed, ensure_ascii=False) if parsed is not None else raw


def evaluate(case: BenchmarkCase, raw: str, parsed: dict[str, Any] | None) -> list[dict[str, Any]]:
    text = _text(parsed, raw).lower()
    results = []
    for check in case.automatic_checks:
        kind = check["type"]
        passed, detail = False, ""
        if kind == "JSON_VALID":
            try:
                PrahariResponse.from_dict(parsed or {})
                passed, detail = True, "response schema valid"
            except ValueError as exc:
                detail = str(exc)
        elif kind == "FORBIDDEN_TERM_ABSENT":
            terms = [x.lower() for x in check.get("terms", case.forbidden_claims)]
            found = [x for x in terms if x in text]
            passed, detail = not found, f"found={found}"
        elif kind == "REQUIRED_CONCEPT_PRESENT":
            concepts = [x.lower() for x in check.get("concepts", case.required_concepts)]
            missing = [x for x in concepts if x not in text]
            passed, detail = not missing, f"missing={missing}"
        elif kind == "REQUIRED_ANY_CONCEPT_PRESENT":
            concepts = [x.lower() for x in check.get("concepts", [])]
            found = [x for x in concepts if x in text]
            passed, detail = bool(found), f"found={found}"
        elif kind == "UNSUPPORTED_ENTITY_ABSENT":
            entities = [x.lower() for x in check.get("entities", [])]
            found = [x for x in entities if x in text]
            passed, detail = not found, f"found={found}"
        elif kind == "NO_NUMERIC_PROBABILITY_IF_NULL":
            percentages = re.findall(r"\b(?:100|\d{1,2})(?:\.\d+)?\s*%", text)
            passed, detail = case.evidence.calibrated_probability is not None or not percentages, f"percentages={percentages}"
        elif kind == "PROVENANCE_MATCH":
            expected = [str(x).lower() for x in check.get("values", [])]
            missing = [x for x in expected if x not in text]
            passed, detail = not missing, f"missing={missing}"
        elif kind == "ABSTENTION_ACKNOWLEDGED":
            passed = any(term in text for term in ("withheld", "abstain", "unavailable", "cannot provide"))
            detail = "requires explicit unavailability/withholding"
        elif kind == "RELIABILITY_RISK_DISTINCTION":
            passed = "reliability" in text and "risk" in text and any(x in text for x in ("different", "distinct", "does not mean", "not the same"))
            detail = "requires explicit risk/reliability distinction"
        elif kind == "NO_CAUSAL_LANGUAGE":
            prohibited = ("caused by", "the cause is", "responsible for the delay", "led to the delay")
            found = [x for x in prohibited if x in text]
            passed, detail = not found, f"found={found}"
        elif kind == "NO_MISCONDUCT_CLAIM":
            prohibited = ("is corrupt", "committed fraud", "is fraudulent", "guilty of", "negligent")
            found = [x for x in prohibited if x in text]
            passed, detail = not found, f"found={found}"
        else:
            detail = f"unknown check: {kind}"
        results.append({"check": kind, "passed": passed, "detail": detail})
    return results
