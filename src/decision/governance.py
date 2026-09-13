"""PRAHARI Officer Decision Layer V1; independent of model training and LLM output."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from hashlib import sha256
from typing import Any
from src.trust.data_trust import DataTrustResult

RELEASE_CONTRACT_VERSION='model-release-v1'
ELIGIBILITY_CONTRACT_VERSION='prediction-eligibility-v1'
DECISION_POLICY_VERSION='officer-decision-v1'
ALERT_POLICY_VERSION='alert-policy-v1'
REVIEW_STATES=frozenset({'REVIEW_RECOMMENDED','DATA_VERIFICATION_REQUIRED','MONITOR','NO_REVIEW_SIGNAL','PREDICTION_WITHHELD'})
ALERT_STATES=frozenset({'NOT_ELIGIBLE','ELIGIBLE_NOT_CREATED','OPEN','ACKNOWLEDGED','RESOLVED'})

@dataclass(frozen=True)
class ModelReleaseStatus:
    status:str='WITHHELD'
    reason_codes:tuple[str,...]=('HUMAN_TARGET_VALIDATION_PENDING','CALIBRATION_NOT_CONFIRMED','MODEL_NOT_RELEASED')
    contract_version:str=RELEASE_CONTRACT_VERSION
    def to_dict(self):return asdict(self)

@dataclass(frozen=True)
class PredictionEligibilityResult:
    prediction_eligible:bool;reason_codes:list[str]
    contract_version:str=ELIGIBILITY_CONTRACT_VERSION
    def to_dict(self):return asdict(self)

@dataclass(frozen=True)
class ReviewDecision:
    canonical_project_id:str;as_of_month:str;target_family:str|None
    review_state:str;priority:str|None;prediction_status:str;reliability:str|None
    reason_codes:list[str];recommended_action:str|None;last_valid_update:str|None
    alert_status:str;alert_deduplication_key:str|None
    decision_policy_version:str=DECISION_POLICY_VERSION
    alert_policy_version:str=ALERT_POLICY_VERSION
    def to_dict(self):return asdict(self)

def assess_prediction_eligibility(trust:DataTrustResult,release:ModelReleaseStatus,*,project_completed=False,target_eligible=True,artifact_available=True)->PredictionEligibilityResult:
    reasons=list(trust.data_reason_codes)
    if project_completed:reasons.append('PROJECT_COMPLETED')
    if not target_eligible:reasons.append('TARGET_NOT_ELIGIBLE')
    if not artifact_available:reasons.append('ARTIFACT_UNAVAILABLE')
    if release.status!='RELEASED':reasons.extend(release.reason_codes)
    reasons=list(dict.fromkeys(reasons))
    return PredictionEligibilityResult(not reasons,reasons)

def alert_deduplication_key(project_id:str,target:str,model_version:str,alert_type:str,window:str)->str:
    material='|'.join((project_id,target,model_version,alert_type,window))
    return sha256(material.encode()).hexdigest()[:24]

def decide_review(*,trust:DataTrustResult,eligibility:PredictionEligibilityResult,prediction:dict[str,Any]|None=None,project_completed=False,existing_unresolved_alert_keys=frozenset(),alert_rule_satisfied=False,implementation_watch:dict[str,Any]|None=None)->ReviewDecision:
    project_completed=project_completed or 'PROJECT_COMPLETED' in eligibility.reason_codes
    prediction=prediction or {};status=prediction.get('prediction_status','WITHHELD');target=prediction.get('target');reliability=prediction.get('reliability_band')
    reasons=[];state='NO_REVIEW_SIGNAL';action=None;priority=None;alert_status='NOT_ELIGIBLE';dedup=None
    data_map={'IDENTITY_UNCERTAIN':'IDENTITY_VERIFICATION','SOURCE_INTERVAL_MISSING':'SOURCE_GAP','SOURCE_AS_OF_OBSERVATION_UNAVAILABLE':'STALE_UPDATE','STALE_ONE_OR_MORE_REPORTING_PERIODS':'STALE_UPDATE','INSUFFICIENT_HISTORY':'INSUFFICIENT_HISTORY','FEATURES_INSUFFICIENT':'FEATURES_INSUFFICIENT','SCHEMA_UNKNOWN':'SCHEMA_VERIFICATION','SCHEMA_NOT_EVALUABLE_NO_OBSERVATION':'SCHEMA_VERIFICATION','PROVENANCE_UNKNOWN':'SOURCE_PROVENANCE_VERIFICATION'}
    actionable=list(dict.fromkeys(data_map[x] for x in trust.data_reason_codes if x in data_map))
    watch=implementation_watch or {};watch_status=watch.get('status');watch_reasons=set(watch.get('reason_codes',[]))
    watch_data_issue=bool(watch_reasons & {'REPORT_STALE','REPORT_MONTH_MISSING','SOURCE_GAP','FEATURE_DATA_INCOMPLETE','STRUCTURAL_SCHEMA_LIMITATION','PROVENANCE_INCOMPLETE'})
    if project_completed:
        reasons=['COMPLETED_PROJECT'];action=None
    elif actionable:
        state='DATA_VERIFICATION_REQUIRED';reasons=actionable;action='Review latest project update and verify missing or inconsistent reporting evidence'
    elif watch_data_issue and watch_status=='DATA_INSUFFICIENT':
        state='DATA_VERIFICATION_REQUIRED';reasons=['DATA_VERIFICATION_REQUIRED'];action='Verify the reporting, provenance, or structured field evidence required by Implementation Watch'
    elif watch_status in {'WATCH','ELEVATED'} and trust.data_usable:
        state='REVIEW_RECOMMENDED';priority='HIGH' if watch_status=='ELEVATED' else 'MEDIUM';reasons=['IMPLEMENTATION_PRESSURE_SIGNAL'];action='Review the observable implementation-pressure signals and their source evidence';alert_status='NOT_ELIGIBLE'
    elif status!='AVAILABLE' or not eligibility.prediction_eligible:
        state='PREDICTION_WITHHELD';reasons=['MODEL_RELEASE_PENDING'] if any(x in eligibility.reason_codes for x in ('HUMAN_TARGET_VALIDATION_PENDING','CALIBRATION_NOT_CONFIRMED','MODEL_NOT_RELEASED')) else list(eligibility.reason_codes) or ['NO_ACTIONABLE_SIGNAL'];action='Monitor until the governed prediction release requirements are satisfied'
    elif prediction.get('risk_band')=='HIGH' and reliability in {'HIGH','MODERATE'} and trust.data_usable:
        state='REVIEW_RECOMMENDED';reasons=['RISK_SIGNAL'];action='Review project due to elevated predictive signal'
        if alert_rule_satisfied:
            dedup=alert_deduplication_key(trust.canonical_project_id,target or 'UNKNOWN',prediction.get('model_version','UNKNOWN'),'ELEVATED_PREDICTIVE_SIGNAL',trust.as_of_month)
            alert_status='NOT_ELIGIBLE' if dedup in existing_unresolved_alert_keys else 'ELIGIBLE_NOT_CREATED'
    else:
        state='MONITOR';reasons=['LOW_RELIABILITY'] if reliability not in {'HIGH','MODERATE'} else ['NO_ACTIONABLE_SIGNAL'];action='Continue routine monitoring'
    return ReviewDecision(trust.canonical_project_id,trust.as_of_month,target,state,priority,status,reliability,reasons,action,trust.observed_project_level_months[-1] if trust.observed_project_level_months else None,alert_status,dedup)
