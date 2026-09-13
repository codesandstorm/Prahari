from datetime import date
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.schemas import ProjectDetail
from src.decision.governance import ModelReleaseStatus, assess_prediction_eligibility, decide_review
from src.implementation_watch import CufProjectSnapshot, ImplementationWatchEngine
from src.implementation_watch.contracts import Availability, Clearance, LandStatus, Milestone, RowStatus, Tender
from src.implementation_watch.features import (
    clearance_metrics, consecutive_stagnant, financial_physical_divergence,
    financial_progress_gap, land_metrics, milestone_metrics, physical_progress_gap,
    milestone_slippage_trend, row_pending, tender_metrics,
)
from src.implementation_watch.llm_evidence import assistant_evidence
from src.implementation_watch.officer import officer_reason_codes
from src.ml.feature_discovery_v2 import COMPACT_V2
from src.trust.data_trust import DataTrustResult, Dimension

ROOT=Path(__file__).resolve().parents[1]
AS_OF=date(2026,6,1)


def snap(**kwargs):
    base=dict(canonical_project_id='P1',as_of=AS_OF,data_origin='SYNTHETIC_CUF_PROTOTYPE',source_refs=['FIXTURE'],provenance_complete=True)
    base.update(kwargs);return CufProjectSnapshot(**base)


def trust(status='PASS'):
    good=Dimension(status,'X','fixture')
    return DataTrustResult('P1','2026-06',good,good,good,good,good,good,good,good,14,14,14,13,['2026-06'],[],[],[],list(COMPACT_V2),[],status=='PASS',[] if status=='PASS' else ['SOURCE_UNAVAILABLE'])


def test_frozen_compact_v2_exactly_14_features():
    assert COMPACT_V2 == (
        'log_original_cost','planned_duration_months','project_age_months','expenditure_to_cost','physical_progress','physical_progress_missing',
        'history_span_months','remaining_schedule_months','required_future_velocity','progress_vs_elapsed_gap','low_progress_near_deadline','consecutive_stagnant','cumulative_cost_revision_pct','expenditure_velocity',
    )


def test_cuf_registry_complete_and_official_hash_frozen():
    registry=json.loads((ROOT/'config'/'cuf_field_registry.json').read_text(encoding='utf-8'))
    assert registry['official_document']['sha256']=='c058929cc4f19dab8df2e1527419a865036080996f60cf976da9e55a547d4412'
    required={'official_field_name','official_section','official_definition','official_source_reference','prahari_canonical_name','historical_dataset_column','historical_data_type','historical_unit','current_coverage','missingness_rate','project_coverage','month_coverage','structured_status','available_at_anchor_t','predictive_use_allowed','implementation_watch_use_allowed','data_trust_use_allowed','derived_features','historical_availability_state','future_paimana_support','notes'}
    assert len(registry['fields'])>=35
    assert all(required <= set(item) for item in registry['fields'])
    assert {'AVAILABLE_CURRENTLY','CUF_AVAILABLE_NOT_IN_HISTORICAL_DATA','UNSAFE_FOR_PREDICTION','STRUCTURALLY_UNAVAILABLE'} <= {x['structured_status'] for x in registry['fields']}


def test_gap_features_and_semantic_guard():
    assert physical_progress_gap(55,72).value==-17
    assert physical_progress_gap(None,72).availability==Availability.UNREPORTED
    assert financial_progress_gap(55,72,semantics_compatible=True).value==-17
    assert financial_progress_gap(55,72,semantics_compatible=False).note=='SEMANTIC_MISMATCH'
    assert financial_physical_divergence(73,55,semantics_compatible=True).value==18


def test_stagnation_is_calendar_safe_and_gap_breaks():
    a=Availability.AVAILABLE
    assert consecutive_stagnant([('2026-04',50,a),('2026-05',50,a),('2026-06',50,a)]).value==2
    assert consecutive_stagnant([('2026-03',50,a),('2026-05',50,a),('2026-06',50,a)]).value==1
    assert consecutive_stagnant([('2026-04',50,a),('2026-05',None,Availability.SOURCE_GAP),('2026-06',50,a)]).value==0


def test_milestone_overdue_future_and_applicability():
    metrics=milestone_metrics([Milestone(label='M1',planned_date=date(2026,5,1)),Milestone(label='future',planned_date=date(2026,7,1))],AS_OF)
    assert metrics['delayed_count'].value==1 and metrics['max_delay_days'].value==31
    assert milestone_metrics([Milestone(label='NA',applicable=False)],AS_OF)['delayed_count'].availability==Availability.NOT_APPLICABLE
    assert milestone_metrics(None,AS_OF)['delayed_count'].availability==Availability.STRUCTURALLY_UNAVAILABLE
    assert milestone_metrics([],AS_OF)['delayed_count'].availability==Availability.UNREPORTED
    assert milestone_metrics([Milestone(label='future actual',planned_date=date(2026,5,1),actual_date=date(2026,8,1))],AS_OF)['max_delay_days'].value==31
    assert milestone_slippage_trend(50,20,observations_compatible=True).value==30
    assert milestone_slippage_trend(50,20,observations_compatible=True,source_gap=True).availability==Availability.SOURCE_GAP


def test_land_row_clearance_and_tender_rules():
    land=land_metrics(LandStatus(applicable=True,required=100,acquired=76,acquisition_complete=False,expected_completion_date=date(2026,8,1)),AS_OF,date(2026,7,1))
    assert land['remaining_pct'].value==24 and land['deadline_conflict'].value is True
    assert row_pending(RowStatus(applicable=False)).availability==Availability.NOT_APPLICABLE
    assert row_pending(RowStatus(applicable=True,pending=True)).value is True
    assert row_pending(RowStatus(applicable=True,availability_pct=75)).value is True
    assert clearance_metrics([],frozenset())['pending_count'].availability==Availability.UNREPORTED
    clear=clearance_metrics([Clearance(category='Forest',status='PENDING'),Clearance(category='Unmapped local approval',status='PENDING')],frozenset({'FOREST'}))
    assert clear['pending_count'].value==2 and clear['critical_pending'].value is True
    tender=tender_metrics([Tender(publish_date=date(2026,1,1),expected_award_date=date(2026,3,1))],AS_OF)
    assert tender['active'].value is True and tender['delay_count'].value==1 and tender['cycle_days'].value==151
    with pytest.raises(ValidationError):Tender(publish_date=date(2026,2,1),award_date=date(2026,1,1))
    future_award=tender_metrics([Tender(publish_date=date(2026,1,1),award_date=date(2026,8,1))],AS_OF)
    assert future_award['active'].value is True  # future actual is unavailable at this anchor
    assert tender_metrics([],AS_OF)['active'].availability==Availability.UNREPORTED


def test_versioned_policy_and_reason_registry_match_code():
    from src.implementation_watch.engine import SIGNAL_META
    from src.implementation_watch import policy
    reasons=json.loads((ROOT/'config'/'implementation_watch_reason_codes.json').read_text())['codes']
    assert set(reasons)==set(SIGNAL_META)
    configured=json.loads((ROOT/'config'/'implementation_watch_policy.json').read_text())
    assert configured['high_required_future_pace_pp_per_month']==policy.HIGH_REQUIRED_FUTURE_PACE_PP_PER_MONTH
    assert configured['critical_clearance_categories']==sorted(policy.CRITICAL_CLEARANCE_CATEGORIES)


def test_engine_states_reason_serialization_explanations_and_no_causality():
    engine=ImplementationWatchEngine()
    clear=engine.evaluate(snap(scheduled_physical_progress=60,actual_physical_progress=65,scheduled_financial_progress=50,actual_financial_progress=51,financial_progress_semantics_compatible=True,milestones=[],land=LandStatus(applicable=False),right_of_way=RowStatus(applicable=False),clearances=[],tenders=[]))
    assert clear.status=='CLEAR'
    watch=engine.evaluate(snap(scheduled_physical_progress=72,actual_physical_progress=55))
    assert watch.status=='WATCH' and 'PHYSICAL_PROGRESS_BEHIND_PLAN' in watch.reason_codes
    elevated=engine.evaluate(snap(actual_physical_progress=40,required_future_velocity=15,remaining_schedule_months=4,low_progress_near_deadline=True))
    assert elevated.status=='ELEVATED'
    insufficient=engine.evaluate(snap(source_availability=Availability.SOURCE_GAP,report_month_missing=True,provenance_complete=False),data_trust=trust('FAIL'))
    assert insufficient.status=='DATA_INSUFFICIENT'
    payload=elevated.model_dump(mode='json');json.dumps(payload)
    text=' '.join(x.plain_language_explanation.lower() for x in elevated.signals)
    assert not any(word in text for word in (' caused ','fraud','corruption','contractor caused'))
    assert all(x.causal_claim is False and x.technical_explanation['formula'] for x in elevated.signals)


def test_trend_does_not_infer_from_one_observation():
    engine=ImplementationWatchEngine();first=engine.evaluate(snap(scheduled_physical_progress=70,actual_physical_progress=50))
    assert first.trend=='NEW'
    second=engine.evaluate(snap(scheduled_physical_progress=70,actual_physical_progress=72,milestones=[],land=LandStatus(applicable=False),right_of_way=RowStatus(applicable=False),clearances=[],tenders=[]),previous=first)
    assert second.trend=='RESOLVED'


def test_data_trust_and_officer_boundary_no_alert():
    engine=ImplementationWatchEngine();watch=engine.evaluate(snap(actual_physical_progress=50,required_future_velocity=8))
    t=trust();elig=assess_prediction_eligibility(t,ModelReleaseStatus())
    decision=decide_review(trust=t,eligibility=elig,implementation_watch=watch.model_dump(mode='json'))
    assert decision.review_state=='REVIEW_RECOMMENDED'
    assert decision.reason_codes==['IMPLEMENTATION_PRESSURE_SIGNAL']
    assert decision.alert_status=='NOT_ELIGIBLE' and decision.alert_deduplication_key is None
    assert officer_reason_codes(watch)==['IMPLEMENTATION_PRESSURE_SIGNAL','DATA_VERIFICATION_REQUIRED']  # structural limitations remain visible


def test_llm_evidence_is_lossless_and_cannot_override():
    result=ImplementationWatchEngine().evaluate(snap(scheduled_physical_progress=72,actual_physical_progress=55))
    evidence=assistant_evidence(result)
    assert evidence['status']==result.status and evidence['signals'][0]['causal_claim'] is False
    assert 'probability' not in evidence and 'risk_band' not in evidence


def test_backend_schema_represents_withheld_predictions_beside_elevated_watch():
    payload={
        'canonical_project_id':'P1','project_code':None,'canonical_name':'Project','agency':None,'ministry':None,'sector':None,'state':None,'latest_reporting_month':AS_OF,
        'prediction':None,'identity_method':'EXACT','identity_status':'RESOLVED_EXACT','latest_snapshot':None,'data_trust':{'data_status':'USABLE'},'model_release':{'status':'WITHHELD'},'prediction_eligibility':{'prediction_eligible':False},'officer_decision':{'review_state':'REVIEW_RECOMMENDED'},'implementation_watch':{'status':'ELEVATED'}
    }
    assert ProjectDetail.model_validate(payload).implementation_watch['status']=='ELEVATED'


def test_future_payload_validation_and_origin_separation():
    with pytest.raises(ValidationError):snap(actual_physical_progress=101)
    assert snap(data_origin='SYNTHETIC_CUF_PROTOTYPE').data_origin=='SYNTHETIC_CUF_PROTOTYPE'
    assert snap(data_origin='PAIMANA_CUF',right_of_way=RowStatus(applicable=True,pending=None)).right_of_way.pending is None
