from src.decision.governance import ModelReleaseStatus,alert_deduplication_key,assess_prediction_eligibility,decide_review
from test_data_trust_v1 import evaluator,months

def trusted():
    history=months(18);return evaluator().evaluate(history,history[-1]['reporting_month'])
def test_model_pending_is_not_bad_data_and_has_nullable_priority():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus());decision=decide_review(trust=trust,eligibility=eligibility);assert trust.data_usable and decision.review_state=='PREDICTION_WITHHELD' and decision.priority is None and decision.reason_codes==['MODEL_RELEASE_PENDING']
def test_data_failure_routes_to_verification_without_fake_risk():
    history=months(3);trust=evaluator().evaluate(history,history[-1]['reporting_month']);decision=decide_review(trust=trust,eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus()));assert decision.review_state=='DATA_VERIFICATION_REQUIRED' and 'INSUFFICIENT_HISTORY' in decision.reason_codes and decision.alert_status=='NOT_ELIGIBLE'
def test_released_high_signal_routes_to_review_but_does_not_create_alert():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus('RELEASED',()));prediction={'prediction_status':'AVAILABLE','target':'S1','risk_band':'HIGH','probability':.8,'reliability_band':'HIGH','model_version':'m1'};decision=decide_review(trust=trust,eligibility=eligibility,prediction=prediction,alert_rule_satisfied=True);assert decision.review_state=='REVIEW_RECOMMENDED' and decision.priority is None and decision.alert_status=='ELIGIBLE_NOT_CREATED'
def test_withheld_prediction_cannot_create_risk_review():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus());decision=decide_review(trust=trust,eligibility=eligibility,prediction={'prediction_status':'WITHHELD','target':'S1','risk_band':'HIGH','probability':.99,'reliability_band':'HIGH'});assert decision.review_state=='PREDICTION_WITHHELD' and 'RISK_SIGNAL' not in decision.reason_codes
def test_completed_project_is_normally_excluded():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus(),project_completed=True);decision=decide_review(trust=trust,eligibility=eligibility,project_completed=True);assert decision.review_state=='NO_REVIEW_SIGNAL' and decision.reason_codes==['COMPLETED_PROJECT']
def test_alert_deduplication_blocks_duplicate_unresolved_situation():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus('RELEASED',()));prediction={'prediction_status':'AVAILABLE','target':'S1','risk_band':'HIGH','reliability_band':'HIGH','model_version':'m1'};key=alert_deduplication_key('P1','S1','m1','ELEVATED_PREDICTIVE_SIGNAL',trust.as_of_month);decision=decide_review(trust=trust,eligibility=eligibility,prediction=prediction,alert_rule_satisfied=True,existing_unresolved_alert_keys={key});assert decision.alert_status=='NOT_ELIGIBLE'
def test_frontend_serialization_has_separate_concepts():
    trust=trusted();eligibility=assess_prediction_eligibility(trust,ModelReleaseStatus());data=decide_review(trust=trust,eligibility=eligibility).to_dict();assert {'review_state','priority','prediction_status','reliability','reason_codes','alert_status'}<=set(data)
