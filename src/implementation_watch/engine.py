"""Deterministic evidence-backed Implementation Watch V1 policy engine."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date
from typing import Any

from .contracts import (
    Availability, CufProjectSnapshot, FamilyResult, ImplementationWatchResult,
    SignalState, WatchSignal,
)
from .features import (
    FeatureValue, clearance_metrics, consecutive_stagnant,
    financial_physical_divergence, financial_progress_gap, funding_ratios,
    land_metrics, milestone_metrics, milestone_slippage_trend, physical_progress_gap, row_pending,
    tender_metrics,
)
from .policy import CRITICAL_CLEARANCE_CATEGORIES,HIGH_LAND_REMAINING_PCT,HIGH_REQUIRED_FUTURE_PACE_PP_PER_MONTH,PROLONGED_TENDER_CYCLE_DAYS,SEVERE_MILESTONE_DELAY_DAYS

FAMILIES = ("EXECUTION", "FINANCIAL", "MILESTONE", "LAND", "ROW", "CLEARANCE", "PROCUREMENT", "REPORTING", "DATA_QUALITY")

SIGNAL_META = {
    "PHYSICAL_PROGRESS_BEHIND_PLAN": ("EXECUTION", "MEDIUM"),
    "PHYSICAL_PROGRESS_STAGNANT": ("EXECUTION", "MEDIUM"),
    "HIGH_REQUIRED_FUTURE_PACE": ("EXECUTION", "HIGH"),
    "LOW_PROGRESS_NEAR_DEADLINE": ("EXECUTION", "HIGH"),
    "FINANCIAL_PROGRESS_BEHIND_PLAN": ("FINANCIAL", "MEDIUM"),
    "FINANCIAL_PHYSICAL_DIVERGENCE": ("FINANCIAL", "MEDIUM"),
    "MILESTONE_OVERDUE": ("MILESTONE", "MEDIUM"),
    "MULTIPLE_MILESTONES_OVERDUE": ("MILESTONE", "HIGH"),
    "SEVERE_MILESTONE_SLIPPAGE": ("MILESTONE", "HIGH"),
    "MILESTONE_SLIPPAGE_WORSENING": ("MILESTONE", "MEDIUM"),
    "LAND_ACQUISITION_PENDING": ("LAND", "MEDIUM"),
    "HIGH_LAND_REMAINING": ("LAND", "HIGH"),
    "LAND_DEADLINE_CONFLICT": ("LAND", "HIGH"),
    "ROW_PENDING": ("ROW", "MEDIUM"),
    "CLEARANCE_PENDING": ("CLEARANCE", "MEDIUM"),
    "MULTIPLE_CLEARANCES_PENDING": ("CLEARANCE", "HIGH"),
    "CRITICAL_CLEARANCE_PENDING": ("CLEARANCE", "HIGH"),
    "TENDER_AWARD_PENDING": ("PROCUREMENT", "MEDIUM"),
    "TENDER_CYCLE_PROLONGED": ("PROCUREMENT", "MEDIUM"),
    "MULTIPLE_TENDER_DELAYS": ("PROCUREMENT", "HIGH"),
    "REPORT_STALE": ("REPORTING", "MEDIUM"),
    "REPORT_MONTH_MISSING": ("REPORTING", "HIGH"),
    "SOURCE_GAP": ("REPORTING", "HIGH"),
    "FEATURE_DATA_INCOMPLETE": ("DATA_QUALITY", "MEDIUM"),
    "STRUCTURAL_SCHEMA_LIMITATION": ("DATA_QUALITY", "INFO"),
    "PROVENANCE_INCOMPLETE": ("DATA_QUALITY", "MEDIUM"),
}


def _technical(feature: FeatureValue) -> dict[str, Any]:
    return {"raw_values": feature.inputs, "normalized_value": feature.value, "formula": feature.formula, "threshold_or_policy": feature.inputs.get("threshold_pp") or feature.inputs.get("threshold") or "see formula", "availability": feature.availability.value, "note": feature.note}


def _explanation(code: str, feature: FeatureValue) -> str:
    value = feature.value
    templates = {
        "PHYSICAL_PROGRESS_BEHIND_PLAN": lambda: f"Physical progress is {abs(float(value)):.1f} percentage points behind the scheduled plan." if feature.state==SignalState.DETECTED else "Physical progress is not behind the scheduled plan by the v1 threshold.",
        "PHYSICAL_PROGRESS_STAGNANT": lambda: f"Reported physical progress has not increased across {int(value)} valid consecutive monthly transitions.",
        "HIGH_REQUIRED_FUTURE_PACE": lambda: f"The project requires {float(value):.2f} percentage points of physical progress per remaining month.",
        "LOW_PROGRESS_NEAR_DEADLINE": "Reported physical progress is below 80% with no more than six scheduled months remaining.",
        "FINANCIAL_PROGRESS_BEHIND_PLAN": lambda: f"Financial progress is {abs(float(value)):.1f} percentage points behind the compatible scheduled financial plan." if feature.state==SignalState.DETECTED else "Financial progress is not behind the compatible scheduled plan by the v1 threshold.",
        "FINANCIAL_PHYSICAL_DIVERGENCE": lambda: f"Financial and physical progress differ by {abs(float(value)):.1f} percentage points; this is an attention signal, not a finding of cause or wrongdoing." if feature.state==SignalState.DETECTED else "Financial and physical progress do not diverge by the v1 attention threshold.",
        "MILESTONE_OVERDUE": lambda: f"{int(value)} applicable milestone is overdue or was completed late." if feature.state==SignalState.DETECTED else "No applicable milestone is overdue in the supplied as-of evidence.",
        "MULTIPLE_MILESTONES_OVERDUE": lambda: f"{int(value)} applicable milestones are overdue or were completed late.",
        "SEVERE_MILESTONE_SLIPPAGE": lambda: f"The largest observed milestone delay is {int(value)} days.",
        "MILESTONE_SLIPPAGE_WORSENING": lambda: f"Maximum milestone slippage increased by {int(value)} days across compatible observations.",
        "LAND_ACQUISITION_PENDING": "The structured source reports that land acquisition remains incomplete." if feature.state==SignalState.DETECTED else "The structured source does not report land acquisition as pending.",
        "HIGH_LAND_REMAINING": lambda: f"{float(value):.1f}% of the required land remains to be acquired.",
        "LAND_DEADLINE_CONFLICT": "The reported expected land-completion date is later than the relevant scheduled milestone date.",
        "ROW_PENDING": "The structured source reports right-of-way work as pending." if feature.state==SignalState.DETECTED else "The structured source does not report right-of-way work as pending.",
        "CLEARANCE_PENDING": lambda: f"{int(value)} required clearance remains pending." if feature.state==SignalState.DETECTED else "No applicable clearance is reported pending.",
        "MULTIPLE_CLEARANCES_PENDING": lambda: f"{int(value)} required clearances remain pending.",
        "CRITICAL_CLEARANCE_PENDING": "A pending clearance belongs to a category listed in the versioned critical-clearance policy.",
        "TENDER_AWARD_PENDING": "A published tender has no reported award date." if feature.state==SignalState.DETECTED else "No published applicable tender is awaiting an award in the supplied as-of evidence.",
        "TENDER_CYCLE_PROLONGED": lambda: f"The longest observed tender cycle is {int(value)} days.",
        "MULTIPLE_TENDER_DELAYS": lambda: f"{int(value)} tenders are past their reported expected award date.",
        "REPORT_STALE": "The current project report is marked stale.",
        "REPORT_MONTH_MISSING": "The project-level report for the requested month is unavailable.",
        "SOURCE_GAP": "A source gap prevents a continuous project-level observation sequence.",
        "FEATURE_DATA_INCOMPLETE": "One or more fields required for this signal are unreported or semantically incompatible.",
        "STRUCTURAL_SCHEMA_LIMITATION": "The historical source schema does not contain this structured field family.",
        "PROVENANCE_INCOMPLETE": "The project observation does not have complete source provenance.",
    }
    selected=templates[code]
    return selected() if callable(selected) else selected


def _signal(code: str, feature: FeatureValue, snapshot: CufProjectSnapshot, *, state: SignalState | None = None) -> WatchSignal:
    family, severity = SIGNAL_META[code]
    return WatchSignal(code=code, family=family, status=state or feature.state, severity=severity, value=feature.value, unit="percentage_points" if code in {"PHYSICAL_PROGRESS_BEHIND_PLAN", "FINANCIAL_PROGRESS_BEHIND_PLAN", "FINANCIAL_PHYSICAL_DIVERGENCE"} else "days" if code in {"SEVERE_MILESTONE_SLIPPAGE", "TENDER_CYCLE_PROLONGED"} else None, as_of=snapshot.as_of, plain_language_explanation=_explanation(code, feature), technical_explanation=_technical(feature), source_available=snapshot.source_availability == Availability.AVAILABLE, source_refs=snapshot.source_refs, availability=feature.availability, data_quality_state="SUPPORTED" if feature.availability == Availability.AVAILABLE else feature.availability.value, causal_claim=False)


def _family(name: str, signals: list[WatchSignal]) -> FamilyResult:
    owned = [signal for signal in signals if signal.family == name]
    if not owned:
        return FamilyResult(family=name, availability=Availability.UNKNOWN, status=SignalState.NOT_AVAILABLE, signals=[], evidence=[], limitations=["No governed inputs were evaluated for this family."])
    detected = any(x.status == SignalState.DETECTED for x in owned)
    available = any(x.availability == Availability.AVAILABLE for x in owned)
    if detected: state = SignalState.DETECTED
    elif available: state = SignalState.NOT_DETECTED
    elif any(x.status == SignalState.UNRELIABLE for x in owned): state = SignalState.UNRELIABLE
    else: state = SignalState.NOT_AVAILABLE
    availability = Availability.AVAILABLE if available else owned[0].availability
    return FamilyResult(family=name, availability=availability, status=state, signals=owned, evidence=[{"code": x.code, "value": x.value, "source_refs": x.source_refs} for x in owned], limitations=[] if available else ["Required structured evidence is unavailable; absence is not interpreted as safety."])


def _trust_value(trust: Any, name: str) -> str | None:
    if trust is None: return None
    value = getattr(trust, name, None)
    if value is not None and hasattr(value, "status"): return value.status
    if isinstance(trust, dict):
        value = trust.get(name)
        if isinstance(value, dict): return value.get("status")
    return None


def derive_trend(current: ImplementationWatchResult, previous: ImplementationWatchResult | None) -> str:
    if previous is None: return "NEW" if current.status in {"WATCH", "ELEVATED"} else "NOT_AVAILABLE"
    rank = {"CLEAR": 0, "WATCH": 1, "ELEVATED": 2}
    if current.status not in rank or previous.status not in rank: return "NOT_AVAILABLE"
    if rank[current.status] > rank[previous.status]: return "WORSENING"
    if rank[current.status] < rank[previous.status]: return "RESOLVED" if current.status == "CLEAR" else "IMPROVING"
    return "PERSISTENT"


class ImplementationWatchEngine:
    """Evaluate current structured evidence; never infer causes or probabilities."""

    def evaluate(self, snapshot: CufProjectSnapshot, *, progress_history: list[tuple[str, float | None, Availability]] | None = None, data_trust: Any = None, previous: ImplementationWatchResult | None = None) -> ImplementationWatchResult:
        signals: list[WatchSignal] = []
        physical = physical_progress_gap(snapshot.actual_physical_progress, snapshot.scheduled_physical_progress)
        if physical.availability == Availability.AVAILABLE: signals.append(_signal("PHYSICAL_PROGRESS_BEHIND_PLAN", physical, snapshot))
        stagnation = consecutive_stagnant(progress_history or [])
        if stagnation.state == SignalState.DETECTED: signals.append(_signal("PHYSICAL_PROGRESS_STAGNANT", stagnation, snapshot))
        if snapshot.required_future_velocity is not None and snapshot.required_future_velocity >= HIGH_REQUIRED_FUTURE_PACE_PP_PER_MONTH:
            fv = FeatureValue(snapshot.required_future_velocity, Availability.AVAILABLE, SignalState.DETECTED, "existing compact-v2.1-calendar-safe required_future_velocity; threshold from policy", {"required_future_velocity": snapshot.required_future_velocity, "threshold": HIGH_REQUIRED_FUTURE_PACE_PP_PER_MONTH})
            signals.append(_signal("HIGH_REQUIRED_FUTURE_PACE", fv, snapshot))
        if snapshot.low_progress_near_deadline is True:
            fv = FeatureValue(True, Availability.AVAILABLE, SignalState.DETECTED, "physical_progress < 80 and remaining_schedule_months <= 6", {"physical_progress": snapshot.actual_physical_progress, "remaining_schedule_months": snapshot.remaining_schedule_months})
            signals.append(_signal("LOW_PROGRESS_NEAR_DEADLINE", fv, snapshot))

        fg = financial_progress_gap(snapshot.actual_financial_progress, snapshot.scheduled_financial_progress, semantics_compatible=snapshot.financial_progress_semantics_compatible)
        if fg.availability == Availability.AVAILABLE: signals.append(_signal("FINANCIAL_PROGRESS_BEHIND_PLAN", fg, snapshot))
        divergence = financial_physical_divergence(snapshot.actual_financial_progress, snapshot.actual_physical_progress, semantics_compatible=snapshot.financial_progress_semantics_compatible)
        if divergence.availability == Availability.AVAILABLE: signals.append(_signal("FINANCIAL_PHYSICAL_DIVERGENCE", divergence, snapshot))

        milestones = milestone_metrics(snapshot.milestones, snapshot.as_of)
        if milestones["delayed_count"].state == SignalState.DETECTED:
            code = "MULTIPLE_MILESTONES_OVERDUE" if int(milestones["delayed_count"].value or 0) >= 2 else "MILESTONE_OVERDUE"
            signals.append(_signal(code, milestones["delayed_count"], snapshot))
        elif milestones["delayed_count"].availability == Availability.AVAILABLE:
            signals.append(_signal("MILESTONE_OVERDUE", milestones["delayed_count"], snapshot))
        if milestones["max_delay_days"].value is not None and float(milestones["max_delay_days"].value) >= SEVERE_MILESTONE_DELAY_DAYS:
            signals.append(_signal("SEVERE_MILESTONE_SLIPPAGE", milestones["max_delay_days"], snapshot))
        elif milestones["max_delay_days"].availability == Availability.AVAILABLE:
            signals.append(_signal("SEVERE_MILESTONE_SLIPPAGE", milestones["max_delay_days"], snapshot))
        if previous is not None and milestones["max_delay_days"].availability == Availability.AVAILABLE:
            prior=next((x.value for x in previous.signals if x.code=="SEVERE_MILESTONE_SLIPPAGE" and x.availability==Availability.AVAILABLE),None)
            trend_feature=milestone_slippage_trend(float(milestones["max_delay_days"].value),float(prior) if prior is not None else None,observations_compatible=True)
            if trend_feature.state==SignalState.DETECTED:signals.append(_signal("MILESTONE_SLIPPAGE_WORSENING",trend_feature,snapshot))

        relevant_due = min((x.scheduled_finish_revised or x.scheduled_finish_original or x.revised_date or x.planned_date for x in snapshot.milestones or [] if (x.scheduled_finish_revised or x.scheduled_finish_original or x.revised_date or x.planned_date)), default=None)
        land = land_metrics(snapshot.land, snapshot.as_of, relevant_due)
        if land["pending"].state == SignalState.DETECTED: signals.append(_signal("LAND_ACQUISITION_PENDING", land["pending"], snapshot))
        if land["remaining_pct"].value is not None and float(land["remaining_pct"].value) >= HIGH_LAND_REMAINING_PCT: signals.append(_signal("HIGH_LAND_REMAINING", land["remaining_pct"], snapshot))
        if land["deadline_conflict"].state == SignalState.DETECTED: signals.append(_signal("LAND_DEADLINE_CONFLICT", land["deadline_conflict"], snapshot))
        if land["pending"].availability == Availability.AVAILABLE and land["pending"].state == SignalState.NOT_DETECTED: signals.append(_signal("LAND_ACQUISITION_PENDING", land["pending"], snapshot))

        row = row_pending(snapshot.right_of_way)
        if row.state == SignalState.DETECTED: signals.append(_signal("ROW_PENDING", row, snapshot))
        elif row.availability == Availability.AVAILABLE: signals.append(_signal("ROW_PENDING", row, snapshot))
        clearances = clearance_metrics(snapshot.clearances, CRITICAL_CLEARANCE_CATEGORIES)
        if clearances["pending_count"].state == SignalState.DETECTED:
            code = "MULTIPLE_CLEARANCES_PENDING" if int(clearances["pending_count"].value or 0) >= 2 else "CLEARANCE_PENDING"
            signals.append(_signal(code, clearances["pending_count"], snapshot))
        elif clearances["pending_count"].availability == Availability.AVAILABLE:
            signals.append(_signal("CLEARANCE_PENDING", clearances["pending_count"], snapshot))
        if clearances["critical_pending"].state == SignalState.DETECTED: signals.append(_signal("CRITICAL_CLEARANCE_PENDING", clearances["critical_pending"], snapshot))

        tenders = tender_metrics(snapshot.tenders, snapshot.as_of,PROLONGED_TENDER_CYCLE_DAYS)
        if snapshot.has_active_tenders is not None:
            tenders["active"]=FeatureValue(snapshot.has_active_tenders,Availability.AVAILABLE,SignalState.DETECTED if snapshot.has_active_tenders else SignalState.NOT_DETECTED,"official CUF has_active_tenders flag",{"has_active_tenders":snapshot.has_active_tenders})
        if tenders["active"].state == SignalState.DETECTED: signals.append(_signal("TENDER_AWARD_PENDING", tenders["active"], snapshot))
        elif tenders["active"].availability == Availability.AVAILABLE: signals.append(_signal("TENDER_AWARD_PENDING", tenders["active"], snapshot))
        if tenders["cycle_days"].state == SignalState.DETECTED: signals.append(_signal("TENDER_CYCLE_PROLONGED", tenders["cycle_days"], snapshot))
        if tenders["delay_count"].value is not None and int(tenders["delay_count"].value) >= 2: signals.append(_signal("MULTIPLE_TENDER_DELAYS", tenders["delay_count"], snapshot))

        if snapshot.report_stale is True:
            signals.append(_signal("REPORT_STALE", FeatureValue(True, Availability.AVAILABLE, SignalState.DETECTED, "report_stale = true", {}), snapshot))
        if snapshot.report_month_missing:
            signals.append(_signal("REPORT_MONTH_MISSING", FeatureValue(True, Availability.SOURCE_GAP, SignalState.DETECTED, "report_month_missing = true", {}), snapshot))
        if snapshot.source_availability == Availability.SOURCE_GAP:
            signals.append(_signal("SOURCE_GAP", FeatureValue(True, Availability.SOURCE_GAP, SignalState.DETECTED, "source_availability = SOURCE_GAP", {}), snapshot))
        if snapshot.provenance_complete is False:
            signals.append(_signal("PROVENANCE_INCOMPLETE", FeatureValue(True, Availability.UNREPORTED, SignalState.DETECTED, "provenance_complete = false", {}), snapshot))

        structural = [name for name, value in (("MILESTONE", snapshot.milestones), ("LAND", snapshot.land), ("ROW", snapshot.right_of_way), ("CLEARANCE", snapshot.clearances), ("PROCUREMENT", snapshot.tenders)) if value is None]
        if structural:
            feature = FeatureValue(",".join(structural), Availability.STRUCTURALLY_UNAVAILABLE, SignalState.DETECTED, "structured families absent from source schema", {"families": structural})
            signals.append(_signal("STRUCTURAL_SCHEMA_LIMITATION", feature, snapshot))

        source_failed = _trust_value(data_trust, "source") == "FAIL"
        provenance_failed = _trust_value(data_trust, "provenance") in {"FAIL", "UNKNOWN"}
        if source_failed:
            signals = [signal.model_copy(update={"status": SignalState.UNRELIABLE, "data_quality_state": "SOURCE_TRUST_FAIL"}) if signal.family not in {"REPORTING", "DATA_QUALITY"} else signal for signal in signals]
        if provenance_failed and not any(x.code == "PROVENANCE_INCOMPLETE" for x in signals):
            signals.append(_signal("PROVENANCE_INCOMPLETE", FeatureValue(True, Availability.UNREPORTED, SignalState.DETECTED, "Data Trust provenance FAIL/UNKNOWN", {}), snapshot))

        families = [_family(name, signals) for name in FAMILIES]
        detected_operational = [x for x in signals if x.status == SignalState.DETECTED and x.family not in {"REPORTING", "DATA_QUALITY"}]
        high = sum(x.severity == "HIGH" for x in detected_operational)
        if source_failed: status = "DATA_INSUFFICIENT"
        elif high or len(detected_operational) >= 3: status = "ELEVATED"
        elif detected_operational: status = "WATCH"
        elif any(f.availability == Availability.AVAILABLE for f in families if f.family not in {"REPORTING", "DATA_QUALITY"}): status = "CLEAR"
        else: status = "DATA_INSUFFICIENT"
        result = ImplementationWatchResult(status=status, as_of=snapshot.as_of, trend="NOT_AVAILABLE", reason_codes=list(dict.fromkeys(x.code for x in signals if x.status in {SignalState.DETECTED, SignalState.UNRELIABLE})), signals=signals, families=families, unavailable_families=[f.family for f in families if f.availability in {Availability.STRUCTURALLY_UNAVAILABLE, Availability.UNREPORTED, Availability.UNKNOWN}], data_quality_notes=[x.plain_language_explanation for x in signals if x.family in {"REPORTING", "DATA_QUALITY"}], data_origin=snapshot.data_origin)
        return result.model_copy(update={"trend": derive_trend(result, previous)})
