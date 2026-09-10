from src.trust.data_trust import DataTrustEvaluator,enforce_prediction_eligibility,frontend_view
from src.trust.cuf_validation import StructuredInputValidator
from src.decision.governance import ModelReleaseStatus,assess_prediction_eligibility

def row(month,identity='RESOLVED_EXACT',progress='40',source='SRC'):
    return {'canonical_project_id':'P1','reporting_month':month,'identity_status':identity,'identity_method':'EXACT_SOURCE_IDENTIFIER','source_id':source,'source_sha256':'abc','pdf_page_index':'2','source_table':'All Ongoing Projects','schema_family':'PAIMANA','physical_progress_schema_available':'YES','original_target_doc_raw':'12/2027','approval_date_raw':'01/2024','original_cost_raw':'100','cumulative_expenditure_raw':'40','physical_progress_raw':progress,'project_status_raw':'ONGOING'}
def months(n):
    return [row(f"{2025+(i//12):04d}-{i%12+1:02d}") for i in range(n)]
def evaluator(**kw):
    coverage={r['reporting_month']:'PROJECT_LEVEL' for r in months(18)};return DataTrustEvaluator(coverage,{'SRC':{'sha256':'abc'}},**kw)
def test_complete_trust_still_withheld_for_scientific_release():
    history=months(18);r=evaluator().evaluate(history,history[-1]['reporting_month']);eligibility=assess_prediction_eligibility(r,ModelReleaseStatus());assert r.identity.status=='PASS' and r.history.status=='PASS' and r.data_usable and r.data_reason_codes==[];assert not eligibility.prediction_eligible and 'HUMAN_TARGET_VALIDATION_PENDING' in eligibility.reason_codes
def test_complete_trust_is_eligible_only_after_governed_release_gates():
    history=months(18);r=evaluator().evaluate(history,history[-1]['reporting_month']);assert assess_prediction_eligibility(r,ModelReleaseStatus('RELEASED',())).prediction_eligible
def test_exact_and_ambiguous_identity():
    history=months(13);history[-1]['identity_status']='AMBIGUOUS';assert evaluator().evaluate(history,history[-1]['reporting_month']).identity.code=='IDENTITY_UNCERTAIN'
def test_short_history_gap_stale_missing_provenance_and_schema():
    history=months(5);del history[-1]['pdf_page_index'];history[-1]['physical_progress_schema_available']='NO'
    current=evaluator().evaluate(history,history[-1]['reporting_month']);assert current.history.code=='INSUFFICIENT_HISTORY' and current.provenance.code=='PARTIAL_PROVENANCE' and current.schema.code=='SCHEMA_UNSUPPORTED'
    stale=evaluator().evaluate(history,'2025-06');assert stale.freshness.code=='STALE_ONE_OR_MORE_REPORTING_PERIODS' and stale.provenance.code=='PROVENANCE_UNKNOWN'
def test_aggregate_and_missing_source_are_not_synthesized():
    history=months(13);e=evaluator();e.coverage[history[4]['reporting_month']]='AGGREGATE_ONLY';r=e.evaluate(history,history[-1]['reporting_month']);assert r.coverage.code=='SOURCE_INTERVAL_MISSING' and history[4]['reporting_month'] in r.aggregate_only_months
def test_frontend_has_no_numeric_trust_score_and_risk_is_absent():
    history=months(13);view=frontend_view(evaluator().evaluate(history,history[-1]['reporting_month']));assert 'score' not in view and 'risk' not in view and 'prediction' not in view
def test_high_model_score_cannot_override_trust_or_become_low_risk():
    history=months(3);trust=evaluator().evaluate(history,history[-1]['reporting_month']);eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus());guarded=enforce_prediction_eligibility({'prediction_status':'AVAILABLE','probability':0.99,'risk_band':'HIGH'},trust,eligibility);assert guarded['prediction_status']=='WITHHELD' and guarded['probability'] is None and guarded['risk_band'] is None and 'INSUFFICIENT_HISTORY' in guarded['withholding_reason_codes']
def test_governed_input_validation():
    v=StructuredInputValidator();bad=v.validate({'canonical_project_id':'P','reporting_month':'2026-06','physical_progress':120,'approval_date':'2026-01-01','original_completion_date':'2025-01-01'});codes={x['code'] for x in bad['issues']};assert {'FIELD_RANGE_FAIL','DATE_LOGIC_FAIL'}<=codes and bad['status']=='INVALID'
    warning=v.validate({'canonical_project_id':'P','reporting_month':'2026-06','physical_progress':25},{'physical_progress':80});assert warning['status']=='WARNING' and warning['issues'][0]['code']=='TEMPORAL_REVERSAL_WARN'
def test_duplicate_submission_and_milestone_contract():
    v=StructuredInputValidator('future-cuf-governed-v1');r=v.validate({'canonical_project_id':'P','reporting_month':'2026-06','submission_id':'A','milestones':[{'planned':'2026-05-01','revised':'2026-04-01'}]},{'submission_id':'A'});codes={x['code'] for x in r['issues']};assert 'DUPLICATE_SUBMISSION' in codes and 'MILESTONE_SEQUENCE_WARN' in codes
def test_future_input_cost_tender_staleness_and_unknown_contracts():
    v=StructuredInputValidator('future-cuf-governed-v1')
    result=v.validate({'canonical_project_id':'P','reporting_month':'2026-06','original_cost':100,'revised_cost':90,'cumulative_expenditure':110,'tender_publish_date':'2026-05-02','tender_award_date':'2026-05-01','update_date':'2026-04-30','status':'COMPLETED','physical_progress':80})
    codes={x['code'] for x in result['issues']}
    assert {'POSSIBLE_COST_CORRECTION_WARN','COST_EXPENDITURE_PLAUSIBILITY_WARN','MILESTONE_SEQUENCE_FAIL','STALE_UPDATE_TIMESTAMP_WARN','CONTRADICTORY_STATUS_WARN'}<=codes
    assert result['status']=='INVALID'
    unknown=v.validate({'canonical_project_id':'P','reporting_month':'2026-06'})
    assert unknown['status']=='UNKNOWN' and unknown['issues'][0]['code']=='NO_GOVERNED_FIELDS_PRESENT'
