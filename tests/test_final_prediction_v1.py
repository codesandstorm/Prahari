import csv
from pathlib import Path
import joblib, math
import numpy as np
from src.ml.final_prediction import COMPACT_V2, build_compact_v2, build_target, reliability
from src.ml.prediction_service import FrozenPredictionService

ROOT=Path(__file__).resolve().parents[1]
def row(month, revised='', progress='20', status='ONGOING', identity='RESOLVED_EXACT'):
    return {'canonical_project_id':'P1','reporting_month':month,'identity_status':identity,'original_target_doc_raw':'12/2026','revised_doc_raw':revised,'approval_date_raw':'01/2024','original_cost_raw':'100','revised_cost_raw':'','cumulative_expenditure_raw':'20','physical_progress_raw':progress,'project_status_raw':status}
def test_compact_order_and_calendar_gap():
    f=build_compact_v2([row('2025-01','',progress='10'),row('2025-03','',progress='20')])
    assert tuple(f)==COMPACT_V2 and math.isnan(f['expenditure_velocity']) and f['consecutive_stagnant']==0
def test_s1_and_s2_are_separate_and_future_presence_required():
    cov={f'2025-0{x}':'PROJECT_LEVEL' for x in range(1,7)}
    rows=[row('2025-01'),row('2025-02'),row('2025-03','01/2027'),row('2025-04','01/2027'),row('2025-05','02/2027')]
    s1,ledger,_=build_target(rows,cov,'S1');s2,_,_=build_target(rows,cov,'S2')
    assert any(r['event']==1 for r in s1)
    assert all(r['target']=='S1' for r in s1) and all(r['target']=='S2' for r in s2)
    assert any(r['status']=='CENSORED' for r in ledger)
def test_s1_downward_correction_does_not_lower_event_baseline():
    cov={f'2025-0{x}':'PROJECT_LEVEL' for x in range(1,7)}
    rows=[row('2025-01'),row('2025-02','11/2026'),row('2025-03',''),row('2025-04',''),row('2025-05','')]
    cohort,_,_=build_target(rows,cov,'S1')
    anchor=next(r for r in cohort if r['anchor_month']=='2025-02')
    assert anchor['event']==0
def test_identity_completion_and_missing_source_fail_closed():
    cov={f'2025-0{x}':'PROJECT_LEVEL' for x in range(1,7)}; rows=[row('2025-01'),row('2025-02',identity='AMBIGUOUS'),row('2025-03'),row('2025-04'),row('2025-05')]
    _,ledger,_=build_target(rows,cov,'S1'); assert any('IDENTITY_NOT_EXACT' in r['reasons'] for r in ledger)
    rows[1]['identity_status']='RESOLVED_EXACT';rows[1]['physical_progress_raw']='100'
    _,ledger,_=build_target(rows,cov,'S1');assert any('COMPLETED_AT_T' in r['reasons'] for r in ledger)
def test_artifacts_reload_and_inference_withholds_probability():
    for target in ('s1','s2'):
        path=ROOT/'models/prediction'/target/'v1/pipeline.joblib'
        a=joblib.load(path);b=joblib.load(path);assert tuple(a['features'])==COMPACT_V2
        probe=np.ones((1,len(COMPACT_V2)))
        assert np.array_equal(a['model'].predict_proba(probe),b['model'].predict_proba(probe))
    service=FrozenPredictionService(ROOT);result=service.predict([row('2026-05'),row('2026-06')],'2026-06','S1')
    assert result.prediction_status=='WITHHELD' and result.probability is None and result.risk_band is None
def test_reliability_is_probability_independent():
    f={n:1.0 for n in COMPACT_V2};f['history_span_months']=12
    assert reliability(f,'RESOLVED_EXACT',True)[0]=='WITHHELD'

def test_backend_adapter_preserves_fail_closed_contract():
    from backend.prediction import FrozenModelPredictionProvider
    result=FrozenModelPredictionProvider(ROOT).predict([row('2026-05'),row('2026-06')],'2026-06','S1')
    assert result['prediction_status']=='WITHHELD' and result['probability'] is None
