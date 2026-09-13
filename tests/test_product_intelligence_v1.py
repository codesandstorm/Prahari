from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.product_intelligence import synthetic_project_intelligence
from src.benchmarking import BenchmarkMode, BenchmarkRecord, PeerBenchmarkService, cost_band, lifecycle_band
from src.intelligence import IntelligenceMode, build_project_intelligence
from src.sandbox.generator import DATA_ORIGIN, OUTPUT, generate_sandbox
from src.sandbox.repository import SyntheticSandboxRepository

ROOT=Path(__file__).resolve().parents[1]


def _hash_tree(root):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.name!='generation_metadata.json'}


def test_sandbox_generation_is_deterministic(tmp_path):
    one,two=tmp_path/'data'/'synthetic'/'one',tmp_path/'data'/'synthetic'/'two'
    a=generate_sandbox(one);b=generate_sandbox(two)
    assert a['dataset_fingerprint_sha256']==b['dataset_fingerprint_sha256']
    assert _hash_tree(one)==_hash_tree(two)
    assert a['project_count']==1000 and a['project_month_count']==24000 and a['curated_project_count']==120


def test_synthetic_origin_ranges_and_temporal_realism():
    repo=SyntheticSandboxRepository(); rows=repo.months
    assert all(x['data_origin']==DATA_ORIGIN for x in rows)
    assert all(not x['actual_physical_progress'] or 0<=float(x['actual_physical_progress'])<=100 for x in rows)
    by={}
    for row in rows:by.setdefault(row['canonical_project_id'],[]).append(row)
    for history in by.values():
        planned=[float(x['scheduled_physical_progress']) for x in history if x['scheduled_physical_progress']]
        assert planned==sorted(planned)


def test_invalid_fixtures_are_explicitly_excluded():
    fixture=json.loads((OUTPUT/'invalid_validation_fixtures.json').read_text())
    assert fixture['excluded_from_portfolio'] is True and fixture['fixture_purpose']=='VALIDATOR_TEST_ONLY'
    assert {x['case'] for x in fixture['cases']} >= {'NEGATIVE_PROGRESS','PROGRESS_ABOVE_100','DUPLICATE_MILESTONE_IDS','SOURCE_GAP'}
    assert not any(p['canonical_project_id'].startswith('INVALID') for p in SyntheticSandboxRepository().projects)


def test_curated_scenarios_match_governed_watch_results():
    catalog={r['canonical_project_id']:r for r in csv.DictReader((OUTPUT/'scenario_catalog.csv').open())}
    for pid,row in catalog.items(): assert synthetic_project_intelligence(pid).implementation_watch['status']==row['expected_watch_status']
    examples={row['scenario_id']:synthetic_project_intelligence(pid) for pid,row in catalog.items()}
    assert examples['HEALTHY_ON_TRACK'].implementation_watch['status']=='CLEAR'
    assert examples['MULTI_PRESSURE_PROJECT'].implementation_watch['status']=='ELEVATED'
    assert examples['DATA_INSUFFICIENT_PROJECT'].implementation_watch['status']=='DATA_INSUFFICIENT'
    assert examples['IMPROVING_PROJECT'].risk_trend['state']=='IMPROVING'


def _record(i,origin='HISTORICAL_FLASH_REPORT',month='2026-06',sector='ROAD',band='150_TO_500_CR',life='MID',value=None):
    return BenchmarkRecord(f'P{i}',month,origin,sector,band,life,{'required_future_velocity':float(i if value is None else value)})


def test_cost_and_lifecycle_bands_are_transparent():
    assert [cost_band(x) for x in (100,150,500,1000,5000,None)]==['BELOW_150_CR','150_TO_500_CR','500_TO_1000_CR','1000_TO_5000_CR','5000_CR_AND_ABOVE','UNKNOWN']
    assert lifecycle_band(date(2024,1,1),date(2026,1,1),date(2024,6,1))=='EARLY'
    assert lifecycle_band(date(2024,1,1),date(2026,1,1),date(2027,1,1))=='OVERDUE'
    assert lifecycle_band(None,None,date(2026,1,1))=='UNKNOWN'


def test_benchmark_percentiles_fallback_and_minimum_support():
    records=[_record(i) for i in range(40)]; subject=records[0]
    result=PeerBenchmarkService(records).benchmark(subject,BenchmarkMode.REAL_CURRENT)
    metric=next(x for x in result.metrics if x.metric=='required_future_velocity')
    assert result.peer_group_level==1 and result.peer_count==39 and metric.percentile is not None and metric.peer_p25 is not None
    tiny=PeerBenchmarkService(records[:5]).benchmark(records[0],BenchmarkMode.REAL_CURRENT)
    assert tiny.peer_count==0 and all(x.percentile is None for x in tiny.metrics)


def test_historical_benchmark_never_uses_future_records():
    records=[_record(i,month='2025-01') for i in range(20)]+[_record(i+100,month='2026-01',value=999) for i in range(20)]
    result=PeerBenchmarkService(records).benchmark(records[0],BenchmarkMode.REAL_HISTORICAL_AS_OF)
    metric=next(x for x in result.metrics if x.metric=='required_future_velocity')
    assert metric.peer_count==19 and metric.peer_mean<100


def test_real_synthetic_benchmark_boundary_fails_closed():
    real=[_record(i) for i in range(20)]; synthetic=[_record(i+30,origin=DATA_ORIGIN) for i in range(20)]
    service=PeerBenchmarkService(real+synthetic)
    assert service.benchmark(real[0],BenchmarkMode.REAL_CURRENT).data_origin=='HISTORICAL_FLASH_REPORT'
    with pytest.raises(ValueError):service.benchmark(real[0],BenchmarkMode.SYNTHETIC_SANDBOX)


def test_unified_contract_keeps_dimensions_and_withheld_nulls():
    watch={'status':'WATCH','trend':'NEW','reason_codes':['PHYSICAL_PROGRESS_STAGNANT'],'signals':[]}
    obj=build_project_intelligence(mode=IntelligenceMode.REAL_HISTORICAL,identity={'canonical_project_id':'P1'},current_state={},watch=watch,trust={'data_status':'USABLE'},benchmark={},officer_decision={'review_state':'REVIEW_RECOMMENDED','alert_status':'NOT_ELIGIBLE'},evidence=[{'data_origin':'HISTORICAL_FLASH_REPORT'}],provenance={})
    assert obj.schedule_intelligence['probability'] is None and obj.cost_intelligence['risk_band'] is None
    assert 'overall_risk_score' not in obj.model_dump_json()
    assert obj.reliability['prediction_reliability']=='NOT_APPLICABLE'
    with pytest.raises(ValidationError):obj.model_copy(update={'data_origin':DATA_ORIGIN}).model_validate(obj.model_copy(update={'data_origin':DATA_ORIGIN}).model_dump())


def test_synthetic_intelligence_is_frontend_ready_and_never_official():
    obj=synthetic_project_intelligence('SYN-CUF-0001'); data=obj.model_dump(mode='json')
    assert data['mode']=='SYNTHETIC_SANDBOX' and data['data_origin']==DATA_ORIGIN
    assert data['schedule_intelligence']['prediction_status']=='WITHHELD' and data['schedule_intelligence']['probability'] is None
    assert data['cost_intelligence']['prediction_status']=='WITHHELD' and data['cost_intelligence']['probability'] is None
    assert all(x['data_origin']==DATA_ORIGIN and x['table']=='SYNTHETIC_CUF_FIXTURE' for x in data['evidence_summary'])
    assert data['assistant_context']['constraints'] and data['peer_benchmark']['mode']=='SYNTHETIC_SANDBOX'
    assert synthetic_project_intelligence('SYN-CUF-0023').risk_trend['state']=='INSUFFICIENT_HISTORY'


def test_no_synthetic_ids_enter_canonical_real_artifacts():
    for name in ('project_master.csv','report_month.csv'):
        assert 'SYN-CUF-' not in (ROOT/'data'/'processed'/'longitudinal_2023_07_2026_06_mixed'/name).read_text(encoding='utf-8')
