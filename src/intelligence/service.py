"""Composition-only Unified Project Intelligence V1 service.

It reuses authoritative subsystem outputs and never creates a composite risk
score, prediction probability, causal conclusion, or competing officer policy.
"""
from __future__ import annotations
from typing import Any

from .contracts import IntelligenceMode, ProjectIntelligence


def attention_trend(current_watch: dict, previous_watch: dict | None = None, trust_changed: bool | None = None) -> dict:
    declared=current_watch.get("trend")
    mapping={"WORSENING":"WORSENING","IMPROVING":"IMPROVING","RESOLVED":"IMPROVING","PERSISTENT":"STABLE"}
    if current_watch.get("status")=="DATA_INSUFFICIENT" or (previous_watch and previous_watch.get("status")=="DATA_INSUFFICIENT"): state="INSUFFICIENT_HISTORY"
    elif declared in mapping: state=mapping[declared]
    elif previous_watch is None: state="INSUFFICIENT_HISTORY"
    else:
        rank={"CLEAR":0,"WATCH":1,"ELEVATED":2}
        before,after=rank.get(previous_watch.get("status")),rank.get(current_watch.get("status"))
        state="INSUFFICIENT_HISTORY" if before is None or after is None else "WORSENING" if after>before else "IMPROVING" if after<before else "STABLE"
    if trust_changed and state=="STABLE": state="MIXED"
    return {"state":state,"basis":["IMPLEMENTATION_WATCH_HISTORY"] + (["DATA_TRUST_CHANGE"] if trust_changed else []),"prediction_trajectory_used":False}


def _actions(watch: dict, decision: dict) -> list[dict]:
    codes=set(watch.get("reason_codes",[])); actions=[]
    mapping=[
        ({"PHYSICAL_PROGRESS_STAGNANT"},"Review recent physical-progress stagnation."),
        ({"HIGH_REQUIRED_FUTURE_PACE","LOW_PROGRESS_NEAR_DEADLINE","PHYSICAL_PROGRESS_BEHIND_PLAN"},"Review the current deterministic schedule-pressure evidence."),
        ({"REPORT_STALE","REPORT_MONTH_MISSING","SOURCE_GAP","PROVENANCE_INCOMPLETE"},"Verify missing, stale, or incomplete reporting evidence."),
        ({"MILESTONE_OVERDUE","MULTIPLE_MILESTONES_OVERDUE","SEVERE_MILESTONE_SLIPPAGE"},"Review overdue milestone evidence."),
        ({"LAND_ACQUISITION_PENDING","HIGH_LAND_REMAINING","LAND_DEADLINE_CONFLICT"},"Check the structured land-acquisition evidence."),
        ({"CLEARANCE_PENDING","MULTIPLE_CLEARANCES_PENDING","CRITICAL_CLEARANCE_PENDING"},"Check pending clearance status and evidence."),
        ({"ROW_PENDING"},"Check the structured right-of-way evidence."),
        ({"TENDER_AWARD_PENDING","TENDER_CYCLE_PROLONGED","MULTIPLE_TENDER_DELAYS"},"Review the structured tender-cycle evidence."),
    ]
    for match,text in mapping:
        if codes & match: actions.append({"action":text,"basis_codes":sorted(codes & match),"action_type":"REVIEW_OR_VERIFY"})
    if not actions and decision.get("recommended_action"):
        actions.append({"action":decision["recommended_action"],"basis_codes":decision.get("reason_codes",[]),"action_type":"MONITOR_OR_REVIEW"})
    return actions


def build_project_intelligence(*, mode: IntelligenceMode, identity: dict, current_state: dict, watch: dict, trust: dict, benchmark: dict, officer_decision: dict, evidence: list[dict], provenance: dict, previous_watch: dict | None = None) -> ProjectIntelligence:
    origin="SYNTHETIC_CUF_PROTOTYPE" if mode==IntelligenceMode.SYNTHETIC_SANDBOX else "HISTORICAL_FLASH_REPORT"
    schedule={"prediction_status":"WITHHELD","probability":None,"risk_band":None,"research_status":"SCHEDULE_PREDICTION_FINAL_V3_PARTIAL","reason_code":"INSUFFICIENT_TEMPORAL_VALIDATION","deterministic_schedule_pressure":{"status":watch.get("status"),"reason_codes":[x for x in watch.get("reason_codes",[]) if x in {"PHYSICAL_PROGRESS_BEHIND_PLAN","PHYSICAL_PROGRESS_STAGNANT","HIGH_REQUIRED_FUTURE_PACE","LOW_PROGRESS_NEAR_DEADLINE","MILESTONE_OVERDUE","MULTIPLE_MILESTONES_OVERDUE","SEVERE_MILESTONE_SLIPPAGE"}]}}
    cost={"prediction_status":"WITHHELD","probability":None,"risk_band":None,"research_status":"COST_PREDICTION_V3_PARTIAL","reason_code":"NO_COST_MODEL_ADMITTED","factual_cost_state":{k:current_state.get(k) for k in ("original_cost","current_cost","cost_escalation_pct","cumulative_expenditure")}}
    reliability={"prediction_reliability":"NOT_APPLICABLE","data_quality":trust.get("data_status") or trust.get("summary_state","UNKNOWN"),"history_sufficiency":trust.get("history","UNKNOWN"),"source_reliability":trust.get("source","UNKNOWN")}
    actions=_actions(watch,officer_decision)
    assistant={"data_origin":origin,"mode":mode.value,"identity":identity,"current_state":current_state,"schedule_intelligence":schedule,"cost_intelligence":cost,"implementation_watch":watch,"data_trust":trust,"peer_benchmark":benchmark,"officer_decision":officer_decision,"recommended_actions":actions,"evidence":evidence,"constraints":["Do not invent predictions or causes.","Do not override deterministic decision state.","Preserve synthetic provenance visibly."]}
    return ProjectIntelligence(mode=mode,data_origin=origin,identity=identity,current_state=current_state,schedule_intelligence=schedule,cost_intelligence=cost,implementation_watch=watch,data_trust=trust,reliability=reliability,peer_benchmark=benchmark,risk_trend=attention_trend(watch,previous_watch),officer_decision=officer_decision|{"recommended_actions":actions},alerts_summary={"operational_alert_created":False,"status":officer_decision.get("alert_status","NOT_ELIGIBLE"),"prediction_alerts_withheld":True},evidence_summary=evidence,assistant_context=assistant,provenance=provenance)
