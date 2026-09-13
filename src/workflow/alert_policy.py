"""Pure deterministic alert eligibility policy; Officer Decision is authoritative."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
POLICY=json.loads((ROOT/'config'/'alert_policy_v1.json').read_text(encoding='utf-8'))
POLICY_VERSION=POLICY['policy_version']

@dataclass(frozen=True)
class AlertCandidate:
    eligible:bool
    alert_type:str|None
    severity:str|None
    reason_family:str|None
    trigger_reason_codes:tuple[str,...]
    explanation:str
    policy_version:str=POLICY_VERSION

def evaluate_alert_candidate(intelligence:dict)->AlertCandidate:
    decision=intelligence.get('officer_decision') or {};watch=intelligence.get('implementation_watch') or {};trust=intelligence.get('data_trust') or {}
    state=decision.get('review_state');watch_state=watch.get('status');reasons=tuple(sorted(set(decision.get('reason_codes',[])+watch.get('reason_codes',[]))))
    usable=(trust.get('data_status')=='USABLE' or trust.get('summary_state')=='PASS')
    if state=='REVIEW_RECOMMENDED' and usable and watch_state in POLICY['implementation_watch_states']:
        severity=POLICY['severity'][f'{state}:{watch_state}']
        return AlertCandidate(True,'IMPLEMENTATION_PRESSURE',severity,'IMPLEMENTATION',reasons,f'This alert was opened because Implementation Watch is {watch_state} and Officer Decision is REVIEW_RECOMMENDED.')
    if state=='DATA_VERIFICATION_REQUIRED':
        reporting=bool(set(reasons)&{'SOURCE_GAP','REPORT_MONTH_MISSING','REPORT_STALE','STALE_UPDATE'})
        alert_type='REPORTING_GAP' if reporting else 'DATA_VERIFICATION'
        return AlertCandidate(True,alert_type,'ATTENTION','DATA_VERIFICATION',reasons,'This alert was opened because the governed Officer Decision requires verification of project data or source evidence.')
    return AlertCandidate(False,None,None,None,reasons,'No governed Officer Decision is eligible for alert creation.')

def deduplication_key(project_id:str,data_origin:str,alert_type:str,reason_family:str)->str:
    material='|'.join((project_id,data_origin,alert_type,reason_family,POLICY_VERSION))
    return hashlib.sha256(material.encode()).hexdigest()
