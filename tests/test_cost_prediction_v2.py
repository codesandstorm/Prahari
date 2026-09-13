import math

import pytest
from scripts.run_cost_prediction_v2 import json_safe

from backend.schemas import CostIntelligenceOut
from src.decision.governance import ModelReleaseStatus,decide_multi_risk_review
from llm.schemas.evidence import PrahariEvidence
from src.ml.cost_experiment_v2 import calibration_slope_intercept,cost_folds,platt_apply,platt_fit
from src.ml.cost_prediction_v2 import (COST_BASIC_C1,COST_BASIC_C2,RESEARCH_MODE,build_cost_features,
    build_cost_target,cost_api_payload,normalize_cost,peer_benchmark,unified_risk_profile,withheld_cost_evidence)
from src.ml.prediction_research_v2 import cluster_bootstrap_indices,equal_soft_vote


def row(month,revised="-",anticipated="-",original="100",progress="50",status=""):
    return {"canonical_project_id":"P1","reporting_month":month,"identity_status":"RESOLVED_EXACT","project_name_raw":"Project One",
            "original_cost_raw":original,"revised_cost_raw":revised,"anticipated_cost_raw":anticipated,"cumulative_expenditure_raw":"70",
            "approval_date_raw":"01/2023","original_target_doc_raw":"12/2025","revised_doc_raw":"","physical_progress_raw":progress,
            "reported_original_cost":"","reported_revised_cost":"","reported_cumulative_expenditure":"","reported_approval_date":"",
            "reported_original_target_doc":"","reported_revised_doc":"","reported_physical_progress":"","project_status_raw":status,
            "physical_progress_schema_available":"TRUE","schema_family":"PAIMANA_V1","source_id":"SRC-"+month,"pdf_page_index":"10","source_table":"Table 6"}


def history(future_revised="-",future_anticipated="-"):
    return [row("2024-01"),row("2024-02"),row("2024-03"),row("2024-04",future_revised,future_anticipated),row("2024-05",future_revised,future_anticipated),row("2024-06",future_revised,future_anticipated)]


def coverage(missing=None):
    values={f"2024-{m:02d}":"PROJECT_LEVEL" for m in range(1,7)}
    if missing:values[missing]="MISSING_SOURCE"
    return values


def anchor(ledger,target="C1",month="2024-03"):
    return next(r for r in ledger if r["target"]==target and r["anchor_month"]==month)


def test_cost_units_do_not_shift_decimal_or_confuse_lakh():
    assert normalize_cost("₹ 5,000.25")["value_crore"]==pytest.approx(5000.25)
    assert normalize_cost("100 lakh","EXPLICIT_IN_TEXT")["value_crore"]==pytest.approx(1)
    assert normalize_cost("100 crore","EXPLICIT_IN_TEXT")["value_crore"]==pytest.approx(100)
    with pytest.raises(ValueError):normalize_cost("100","EXPLICIT_IN_TEXT")
    with pytest.raises(ValueError):normalize_cost("100 lakh crore","EXPLICIT_IN_TEXT")
    assert json_safe({"missing":float("nan")})=={"missing":None}


def test_c1_positive_negative_and_anticipated_separation():
    cohort,ledger,_=build_cost_target(history("110"),coverage(),"C1",3)
    assert anchor(ledger)["event"]==1 and anchor(ledger)["event_month"]=="2024-04"
    _,negative,_=build_cost_target(history(),coverage(),"C1",3)
    assert anchor(negative)["event"]==0
    _,anticipated,_=build_cost_target(history("-","150"),coverage(),"C1",3)
    assert anchor(anticipated)["event"]==0 and anchor(anticipated)["anticipated_only_flag"]=="TRUE"


def test_c2_uses_frozen_t_baseline_and_downward_revision_is_not_event():
    rows=history("130");rows[2]["revised_cost_raw"]="120";rows[1]["revised_cost_raw"]="120"
    _,ledger,_=build_cost_target(rows,coverage(),"C2",3)
    item=anchor(ledger,"C2");assert item["frozen_revised_cost_at_t"]==120 and item["event_revised_cost"]==130
    rows=history("110");rows[2]["revised_cost_raw"]="120";rows[1]["revised_cost_raw"]="120"
    _,ledger,_=build_cost_target(rows,coverage(),"C2",3)
    item=anchor(ledger,"C2");assert item["event"] is None and item["status"]=="CENSORED"


def test_gap_disappearance_completion_and_original_correction_fail_closed():
    _,ledger,_=build_cost_target(history("110"),coverage("2024-04"),"C1",3);assert anchor(ledger)["status"]=="CENSORED"
    disappearing=history("110")[:-1];_,ledger,_=build_cost_target(disappearing,coverage(),"C1",3);assert anchor(ledger)["status"]=="CENSORED"
    completed=history("110");completed[2]["physical_progress_raw"]="100";_,ledger,_=build_cost_target(completed,coverage(),"C1",3);assert anchor(ledger)["status"]=="EXCLUDED"
    corrected=history("110");corrected[3]["original_cost_raw"]="105";_,ledger,_=build_cost_target(corrected,coverage(),"C1",3);assert anchor(ledger)["status"]=="CENSORED"
    historical=history("110");historical[1]["original_cost_raw"]="95";_,ledger,_=build_cost_target(historical,coverage(),"C1",3);assert anchor(ledger)["status"]=="CENSORED"


def test_feature_contract_is_target_specific_and_as_of_time_only():
    c1=build_cost_features(history()[:3],"C1");c2rows=history()[:3];c2rows[-1]["revised_cost_raw"]="120";c2=build_cost_features(c2rows,"C2")
    assert tuple(c1)==COST_BASIC_C1 and "current_approved_cost_revision_pct" not in c1
    assert tuple(c2)==COST_BASIC_C2 and c2["current_approved_cost_revision_pct"]==20


def test_peer_api_and_unified_risk_contracts_are_fail_closed():
    assert peer_benchmark({"x":1},[{"x":1}],"x")["status"]=="WITHHELD"
    payload=cost_api_payload(project_id="P1",target="C1",horizon=3,probability=.7,reliability="MODERATE",contributors=[],model_version="m",feature_version="f",as_of="2026-06")
    assert payload["cost_research_override"] and payload["cost_machine_provisional"] and payload["production_release_status"]=="WITHHELD"
    profile=unified_risk_profile({"prediction_status":"AVAILABLE","risk_band":"HIGH"},{**payload,"cost_warning_state":"ELEVATED"},{"data_usable":True})
    assert profile["officer_decision"]["reason_codes"][0]=="MULTI_RISK_SIGNAL" and profile["composite_numeric_score"] is None
    assert ModelReleaseStatus().status=="WITHHELD"


def test_api_officer_and_llm_cost_contracts_preserve_withholding():
    cost_evidence=withheld_cost_evidence(project_id="P1",as_of="2026-06")
    assert CostIntelligenceOut.model_validate(cost_evidence).cost_probability is None
    decision=decide_multi_risk_review({},cost_evidence,data_usable=True)
    assert decision["review_state"]=="PREDICTION_WITHHELD" and decision["composite_probability"] is None
    evidence={"canonical_project_id":"P1","project_name":"One","as_of_month":"2026-06","target":"S1","horizon_months":3,
              "prediction_status":"WITHHELD","calibrated_probability":None,"risk_band":None,"reliability_band":"ABSTAIN",
              "cost_intelligence":cost_evidence}
    assert PrahariEvidence.from_dict(evidence).cost_intelligence["cost_probability"] is None


def test_six_month_target_and_future_values_never_enter_anchor_features():
    rows=history()+[row("2024-07"),row("2024-08"),row("2024-09","140")]
    cover={f"2024-{m:02d}":"PROJECT_LEVEL" for m in range(1,10)}
    _,ledger,_=build_cost_target(rows,cover,"C1",6)
    assert anchor(ledger)["event"]==1 and anchor(ledger)["event_month"]=="2024-09"
    before=build_cost_features(rows[:3],"C1")
    rows[-1]["cumulative_expenditure_raw"]="999999"
    assert build_cost_features(rows[:3],"C1")==before


def test_temporal_fold_maturity_and_support_are_fail_closed():
    cohort=[]
    for i in range(40):
        cohort.append({"canonical_project_id":f"P{i}","anchor_month":"2023-01","event":i<5})
    folds=cost_folds(cohort,3)
    assert all(f["status"]=="DESCRIPTIVE_ONLY" for f in folds)
    assert all(not f["train_end"] or f["train_end"]<f["test_start"] for f in folds)


def test_calibration_is_fit_separately_and_reports_diagnostics():
    y=[0,0,1,1];p=[.1,.2,.7,.8]
    calibrator=platt_fit(y,p);calibrated=platt_apply(calibrator,p)
    assert calibrator is not None and len(calibrated)==4
    diagnostics=calibration_slope_intercept(y,calibrated)
    assert math.isfinite(diagnostics["calibration_slope"])


def test_ensemble_alignment_and_bootstrap_respect_contracts():
    assert list(equal_soft_vote([[.2,.4],[.4,.6]]))==pytest.approx([.3,.5])
    indices=cluster_bootstrap_indices(["A","A","B"],replicates=20)
    assert len(indices)==20
    for sample in indices:
        assert list(sample).count(0)==list(sample).count(1)


def test_ensemble_alignment_and_project_cluster_bootstrap():
    assert equal_soft_vote([[.1,.3],[.3,.5]]).tolist()==pytest.approx([.2,.4])
    samples=cluster_bootstrap_indices(["P1","P1","P2"],replicates=5,seed=1)
    assert all(set(sample.tolist()) in ({0,1},{2},{0,1,2}) for sample in samples)
    assert all((0 in sample)==(1 in sample) for sample in samples)


def test_api_officer_llm_evidence_and_release_remain_governed():
    evidence=withheld_cost_evidence(project_id="P1",as_of="2026-06")
    parsed=CostIntelligenceOut.model_validate(evidence)
    assert parsed.cost_probability is None and parsed.production_release_status=="WITHHELD"
    assert ModelReleaseStatus().status=="WITHHELD" and RESEARCH_MODE=="PROTOTYPE_RESEARCH_OVERRIDE"
    decision=decide_multi_risk_review(None,evidence,data_usable=True)
    assert decision["review_state"]=="PREDICTION_WITHHELD" and decision["composite_probability"] is None
    assert "NO_COST_MODEL_PASSED_RESEARCH_ADMISSION" in evidence["cost_withheld_reasons"]


def test_research_history_does_not_include_reserved_july_2026():
    from pathlib import Path
    data=Path(__file__).parents[1]/"data/processed/longitudinal_2022_08_2026_06_research_v2/project_month.csv"
    if not data.exists():pytest.skip("deterministic local research dataset not materialized")
    import csv
    with data.open(encoding="utf-8-sig",newline="") as handle:
        months={r["reporting_month"] for r in csv.DictReader(handle)}
    assert "2026-07" not in months and max(months)=="2026-06"
