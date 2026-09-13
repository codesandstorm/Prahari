"""Generate deterministic CUF/Implementation Watch V1 availability artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.implementation_watch import CufProjectSnapshot, ImplementationWatchEngine
from src.implementation_watch.contracts import Availability, Clearance, LandStatus, Milestone, RowStatus, Tender

REGISTRY=ROOT/'config'/'cuf_field_registry.json'
DATASET=ROOT/'data'/'processed'/'longitudinal_2023_07_2026_06_mixed'/'project_month.csv'


def write_csv(path:Path,rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]) if rows else []
    with path.open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)


def samples():
    engine=ImplementationWatchEngine();as_of=__import__('datetime').date(2026,6,1)
    cases={
        'clear':CufProjectSnapshot(canonical_project_id='SYN-CLEAR',as_of=as_of,data_origin='SYNTHETIC_CUF_PROTOTYPE',source_refs=['SYNTHETIC_FIXTURE'],provenance_complete=True,scheduled_physical_progress=70,actual_physical_progress=72,scheduled_financial_progress=65,actual_financial_progress=66,financial_progress_semantics_compatible=True,milestones=[Milestone(label='Not applicable',applicable=False)],land=LandStatus(applicable=False),right_of_way=RowStatus(applicable=False),clearances=[Clearance(category='Not applicable',applicable=False)],tenders=[Tender(applicable=False)]),
        'watch':CufProjectSnapshot(canonical_project_id='SYN-WATCH',as_of=as_of,data_origin='SYNTHETIC_CUF_PROTOTYPE',source_refs=['SYNTHETIC_FIXTURE'],provenance_complete=True,scheduled_physical_progress=70,actual_physical_progress=55,financial_progress_semantics_compatible=False,milestones=[Milestone(label='Not applicable',applicable=False)],land=LandStatus(applicable=False),right_of_way=RowStatus(applicable=False),clearances=[Clearance(category='Not applicable',applicable=False)],tenders=[Tender(applicable=False)]),
        'elevated':CufProjectSnapshot(canonical_project_id='SYN-ELEVATED',as_of=as_of,data_origin='SYNTHETIC_CUF_PROTOTYPE',source_refs=['SYNTHETIC_FIXTURE'],provenance_complete=True,scheduled_physical_progress=70,actual_physical_progress=45,remaining_schedule_months=4,required_future_velocity=13.75,low_progress_near_deadline=True,milestones=[Milestone(label='Tender award',family='TENDER_AWARD',planned_date=__import__('datetime').date(2025,12,1))],land=LandStatus(applicable=True,remaining_pct=30,acquisition_complete=False,expected_completion_date=__import__('datetime').date(2026,12,1)),right_of_way=RowStatus(applicable=True,pending=True),clearances=[Clearance(category='Forest',status='PENDING'),Clearance(category='Other X',status='PENDING')],tenders=[Tender(tender_id='T1',publish_date=__import__('datetime').date(2025,10,1),expected_award_date=__import__('datetime').date(2026,1,1))]),
        'data_insufficient':CufProjectSnapshot(canonical_project_id='SYN-INSUFFICIENT',as_of=as_of,data_origin='SYNTHETIC_CUF_PROTOTYPE',source_availability=Availability.SOURCE_GAP,report_month_missing=True,provenance_complete=False),
    }
    return {name:engine.evaluate(case).model_dump(mode='json') for name,case in cases.items()}


def main():
    registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
    with DATASET.open(encoding='utf-8-sig',newline='') as handle:dataset_rows=list(csv.DictReader(handle))
    all_projects={row['canonical_project_id'] for row in dataset_rows};all_months={row['reporting_month'] for row in dataset_rows}
    def present(row,columns):return any((row.get(column) or '').strip() not in {'','-','NA','N/A'} for column in columns)
    for item in registry['fields']:
        mapping=item.get('historical_dataset_column')
        if item.get('current_coverage') is None or not mapping:continue
        columns=[column.strip() for column in mapping.split('|')]
        if any(column not in dataset_rows[0] for column in columns):continue
        observed=[row for row in dataset_rows if present(row,columns)]
        measured=(len(observed)/len(dataset_rows),len({row['canonical_project_id'] for row in observed})/len(all_projects),len({row['reporting_month'] for row in observed})/len(all_months))
        recorded=(item['current_coverage'],item['project_coverage'],item['month_coverage'])
        if any(abs(a-b)>0.000001 for a,b in zip(measured,recorded)):
            raise ValueError(f"coverage registry drift for {item['official_field_name']}: measured={measured}, recorded={recorded}")
    availability=[]
    for item in registry['fields']:
        availability.append({key:item.get(key) for key in ('official_field_name','official_section','prahari_canonical_name','historical_dataset_column','current_coverage','missingness_rate','project_coverage','month_coverage','structured_status','historical_availability_state','future_paimana_support')})
    write_csv(ROOT/'outputs'/'cuf'/'cuf_field_availability.csv',availability)
    readiness=[]
    for item in registry['fields']:
        for feature in item['derived_features']:
            readiness.append({'feature':feature,'source_field':item['prahari_canonical_name'],'current_status':'IMPLEMENTABLE_NOW' if item['implementation_watch_use_allowed'] and item['structured_status'] in {'AVAILABLE_CURRENTLY','DERIVABLE_CURRENTLY'} else 'FUTURE_CUF_ONLY','predictive_use_allowed':item['predictive_use_allowed'],'watch_use_allowed':item['implementation_watch_use_allowed'],'historical_availability_state':item['historical_availability_state']})
    write_csv(ROOT/'outputs'/'cuf'/'cuf_feature_readiness.csv',readiness)
    family_rows=[
        {'family':'EXECUTION','current_compute_state':'PARTIAL','current_inputs':'actual physical progress; approved schedule dates','unavailable_inputs':'scheduled physical plan','historical_schema':'MIXED'},
        {'family':'FINANCIAL','current_compute_state':'PARTIAL','current_inputs':'cumulative expenditure','unavailable_inputs':'compatible scheduled/actual financial percentages','historical_schema':'MIXED'},
        {'family':'MILESTONE','current_compute_state':'STRUCTURALLY_UNAVAILABLE','current_inputs':'unstructured milestones_raw retained','unavailable_inputs':'typed milestone dates/status/cost','historical_schema':'UNSTRUCTURED'},
        {'family':'LAND','current_compute_state':'STRUCTURALLY_UNAVAILABLE','current_inputs':'','unavailable_inputs':'structured land details','historical_schema':'ABSENT'},
        {'family':'ROW','current_compute_state':'STRUCTURALLY_UNAVAILABLE','current_inputs':'','unavailable_inputs':'structured ROW applicability/availability','historical_schema':'ABSENT'},
        {'family':'CLEARANCE','current_compute_state':'STRUCTURALLY_UNAVAILABLE','current_inputs':'','unavailable_inputs':'structured clearance records','historical_schema':'ABSENT'},
        {'family':'PROCUREMENT','current_compute_state':'STRUCTURALLY_UNAVAILABLE','current_inputs':'','unavailable_inputs':'structured tender records','historical_schema':'ABSENT'},
        {'family':'REPORTING','current_compute_state':'AVAILABLE','current_inputs':'report calendar/source coverage/provenance','unavailable_inputs':'','historical_schema':'AVAILABLE'},
        {'family':'DATA_QUALITY','current_compute_state':'AVAILABLE','current_inputs':'Data Trust/source/provenance/feature availability','unavailable_inputs':'','historical_schema':'AVAILABLE'},
    ]
    write_csv(ROOT/'outputs'/'implementation_watch'/'current_signal_coverage.csv',family_rows)
    sample_dir=ROOT/'outputs'/'implementation_watch'/'samples';sample_dir.mkdir(parents=True,exist_ok=True)
    for name,payload in samples().items():(sample_dir/f'{name}_synthetic.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    tracked=[REGISTRY,ROOT/'config'/'implementation_watch_reason_codes.json',ROOT/'config'/'implementation_watch_policy.json',ROOT/'config'/'cuf_experiment_registry.json']
    status={'status':'COMPLETE','policy_version':'implementation-watch-v1.0','official_cuf_sha256':registry['official_document']['sha256'],'historical_dataset_sha256':hashlib.sha256(DATASET.read_bytes()).hexdigest(),'sample_origin':'SYNTHETIC_CUF_PROTOTYPE','predictions_created':0,'registry_hashes':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}}
    (ROOT/'outputs'/'implementation_watch'/'implementation_watch_v1_status.json').write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(status,indent=2))


if __name__=='__main__':main()
