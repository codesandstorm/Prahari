"""Pure, deterministic CUF feature calculations with explicit availability."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any

from .contracts import Availability, Clearance, LandStatus, Milestone, RowStatus, SignalState, Tender


@dataclass(frozen=True)
class FeatureValue:
    value: float | int | bool | None
    availability: Availability
    state: SignalState
    formula: str
    inputs: dict[str, Any]
    note: str = ""


def _missing(*values: object) -> bool:
    return any(value is None for value in values)


def physical_progress_gap(actual: float | None, scheduled: float | None, *, threshold_pp: float = -10.0) -> FeatureValue:
    if _missing(actual, scheduled):
        return FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "actual_physical_progress - scheduled_physical_progress", {"actual": actual, "scheduled": scheduled})
    gap = float(actual) - float(scheduled)
    return FeatureValue(gap, Availability.AVAILABLE, SignalState.DETECTED if gap <= threshold_pp else SignalState.NOT_DETECTED, "actual_physical_progress - scheduled_physical_progress", {"actual": actual, "scheduled": scheduled, "threshold_pp": threshold_pp})


def financial_progress_gap(actual: float | None, scheduled: float | None, *, semantics_compatible: bool | None, threshold_pp: float = -10.0) -> FeatureValue:
    if semantics_compatible is False:
        return FeatureValue(None, Availability.UNKNOWN, SignalState.DATA_INSUFFICIENT, "actual_financial_progress - scheduled_financial_progress", {"actual": actual, "scheduled": scheduled}, "SEMANTIC_MISMATCH")
    if semantics_compatible is not True or _missing(actual, scheduled):
        return FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "actual_financial_progress - scheduled_financial_progress", {"actual": actual, "scheduled": scheduled}, "Compatible cumulative percentage semantics are required")
    gap = float(actual) - float(scheduled)
    return FeatureValue(gap, Availability.AVAILABLE, SignalState.DETECTED if gap <= threshold_pp else SignalState.NOT_DETECTED, "actual_financial_progress - scheduled_financial_progress", {"actual": actual, "scheduled": scheduled, "threshold_pp": threshold_pp})


def financial_physical_divergence(financial: float | None, physical: float | None, *, semantics_compatible: bool | None, threshold_pp: float = 15.0) -> FeatureValue:
    if semantics_compatible is False:
        return FeatureValue(None, Availability.UNKNOWN, SignalState.DATA_INSUFFICIENT, "actual_financial_progress - actual_physical_progress", {"financial": financial, "physical": physical}, "SEMANTIC_MISMATCH")
    if semantics_compatible is not True or _missing(financial, physical):
        return FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "actual_financial_progress - actual_physical_progress", {"financial": financial, "physical": physical})
    gap = float(financial) - float(physical)
    return FeatureValue(gap, Availability.AVAILABLE, SignalState.DETECTED if abs(gap) >= threshold_pp else SignalState.NOT_DETECTED, "actual_financial_progress - actual_physical_progress", {"financial": financial, "physical": physical, "absolute_threshold_pp": threshold_pp})


def consecutive_stagnant(history: list[tuple[str, float | None, Availability]]) -> FeatureValue:
    """Count trailing unchanged/decreasing progress across consecutive calendar months.

    `history` must be ordered or orderable by YYYY-MM. Any unavailable value or
    calendar discontinuity breaks the sequence rather than becoming stagnation.
    """
    valid = sorted(history, key=lambda item: item[0])
    if len(valid) < 2:
        return FeatureValue(None, Availability.UNREPORTED, SignalState.DATA_INSUFFICIENT, "trailing consecutive month-to-month deltas <= 0", {"observations": len(valid)})
    count = 0
    for idx in range(len(valid) - 1, 0, -1):
        month, current, availability = valid[idx]
        previous_month, previous, previous_availability = valid[idx - 1]
        cy, cm = map(int, month.split("-")); py, pm = map(int, previous_month.split("-"))
        if (cy * 12 + cm) - (py * 12 + pm) != 1:
            break
        if availability != Availability.AVAILABLE or previous_availability != Availability.AVAILABLE or _missing(current, previous):
            break
        if float(current) - float(previous) <= 0:
            count += 1
        else:
            break
    return FeatureValue(count, Availability.AVAILABLE, SignalState.DETECTED if count >= 2 else SignalState.NOT_DETECTED, "trailing consecutive calendar-month deltas <= 0; threshold=2", {"observations": len(valid), "threshold": 2})


def milestone_metrics(items: list[Milestone] | None, as_of: date) -> dict[str, FeatureValue]:
    if items is None:
        unavailable = FeatureValue(None, Availability.STRUCTURALLY_UNAVAILABLE, SignalState.NOT_AVAILABLE, "structured milestone dates", {})
        return {key: unavailable for key in ("delayed_count", "max_delay_days", "slippage_rate")}
    if not items:
        unreported = FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "structured milestone dates", {})
        return {key: unreported for key in ("delayed_count", "max_delay_days", "slippage_rate")}
    applicable = [item for item in items if item.applicable is not False]
    if not applicable:
        na = FeatureValue(None, Availability.NOT_APPLICABLE, SignalState.NOT_APPLICABLE, "applicable milestones", {})
        return {key: na for key in ("delayed_count", "max_delay_days", "slippage_rate")}
    delays = []
    for item in applicable:
        due = item.scheduled_finish_revised or item.scheduled_finish_original or item.revised_date or item.planned_date
        candidate_actual=item.actual_finish or item.actual_date
        actual = candidate_actual if candidate_actual and candidate_actual <= as_of else None
        if due and not actual and due < as_of:
            delays.append((as_of - due).days)
        elif due and actual and actual > due:
            delays.append((actual - due).days)
    count = len(delays)
    common = {"applicable": len(applicable), "delays": delays}
    return {
        "delayed_count": FeatureValue(count, Availability.AVAILABLE, SignalState.DETECTED if count else SignalState.NOT_DETECTED, "count(applicable overdue or completed-late milestones)", common),
        "max_delay_days": FeatureValue(max(delays, default=0), Availability.AVAILABLE, SignalState.DETECTED if delays else SignalState.NOT_DETECTED, "max(milestone delay days)", common),
        "slippage_rate": FeatureValue(100 * count / len(applicable), Availability.AVAILABLE, SignalState.DETECTED if count else SignalState.NOT_DETECTED, "100 * delayed / applicable milestones", common),
    }


def milestone_slippage_trend(current_delay_days: float | None, previous_delay_days: float | None, *, observations_compatible: bool, source_gap: bool = False) -> FeatureValue:
    if source_gap:
        return FeatureValue(None, Availability.SOURCE_GAP, SignalState.DATA_INSUFFICIENT, "current max milestone delay - prior comparable max delay", {"current": current_delay_days,"previous": previous_delay_days}, "A source gap breaks trend")
    if not observations_compatible:
        return FeatureValue(None, Availability.UNKNOWN, SignalState.DATA_INSUFFICIENT, "current max milestone delay - prior comparable max delay", {"current": current_delay_days,"previous": previous_delay_days}, "Incompatible milestone schemas")
    if current_delay_days is None or previous_delay_days is None:
        return FeatureValue(None, Availability.UNREPORTED, SignalState.DATA_INSUFFICIENT, "current max milestone delay - prior comparable max delay", {"current": current_delay_days,"previous": previous_delay_days})
    change=float(current_delay_days)-float(previous_delay_days)
    return FeatureValue(change,Availability.AVAILABLE,SignalState.DETECTED if change>0 else SignalState.NOT_DETECTED,"current max milestone delay - prior comparable max delay",{"current":current_delay_days,"previous":previous_delay_days})


def land_metrics(land: LandStatus | None, as_of: date, relevant_due: date | None = None) -> dict[str, FeatureValue]:
    if land is None:
        u = FeatureValue(None, Availability.STRUCTURALLY_UNAVAILABLE, SignalState.NOT_AVAILABLE, "structured land status", {})
        return {key: u for key in ("remaining_pct", "pending", "deadline_conflict")}
    if land.applicable is False:
        na = FeatureValue(None, Availability.NOT_APPLICABLE, SignalState.NOT_APPLICABLE, "land applicable", {})
        return {key: na for key in ("remaining_pct", "pending", "deadline_conflict")}
    remaining = land.remaining_pct
    if remaining is None and land.required and land.acquired is not None:
        remaining = 100 * (land.required - land.acquired) / land.required
    rav = Availability.AVAILABLE if remaining is not None else Availability.UNREPORTED
    pending = (land.acquisition_complete is False) if land.acquisition_complete is not None else (remaining > 0 if remaining is not None else None)
    conflict = bool(pending and land.expected_completion_date and relevant_due and land.expected_completion_date > relevant_due)
    return {
        "remaining_pct": FeatureValue(remaining, rav, SignalState.DETECTED if remaining is not None and remaining >= 20 else SignalState.NOT_DETECTED if remaining is not None else SignalState.NOT_AVAILABLE, "100 * (required - acquired) / required, or source-confirmed remaining_pct", {"required": land.required, "acquired": land.acquired, "reported_remaining_pct": land.remaining_pct}),
        "pending": FeatureValue(pending, Availability.AVAILABLE if pending is not None else Availability.UNREPORTED, SignalState.DETECTED if pending else SignalState.NOT_DETECTED if pending is not None else SignalState.NOT_AVAILABLE, "explicit incomplete status or confirmed remaining_pct > 0", {"acquisition_complete": land.acquisition_complete, "remaining_pct": remaining}),
        "deadline_conflict": FeatureValue(conflict if pending is not None and land.expected_completion_date and relevant_due else None, Availability.AVAILABLE if pending is not None and land.expected_completion_date and relevant_due else Availability.UNREPORTED, SignalState.DETECTED if conflict else SignalState.NOT_DETECTED if pending is not None and land.expected_completion_date and relevant_due else SignalState.NOT_AVAILABLE, "pending and expected land completion > relevant due date", {"expected_completion_date": land.expected_completion_date, "relevant_due": relevant_due}),
    }


def row_pending(row: RowStatus | None) -> FeatureValue:
    if row is None:
        return FeatureValue(None, Availability.STRUCTURALLY_UNAVAILABLE, SignalState.NOT_AVAILABLE, "explicit ROW applicability and pending status", {})
    if row.applicable is False:
        return FeatureValue(None, Availability.NOT_APPLICABLE, SignalState.NOT_APPLICABLE, "ROW applicable", {})
    pending=row.pending if row.pending is not None else (row.availability_pct < 100 if row.availability_pct is not None else None)
    if pending is None:
        return FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "explicit ROW pending status", {"applicable": row.applicable})
    return FeatureValue(pending, Availability.AVAILABLE, SignalState.DETECTED if pending else SignalState.NOT_DETECTED, "explicit pending status, or confirmed ROW availability below 100%", {"pending": row.pending,"availability_pct":row.availability_pct})


def clearance_metrics(items: list[Clearance] | None, critical_categories: frozenset[str]) -> dict[str, FeatureValue]:
    if items is None:
        u = FeatureValue(None, Availability.STRUCTURALLY_UNAVAILABLE, SignalState.NOT_AVAILABLE, "structured clearance records", {})
        return {"pending_count": u, "critical_pending": u}
    if not items:
        u = FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "structured clearance records", {})
        return {"pending_count": u, "critical_pending": u}
    applicable = [item for item in items if item.applicable is not False]
    if not applicable:
        na = FeatureValue(None, Availability.NOT_APPLICABLE, SignalState.NOT_APPLICABLE, "applicable clearances", {})
        return {"pending_count": na, "critical_pending": na}
    pending = [item for item in applicable if item.status == "PENDING"]
    critical = any(item.category.strip().upper() in critical_categories for item in pending)
    return {
        "pending_count": FeatureValue(len(pending), Availability.AVAILABLE, SignalState.DETECTED if pending else SignalState.NOT_DETECTED, "count(status=PENDING and applicable)", {"categories": [x.category for x in pending]}),
        "critical_pending": FeatureValue(critical, Availability.AVAILABLE, SignalState.DETECTED if critical else SignalState.NOT_DETECTED, "pending category in versioned critical-category policy", {"critical_categories": sorted(critical_categories), "pending_categories": [x.category for x in pending]}),
    }


def tender_metrics(items: list[Tender] | None, as_of: date, prolonged_days: int = 120) -> dict[str, FeatureValue]:
    if items is None:
        u = FeatureValue(None, Availability.STRUCTURALLY_UNAVAILABLE, SignalState.NOT_AVAILABLE, "structured tender records", {})
        return {key: u for key in ("active", "cycle_days", "delay_count")}
    if not items:
        u = FeatureValue(None, Availability.UNREPORTED, SignalState.NOT_AVAILABLE, "structured tender records", {})
        return {key: u for key in ("active", "cycle_days", "delay_count")}
    applicable = [item for item in items if item.applicable is not False]
    if not applicable:
        na = FeatureValue(None, Availability.NOT_APPLICABLE, SignalState.NOT_APPLICABLE, "applicable tenders", {})
        return {key: na for key in ("active", "cycle_days", "delay_count")}
    effective_award = lambda item: item.award_date if item.award_date and item.award_date <= as_of else None
    active = [item for item in applicable if item.publish_date and item.publish_date <= as_of and not effective_award(item)]
    cycles = [((effective_award(item) or as_of) - item.publish_date).days for item in applicable if item.publish_date and item.publish_date <= as_of]
    delayed = [item for item in active if item.expected_award_date and item.expected_award_date < as_of]
    return {
        "active": FeatureValue(bool(active), Availability.AVAILABLE, SignalState.DETECTED if active else SignalState.NOT_DETECTED, "published and not awarded", {"active_count": len(active)}),
        "cycle_days": FeatureValue(max(cycles) if cycles else None, Availability.AVAILABLE if cycles else Availability.UNREPORTED, SignalState.DETECTED if cycles and max(cycles) >= prolonged_days else SignalState.NOT_DETECTED if cycles else SignalState.NOT_AVAILABLE, "days from publication to award, or as_of for active tender", {"cycles": cycles, "threshold_days": prolonged_days}),
        "delay_count": FeatureValue(len(delayed), Availability.AVAILABLE, SignalState.DETECTED if delayed else SignalState.NOT_DETECTED, "count(active and expected_award_date < as_of)", {"count": len(delayed)}),
    }


def funding_ratios(total: float | None, **parts: float | None) -> dict[str, FeatureValue]:
    output = {}
    for name, value in parts.items():
        available = total is not None and total > 0 and value is not None and isfinite(value)
        output[name] = FeatureValue(value / total if available else None, Availability.AVAILABLE if available else Availability.UNREPORTED, SignalState.NOT_DETECTED if available else SignalState.NOT_AVAILABLE, f"{name} / total_funding", {name: value, "total_funding": total}, "Context only; not a Watch trigger")
    return output
