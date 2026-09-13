"""PRAHARI C1/C2 approved-cost deterioration research contracts.

Labels are machine-provisional and may be evaluated only under the explicit
PROTOTYPE_RESEARCH_OVERRIDE.  This module predicts approved cost-state changes,
not final expenditure and not exact final project cost.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter,defaultdict
from datetime import date
from typing import Any,Iterable

import numpy as np

from src.ml.final_prediction import _completed,add_month,build_compact_v2,exact_value
from src.ml.provisional_research import approved_doc,month_date,month_index,number,value

RESEARCH_MODE="PROTOTYPE_RESEARCH_OVERRIDE"
TARGET_VALIDATION_STATUS="MACHINE_PROVISIONAL"
TARGET_VERSIONS={"C1":"C1-v1-machine-provisional","C2":"C2-v1-machine-provisional"}
COST_UNIT="INR_CRORE"
MIN_EVENT_COUNT=30

COST_BASIC_C1=("log_original_cost","planned_duration_months","project_age_months","expenditure_to_original_cost",
               "expenditure_to_current_approved_cost","history_span_months","remaining_schedule_months",
               "recent_expenditure_velocity","schedule_deteriorated_at_t","prior_schedule_revision_months")
COST_BASIC_C2=COST_BASIC_C1+("current_approved_cost_revision_pct","prior_approved_cost_revision_count")
COST_COMPACT_EXTRA=("physical_progress","physical_progress_missing","progress_vs_elapsed_gap","consecutive_stagnant")
DRIVER_TEXT={
 "expenditure_to_original_cost":"Expenditure is high relative to the original approved project cost.",
 "expenditure_to_current_approved_cost":"Expenditure is high relative to the currently approved project cost.",
 "project_age_months":"The project has remained under implementation for an extended period.",
 "current_approved_cost_revision_pct":"The project has already experienced approved cost escalation.",
 "remaining_schedule_months":"The currently approved completion date is near.",
 "prior_schedule_revision_months":"The approved completion schedule has previously moved outward.",
 "physical_progress":"The reported physical-progress position contributed to this warning.",
 "consecutive_stagnant":"Recent reported physical progress has been stagnant.",
}

FEATURE_SOURCES={
 "log_original_cost":("original_cost_raw","log1p(original approved cost)","all compatible eras"),
 "planned_duration_months":("approval_date_raw + original_target_doc_raw","calendar month difference","where both dates exist"),
 "project_age_months":("approval_date_raw + reporting_month","calendar month difference at T","where approval date exists"),
 "expenditure_to_original_cost":("cumulative_expenditure_raw + original_cost_raw","ratio at T","all compatible eras"),
 "expenditure_to_current_approved_cost":("cumulative_expenditure_raw + revised/original cost","ratio at T","all compatible eras"),
 "history_span_months":("project-month observations","inclusive observed span through T","all eras"),
 "remaining_schedule_months":("approved completion date + reporting_month","nonnegative months remaining at T","where approved date exists"),
 "recent_expenditure_velocity":("current and T-1 cumulative expenditure","first difference","requires contiguous T-1"),
 "schedule_deteriorated_at_t":("original/revised completion dates","known approved schedule shift at T","where dates exist"),
 "prior_schedule_revision_months":("original/revised completion dates","known shift magnitude at T","where dates exist"),
 "current_approved_cost_revision_pct":("original/revised cost","known C2 escalation at T","C2 only"),
 "prior_approved_cost_revision_count":("project approved-cost history","count of observed upward state changes through T","C2 only"),
 "physical_progress":("physical_progress_raw","normalized current value at T","richer compatible era only"),
 "physical_progress_missing":("physical_progress_raw","explicit missingness indicator at T","richer compatible era only"),
 "progress_vs_elapsed_gap":("physical progress + schedule dates","as-of-T derived gap","richer compatible era only"),
 "consecutive_stagnant":("physical progress history","trailing as-of-T stagnation count","richer compatible era only"),
}


def cost_feature_registry() -> list[dict[str,Any]]:
    rows=[]
    for feature in dict.fromkeys(COST_BASIC_C2+COST_COMPACT_EXTRA):
        source,derivation,era=FEATURE_SOURCES[feature]
        rows.append({"feature":feature,"source_field":source,"derivation":derivation,"availability_era":era,
                     "known_at_t":"YES","future_value_used":"NO","missingness_semantics":"PRESERVED_FOR_FOLD_LOCAL_IMPUTATION",
                     "used_c1":"YES" if feature in COST_BASIC_C1 or feature in COST_COMPACT_EXTRA else "NO",
                     "used_c2":"YES","basic_compatible":"YES" if feature in COST_BASIC_C2 else "NO",
                     "compact_compatible":"YES"})
    return rows


def normalize_cost(raw: Any, source_unit: str=COST_UNIT) -> dict[str,Any]:
    """Normalize an explicit cost value to crore without guessing unknown units."""
    original="" if raw is None else str(raw).strip(); text=original.replace(",","").replace("₹","")
    if not original or original.upper() in {"-","NA","N/A","N.A.","NULL","NONE","UNKNOWN","NOT AVAILABLE"}:
        return {"raw":original,"value_crore":math.nan,"source_unit":source_unit,"method":"MISSING"}
    lakh=bool(re.search(r"(?i)\blakh\b",text)); crore=bool(re.search(r"(?i)\b(?:crore|cr\.?)\b",text))
    if source_unit not in {"INR_CRORE","INR_LAKH","EXPLICIT_IN_TEXT"}: raise ValueError("UNKNOWN_COST_UNIT")
    if lakh and crore: raise ValueError("CONFLICTING_COST_UNITS")
    if source_unit=="EXPLICIT_IN_TEXT" and not (lakh or crore): raise ValueError("AMBIGUOUS_COST_UNIT")
    text=re.sub(r"(?i)\b(?:rs\.?|inr|lakh|crore|cr\.?)\b","",text).strip()
    try: parsed=float(text)
    except ValueError:return {"raw":original,"value_crore":math.nan,"source_unit":source_unit,"method":"UNPARSEABLE"}
    if math.isfinite(parsed) and (lakh or source_unit=="INR_LAKH"): parsed/=100.0
    method="EXPLICIT_LAKH_TO_CRORE" if lakh or source_unit=="INR_LAKH" else "TABLE_HEADER_CRORE_NO_SCALING"
    return {"raw":original,"value_crore":parsed,"source_unit":"INR_LAKH" if lakh else "INR_CRORE","method":method}


def cost(row: dict[str,Any],field: str) -> float:
    fallback={"original_cost_raw":"reported_original_cost","revised_cost_raw":"reported_revised_cost",
              "anticipated_cost_raw":"anticipated_cost_raw","cumulative_expenditure_raw":"reported_cumulative_expenditure"}.get(field,"")
    return normalize_cost(value(row,field,fallback))["value_crore"]


def greater(candidate: float,baseline: float) -> bool:
    return math.isfinite(candidate) and math.isfinite(baseline) and candidate-baseline>max(.01,abs(baseline)*1e-6)


def approved_cost(row: dict[str,Any]) -> float:
    original=cost(row,"original_cost_raw"); revised=cost(row,"revised_cost_raw")
    return revised if math.isfinite(revised) else original


def upward_revision(row: dict[str,Any]) -> bool:
    return greater(cost(row,"revised_cost_raw"),cost(row,"original_cost_raw"))


def cost_correction_flags(history: list[dict[str,Any]]) -> list[str]:
    flags=[]
    originals=[cost(r,"original_cost_raw") for r in history]
    states=[approved_cost(r) for r in history]
    if any(
        math.isfinite(a) and math.isfinite(b) and (greater(a,b) or greater(b,a))
        for a,b in zip(originals,originals[1:])
    ):
        flags.append("ORIGINAL_COST_CHANGED")
    if any(math.isfinite(a) and math.isfinite(b) and greater(a,b) for a,b in zip(states,states[1:])):
        flags.append("APPROVED_COST_REVERSAL_OR_CORRECTION")
    return flags


def _ratio(a,b): return a/b if math.isfinite(a) and math.isfinite(b) and b>0 else math.nan


def build_cost_features(history: list[dict[str,Any]],target: str,compact: bool=False) -> dict[str,float]:
    history=sorted(history,key=lambda r:r["reporting_month"]); anchor=history[-1]
    original=cost(anchor,"original_cost_raw"); current=approved_cost(anchor); expenditure=cost(anchor,"cumulative_expenditure_raw")
    approval=month_date(value(anchor,"approval_date_raw","reported_approval_date")); original_doc=month_date(value(anchor,"original_target_doc_raw","reported_original_target_doc")); current_doc=approved_doc(anchor)
    y,m=map(int,anchor["reporting_month"].split("-")); as_of=date(y,m,1)
    planned=float((original_doc.year-approval.year)*12+original_doc.month-approval.month) if approval and original_doc else math.nan
    age=float((as_of.year-approval.year)*12+as_of.month-approval.month) if approval else math.nan
    remaining=float(max(0,(current_doc.year-as_of.year)*12+current_doc.month-as_of.month)) if current_doc else math.nan
    previous_exp=exact_value(history,1,"cumulative_expenditure_raw","reported_cumulative_expenditure")
    revision_count=0; last=math.nan
    for row in history:
        state=approved_cost(row)
        if math.isfinite(last) and greater(state,last): revision_count+=1
        last=state
    revised_doc=month_date(value(anchor,"revised_doc_raw","reported_revised_doc"))
    schedule_revision=float((revised_doc.year-original_doc.year)*12+revised_doc.month-original_doc.month) if revised_doc and original_doc and revised_doc>original_doc else 0.0
    features={"log_original_cost":math.log1p(original) if math.isfinite(original) and original>=0 else math.nan,
              "planned_duration_months":planned,"project_age_months":age,"expenditure_to_original_cost":_ratio(expenditure,original),
              "expenditure_to_current_approved_cost":_ratio(expenditure,current),
              "history_span_months":float(month_index(anchor["reporting_month"])-month_index(history[0]["reporting_month"])+1),
              "remaining_schedule_months":remaining,
              "recent_expenditure_velocity":expenditure-previous_exp if math.isfinite(expenditure) and math.isfinite(previous_exp) else math.nan,
              "schedule_deteriorated_at_t":float(schedule_revision>0),"prior_schedule_revision_months":schedule_revision}
    if target=="C2": features.update(current_approved_cost_revision_pct=100*(current-original)/original if math.isfinite(current) and math.isfinite(original) and original>0 else math.nan,
                                      prior_approved_cost_revision_count=float(revision_count))
    if compact:
        base=build_compact_v2(history)
        features.update({name:base[name] for name in COST_COMPACT_EXTRA})
    expected=(COST_BASIC_C2 if target=="C2" else COST_BASIC_C1)+(COST_COMPACT_EXTRA if compact else ())
    assert tuple(features)==expected
    return features


def build_cost_target(rows: list[dict[str,Any]],coverage: dict[str,str],target: str,horizon: int,compact=False):
    if target not in {"C1","C2"} or horizon not in {3,6,12}: raise ValueError("unsupported cost target")
    grouped=defaultdict(list)
    for row in rows: grouped[row["canonical_project_id"]].append(row)
    cohort=[];ledger=[];events=[]
    for pid,observations in sorted(grouped.items()):
        observations.sort(key=lambda r:r["reporting_month"]); lookup={r["reporting_month"]:r for r in observations}
        for idx,anchor in enumerate(observations):
            history=observations[:idx+1]; future_months=[add_month(anchor["reporting_month"],i) for i in range(1,horizon+1)]; reasons=[]
            original=cost(anchor,"original_cost_raw"); revised=cost(anchor,"revised_cost_raw"); frozen=approved_cost(anchor)
            if anchor.get("identity_status")!="RESOLVED_EXACT": reasons.append("IDENTITY_NOT_EXACT")
            if not math.isfinite(original) or original<=0: reasons.append("ORIGINAL_APPROVED_COST_UNAVAILABLE")
            if _completed(anchor): reasons.append("COMPLETED_AT_T")
            ever=any(upward_revision(row) for row in history)
            if target=="C1" and ever: reasons.append("PRIOR_APPROVED_COST_DETERIORATION")
            if target=="C2" and not upward_revision(anchor): reasons.append("NO_APPROVED_COST_DETERIORATION_AT_T")
            if len(history)<2: reasons.append("INSUFFICIENT_HISTORY")
            elif add_month(history[-2]["reporting_month"],1)!=anchor["reporting_month"]: reasons.append("PRIOR_MONTH_GAP")
            if any(coverage.get(month)!="PROJECT_LEVEL" for month in future_months): reasons.append("FUTURE_SOURCE_COVERAGE_GAP")
            if any(month not in lookup for month in future_months): reasons.append("FUTURE_PROJECT_OBSERVATION_MISSING")
            future_pairs=[(month,lookup[month]) for month in future_months if month in lookup]
            future_rows=[row for _,row in future_pairs]
            anticipated_only=any(greater(cost(r,"anticipated_cost_raw"),frozen) and not greater(cost(r,"revised_cost_raw"),frozen) for r in future_rows)
            original_changed=any(math.isfinite(cost(r,"original_cost_raw")) and (greater(cost(r,"original_cost_raw"),original) or greater(original,cost(r,"original_cost_raw"))) for r in future_rows)
            history_flags=cost_correction_flags(history)
            combined_flags=list(dict.fromkeys(history_flags+cost_correction_flags(history[-3:]+future_rows)))
            if "ORIGINAL_COST_CHANGED" in history_flags: reasons.append("ORIGINAL_COST_HISTORY_INCONSISTENT")
            if "APPROVED_COST_REVERSAL_OR_CORRECTION" in history_flags: reasons.append("HISTORICAL_COST_REVERSAL_REQUIRES_VERIFICATION")
            if original_changed: reasons.append("ORIGINAL_COST_CHANGED_IN_OUTCOME_WINDOW")
            if "APPROVED_COST_REVERSAL_OR_CORRECTION" in combined_flags: reasons.append("COST_REVERSAL_REQUIRES_VERIFICATION")
            event_month=None;event_cost=math.nan
            if not reasons:
                baseline=original if target=="C1" else revised
                for month,row in future_pairs:
                    candidate=cost(row,"revised_cost_raw")
                    if greater(candidate,baseline): event_month,event_cost=month,candidate; break
            event=int(event_month is not None) if not reasons else None
            status="ELIGIBLE" if not reasons else ("CENSORED" if any(r.startswith("FUTURE_") or "OUTCOME_WINDOW" in r or "REVERSAL" in r or "HISTORY_INCONSISTENT" in r for r in reasons) else "EXCLUDED")
            timeline=[]
            for offset in range(-1,horizon+1):
                month=add_month(anchor["reporting_month"],offset); row=lookup.get(month,{})
                timeline.append({"month":month,"original":cost(row,"original_cost_raw"),"revised":cost(row,"revised_cost_raw"),"anticipated":cost(row,"anticipated_cost_raw"),"source_id":row.get("source_id"),"page":row.get("pdf_page_index")})
            item={"canonical_project_id":pid,"project_name":anchor.get("project_name_raw",anchor.get("reported_project_name","")),"anchor_month":anchor["reporting_month"],"target":target,"horizon_months":horizon,
                  "target_version":TARGET_VERSIONS[target] if horizon==3 else f"{target}-{horizon}M-v1-machine-provisional","target_validation_status":TARGET_VALIDATION_STATUS,"research_mode":RESEARCH_MODE,
                  "identity_status":anchor.get("identity_status"),"original_approved_cost":original,"frozen_revised_cost_at_t":revised if math.isfinite(revised) else "",
                  "frozen_approved_cost_at_t":frozen,"event":event,"event_month":event_month or "","event_revised_cost":event_cost if math.isfinite(event_cost) else "",
                  "cost_increase_absolute":event_cost-frozen if math.isfinite(event_cost) else "","cost_increase_percent":100*(event_cost-frozen)/frozen if math.isfinite(event_cost) and frozen>0 else "",
                  "completion_state":"COMPLETED" if _completed(anchor) else "ONGOING","source_coverage":"|".join(f"{m}:{coverage.get(m,'UNKNOWN')}" for m in future_months),
                  "schema_family":anchor.get("schema_family"),"correction_like_flags":"|".join(combined_flags),"anticipated_only_flag":str(anticipated_only).upper(),
                  "source_id":anchor.get("source_id"),"source_page":anchor.get("pdf_page_index"),"source_table":anchor.get("source_table"),"cost_unit":COST_UNIT,
                  "status":status,"primary_reason":reasons[0] if reasons else "","secondary_reasons":"|".join(reasons[1:]),"timeline":timeline}
            ledger.append(item)
            if not reasons:
                feature=build_cost_features(history,target,compact)
                cohort.append({"row_key":f"{pid}|{anchor['reporting_month']}","canonical_project_id":pid,"anchor_month":anchor["reporting_month"],"target":target,"horizon_months":horizon,"event":event,"event_month":event_month or "","schema_family":anchor.get("schema_family",""),**feature})
                if event: events.append(item)
    return cohort,ledger,events


def cost_rule_probability(row: dict[str,Any],target: str) -> float:
    """Predeclared transparent comparator; output is a rule signal, not calibrated risk."""
    spend=float(row.get("expenditure_to_current_approved_cost",math.nan)); remaining=float(row.get("remaining_schedule_months",math.nan)); age=float(row.get("project_age_months",math.nan)); planned=float(row.get("planned_duration_months",math.nan))
    signal=(math.isfinite(spend) and spend>=.9 and math.isfinite(remaining) and remaining<=6) or (math.isfinite(spend) and spend>=.8 and math.isfinite(age) and math.isfinite(planned) and planned>0 and age>=planned)
    if target=="C2": signal=signal or (float(row.get("current_approved_cost_revision_pct",0) or 0)>=20 and math.isfinite(spend) and spend>=.85)
    return .75 if signal else .25


def translate_contributors(items: list[dict[str,Any]]) -> list[dict[str,Any]]:
    result=[]
    for rank,item in enumerate(items,1):
        feature=item["feature"]
        result.append({"rank":rank,"feature":feature,"value":item.get("value"),"direction":item.get("direction"),"contribution":item.get("contribution"),"officer_language":DRIVER_TEXT.get(feature,"This source-backed project characteristic contributed to the warning."),"causal":False})
    return result


def peer_benchmark(row: dict[str,Any],peers: list[dict[str,Any]],metric: str,min_support: int=30) -> dict[str,Any]:
    values=np.asarray([float(p[metric]) for p in peers if p.get(metric) not in (None,"") and math.isfinite(float(p[metric]))])
    current=float(row[metric]) if row.get(metric) not in (None,"") else math.nan
    if len(values)<min_support or not math.isfinite(current): return {"metric":metric,"status":"WITHHELD","reason":"PEER_SUPPORT_INSUFFICIENT","peer_sample_size":len(values)}
    return {"metric":metric,"status":"AVAILABLE","project_value":current,"peer_median":float(np.median(values)),"peer_percentile":float(100*np.mean(values<=current)),"peer_sample_size":len(values)}


def cost_api_payload(*,project_id: str,target: str,horizon: int,probability: float|None,reliability: str,contributors: list[dict[str,Any]],model_version: str,feature_version: str,as_of: str,withheld_reasons=()):
    available=probability is not None and not withheld_reasons
    return {"cost_prediction_status":"AVAILABLE_RESEARCH" if available else "WITHHELD","cost_target_family":target,"cost_horizon_months":horizon,
            "cost_probability":probability if available else None,"cost_risk_band":None,"cost_reliability":reliability,"cost_trend":"INSUFFICIENT_HISTORY",
            "top_cost_contributors":contributors if available else [],"cost_model_version":model_version,"cost_feature_version":feature_version,
            "cost_prediction_as_of":as_of,"cost_withheld_reasons":list(withheld_reasons),"cost_research_override":True,"cost_machine_provisional":True,
            "canonical_project_id":project_id,"production_release_status":"WITHHELD"}


def withheld_cost_evidence(*,project_id: str,as_of: str,reasons: Iterable[str]|None=None) -> dict[str,Any]:
    """Authoritative assistant/API evidence when no governed cost model is admitted."""
    return cost_api_payload(
        project_id=project_id,target="C1",horizon=3,probability=None,
        reliability="ABSTAIN",contributors=[],model_version="UNAVAILABLE",
        feature_version="COST_BASIC_LONG_HISTORY_V1",as_of=as_of,
        withheld_reasons=tuple(reasons or ("NO_COST_MODEL_PASSED_RESEARCH_ADMISSION",)),
    )


def unified_risk_profile(schedule: dict[str,Any]|None,cost_prediction: dict[str,Any]|None,data_trust: dict[str,Any]) -> dict[str,Any]:
    schedule= schedule or {}; cost_prediction=cost_prediction or {}
    schedule_high=schedule.get("risk_band")=="HIGH" and schedule.get("prediction_status")=="AVAILABLE"
    cost_high=cost_prediction.get("cost_warning_state")=="ELEVATED" or cost_prediction.get("cost_risk_band")=="HIGH"
    reasons=[]
    if schedule_high: reasons.append("SCHEDULE_RISK_SIGNAL")
    if cost_high: reasons.append("COST_RISK_SIGNAL")
    if schedule_high and cost_high: reasons=["MULTI_RISK_SIGNAL",*reasons]
    if not data_trust.get("data_usable",data_trust.get("data_status")=="USABLE"): state="DATA_VERIFICATION_REQUIRED"; reasons.append("DATA_VERIFICATION")
    elif cost_prediction.get("cost_prediction_status")=="WITHHELD" and schedule.get("prediction_status")!="AVAILABLE": state="PREDICTION_WITHHELD"; reasons.append("MODEL_RELEASE_PENDING")
    elif reasons: state="REVIEW_RECOMMENDED"
    else: state="MONITOR"
    return {"schedule_warning":schedule,"cost_warning":cost_prediction,"prediction_reliability":{"schedule":schedule.get("reliability_band"),"cost":cost_prediction.get("cost_reliability")},"data_trust":data_trust,"officer_decision":{"state":state,"reason_codes":list(dict.fromkeys(reasons)),"recommended_action":"Verify latest approved cost, recent expenditure pattern, approved revisions and schedule feasibility" if state=="REVIEW_RECOMMENDED" else "Continue governed monitoring"},"composite_numeric_score":None}


def cohort_fingerprint(rows: Iterable[dict[str,Any]]) -> str:
    return hashlib.sha256("\n".join(sorted(f"{r['row_key']}|{r['event']}" for r in rows)).encode()).hexdigest()
