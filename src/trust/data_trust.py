"""Model-independent data trust and prediction eligibility V1."""
from __future__ import annotations
import math
from dataclasses import asdict,dataclass
from typing import Any
import numpy as np
from src.ml.final_prediction import COMPACT_V2, EXACT_IDENTITY, add_month, build_compact_v2

TRUST_CONTRACT_VERSION='data-trust-v1'
MINIMUM_HISTORY_MONTHS=13
PASS='PASS';WARN='WARN';FAIL='FAIL';UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class Dimension:
    status:str; code:str; reason:str
@dataclass(frozen=True)
class DataTrustResult:
    canonical_project_id:str;as_of_month:str
    identity:Dimension;source:Dimension;coverage:Dimension;history:Dimension
    freshness:Dimension;features:Dimension;schema:Dimension;provenance:Dimension
    observed_history_months:int;history_span_months:int;contiguous_recent_history:int
    minimum_required_history:int;observed_project_level_months:list[str]
    aggregate_only_months:list[str];missing_source_months:list[str];project_missing_months:list[str]
    available_features:list[str];missing_features:list[str]
    data_usable:bool;data_reason_codes:list[str]
    trust_contract_version:str=TRUST_CONTRACT_VERSION
    def to_dict(self):return asdict(self)

class DataTrustEvaluator:
    def __init__(self,coverage:dict[str,str],manifest:dict[str,dict[str,str]],minimum_history:int=MINIMUM_HISTORY_MONTHS):
        self.coverage=coverage;self.manifest=manifest;self.minimum_history=minimum_history
    def evaluate(self,history:list[dict[str,str]],as_of_month:str)->DataTrustResult:
        rows=sorted((r for r in history if r.get('reporting_month','')<=as_of_month),key=lambda r:r['reporting_month']); anchor=next((r for r in reversed(rows) if r['reporting_month']==as_of_month),None);latest=rows[-1] if rows else None
        pid=(anchor or latest or {}).get('canonical_project_id','UNKNOWN')
        identity_row=anchor or latest
        identity=Dimension(PASS,'VERIFIED_IDENTITY','Exact canonical identity') if identity_row and identity_row.get('identity_status')==EXACT_IDENTITY else Dimension(FAIL,'IDENTITY_UNCERTAIN','Identity is not RESOLVED_EXACT')
        source=Dimension(FAIL,'SOURCE_AS_OF_OBSERVATION_UNAVAILABLE','Project has no observation at the requested as-of month')
        provenance=Dimension(UNKNOWN,'PROVENANCE_UNKNOWN','No as-of provenance')
        if anchor:
            sid=anchor.get('source_id','');m=self.manifest.get(sid);row_hash=anchor.get('source_sha256','')
            if not m:source=Dimension(FAIL,'SOURCE_UNAVAILABLE','Source ID is not registered')
            elif row_hash and m.get('sha256') and row_hash!=m.get('sha256'):source=Dimension(FAIL,'SOURCE_MISMATCH','Observation and manifest SHA-256 differ')
            else:source=Dimension(PASS,'VERIFIED_SOURCE','Registered source and SHA-256 agree')
            complete=bool(sid and row_hash and anchor.get('pdf_page_index') not in ('',None) and anchor.get('source_table'))
            provenance=Dimension(PASS,'PROVENANCE_COMPLETE','Source, hash, physical page and table are present') if complete else Dimension(WARN,'PARTIAL_PROVENANCE','One or more provenance fields are unavailable')
        first=rows[0]['reporting_month'] if rows else as_of_month;months=[];m=first
        while m<=as_of_month:months.append(m);m=add_month(m,1)
        aggregate=[m for m in months if self.coverage.get(m)=='AGGREGATE_ONLY'];missing_source=[m for m in months if self.coverage.get(m)=='MISSING_SOURCE' or m not in self.coverage]
        observed={r['reporting_month'] for r in rows};project_missing=[m for m in months if self.coverage.get(m)=='PROJECT_LEVEL' and m not in observed]
        contiguous=0;cursor=as_of_month
        while cursor in observed and self.coverage.get(cursor)=='PROJECT_LEVEL':contiguous+=1;cursor=add_month(cursor,-1)
        gaps=aggregate or missing_source or project_missing
        if not anchor:coverage=Dimension(FAIL,'SOURCE_INTERVAL_MISSING','Requested as-of project observation is unavailable')
        elif gaps and contiguous>=self.minimum_history:coverage=Dimension(WARN,'HISTORICAL_SOURCE_GAPS','Historical gaps exist outside the sufficient contiguous recent window')
        elif gaps:coverage=Dimension(FAIL,'SOURCE_INTERVAL_MISSING','Required recent source/project interval is unavailable')
        else:coverage=Dimension(PASS,'CONTINUOUS_PROJECT_LEVEL','All intervals are observed project-level months')
        span=(int(as_of_month[:4])-int(first[:4]))*12+int(as_of_month[5:])-int(first[5:])+1 if rows else 0
        history_dim=Dimension(PASS,'HISTORY_SUFFICIENT',f'At least {self.minimum_history} contiguous recent months') if contiguous>=self.minimum_history else Dimension(FAIL,'INSUFFICIENT_HISTORY',f'{contiguous} contiguous recent months; {self.minimum_history} required')
        freshness=Dimension(PASS,'LATEST_AS_OF','Observation exists at requested as-of month') if anchor else (Dimension(WARN,'STALE_ONE_OR_MORE_REPORTING_PERIODS',f"Latest observation is {(latest or {}).get('reporting_month','unknown')}") if latest else Dimension(UNKNOWN,'FRESHNESS_UNKNOWN','No project observations'))
        feature_values=build_compact_v2(rows) if anchor else {n:math.nan for n in COMPACT_V2};missing=[n for n,v in feature_values.items() if not np.isfinite(v)];available=[n for n in COMPACT_V2 if n not in missing]
        temporal_required={'consecutive_stagnant','expenditure_velocity'}
        if temporal_required<=set(available):feature_dim=Dimension(PASS if not missing else WARN,'FEATURES_READY' if not missing else 'FEATURES_PARTIAL_SUPPORTED',f'{len(available)}/14 features available; training imputer supports remaining missing values')
        else:feature_dim=Dimension(FAIL,'FEATURES_INSUFFICIENT','Required temporal feature evidence is unavailable')
        if not anchor:schema=Dimension(UNKNOWN,'SCHEMA_NOT_EVALUABLE_NO_OBSERVATION','Schema cannot be evaluated without an as-of project observation')
        elif not anchor.get('schema_family'):schema=Dimension(UNKNOWN,'SCHEMA_UNKNOWN','Schema family unavailable')
        elif anchor.get('physical_progress_schema_available','').upper() in {'NO','FALSE','0'}:schema=Dimension(FAIL,'SCHEMA_UNSUPPORTED','Physical progress is structurally unavailable')
        elif anchor.get('physical_progress_schema_available','').upper() not in {'YES','TRUE','1'}:schema=Dimension(UNKNOWN,'SCHEMA_UNKNOWN','Physical-progress schema support is not recorded')
        else:schema=Dimension(PASS,'SCHEMA_SUPPORTED',f"Schema {anchor.get('schema_family')} supports the governed input")
        reasons=[]
        for d in (identity,source,coverage,history_dim,freshness,feature_dim,schema,provenance):
            if d.status in (FAIL,UNKNOWN):reasons.append(d.code)
        reasons=list(dict.fromkeys(reasons));usable=not reasons
        return DataTrustResult(pid,as_of_month,identity,source,coverage,history_dim,freshness,feature_dim,schema,provenance,len(rows),span,contiguous,self.minimum_history,[r['reporting_month'] for r in rows if self.coverage.get(r['reporting_month'])=='PROJECT_LEVEL'],aggregate,missing_source,project_missing,available,missing,usable,reasons)

def frontend_view(result:DataTrustResult)->dict[str,Any]:
    return {'trust_contract_version':result.trust_contract_version,'data_status':'USABLE' if result.data_usable else 'NOT_USABLE','identity':result.identity.code,'source':result.source.code,'history':result.history.code,'latest_month':result.as_of_month,'source_gap_count':len(result.aggregate_only_months)+len(result.missing_source_months)+len(result.project_missing_months),'features':result.features.code,'reasons':result.data_reason_codes}

def enforce_prediction_eligibility(prediction:dict[str,Any],result:DataTrustResult,eligibility=None)->dict[str,Any]:
    """Apply the deterministic trust gate after inference without changing trust from model output."""
    guarded=dict(prediction)
    guarded['data_trust']=result.to_dict()
    allowed=eligibility.prediction_eligible if eligibility is not None else result.data_usable
    if allowed:
        return guarded
    reasons=eligibility.reason_codes if eligibility is not None else result.data_reason_codes
    guarded.update({
        'prediction_status':'WITHHELD',
        'probability':None,
        'risk_band':None,
        'reliability_status':'WITHHELD',
        'withholding_reason_codes':list(reasons),
    })
    return guarded
