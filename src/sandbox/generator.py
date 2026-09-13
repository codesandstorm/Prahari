"""Deterministic generator for isolated CUF-style demonstration evidence."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

DATA_ORIGIN = "SYNTHETIC_CUF_PROTOTYPE"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config" / "synthetic_scenario_registry.json"
OUTPUT = ROOT / "data" / "synthetic" / "cuf_sandbox_v1"


def add_month(month: str, offset: int) -> str:
    year, mon = map(int, month.split("-")); index = year * 12 + mon - 1 + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def _fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        digest.update(path.name.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def generate_sandbox(output: Path = OUTPUT) -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8")); rng = random.Random(registry["seed"])
    output.mkdir(parents=True, exist_ok=True)
    scenarios = list(registry["scenarios"])
    sectors = ["ROADS", "RAILWAYS", "POWER", "URBAN_DEVELOPMENT", "CIVIL_AVIATION"]
    agencies = ["SYNTHETIC_IMPLEMENTING_AGENCY_A", "SYNTHETIC_IMPLEMENTING_AGENCY_B", "SYNTHETIC_IMPLEMENTING_AGENCY_C"]
    masters=[]; months=[]; milestones=[]; lands=[]; rows=[]; clearances=[]; tenders=[]; funding=[]; catalog=[]
    count=registry["portfolio_project_count"]; curated=registry["curated_project_count"]
    start=registry["start_month"]
    for n in range(count):
        pid=f"SYN-CUF-{n+1:04d}"; scenario=scenarios[n % len(scenarios)] if n < curated else rng.choice(scenarios)
        original_cost=round(rng.uniform(100,7000),2); revised_factor=1 + (0.18 if scenario in {"MULTI_PRESSURE_PROJECT","FINANCIAL_PHYSICAL_DIVERGENCE"} else rng.uniform(0,.08))
        approval=date(2024,1,1)-timedelta(days=30*rng.randint(0,24)); completion=date(2026,6,1)+timedelta(days=30*rng.randint(-3,18))
        source_refs=[] if scenario=="POOR_PROVENANCE" else [f"SYN-SRC-{pid}"]
        masters.append({"canonical_project_id":pid,"project_name":f"Synthetic CUF Demonstration Project {n+1:04d}","sector":sectors[n%len(sectors)],"ministry":"SYNTHETIC_MINISTRY","agency":agencies[n%len(agencies)],"location":f"SYNTHETIC_STATE_{n%12+1:02d}","scenario_id":scenario,"curated_fixture":str(n<curated).upper(),"data_origin":DATA_ORIGIN,"synthetic_dataset_version":registry["registry_version"],"seed":registry["seed"]})
        if n < curated:
            catalog.append({"canonical_project_id":pid,"scenario_id":scenario,"description":registry["scenarios"][scenario],"expected_watch_status":_expected_status(scenario),"data_origin":DATA_ORIGIN})
        stagnant_base=round(rng.uniform(35,65),1)
        for i in range(registry["months"]):
            month=add_month(start,i); scheduled=min(100,round((i+1)*100/24,1)); actual=max(0,min(100,round(scheduled+rng.uniform(-3,3),1)))
            scheduled_fin=scheduled; actual_fin=max(0,min(100,round(actual+rng.uniform(-3,3),1)))
            if scenario=="PHYSICAL_PROGRESS_LAG": actual=max(0,scheduled-18)
            if scenario=="PHYSICAL_STAGNATION" and i>=21: actual=stagnant_base
            if scenario=="HIGH_REQUIRED_FUTURE_VELOCITY" and i==23: actual=55
            if scenario=="FINANCIAL_BEHIND_PLAN": actual_fin=max(0,scheduled_fin-20)
            if scenario=="FINANCIAL_PHYSICAL_DIVERGENCE" and i==23: actual=70; actual_fin=95
            if scenario=="RECOVERY_AFTER_STAGNATION" and 16<=i<=19: actual=55
            if scenario=="RECOVERY_AFTER_STAGNATION" and i>19: actual=min(100,55+(i-19)*12)
            if scenario=="IMPROVING_PROJECT": actual=60 if i==22 else 100 if i==23 else max(0,min(100,scheduled-(15 if i<12 else max(0,24-i))))
            if scenario=="MULTI_PRESSURE_PROJECT" and i==23: actual=42; actual_fin=25
            source_availability="SOURCE_GAP" if scenario in {"REPORTING_GAP","DATA_INSUFFICIENT_PROJECT"} and i==23 else "AVAILABLE"
            if scenario=="DATA_INSUFFICIENT_PROJECT" and i==23: actual=""; scheduled=""; actual_fin=""; scheduled_fin=""
            current_cost=round(original_cost*revised_factor,2); expenditure=round(current_cost*(float(actual_fin) if actual_fin!="" else 0)/100,2)
            months.append({"canonical_project_id":pid,"reporting_month":month,"scheduled_physical_progress":scheduled,"actual_physical_progress":actual,"scheduled_financial_progress":scheduled_fin,"actual_financial_progress":actual_fin,"original_cost":original_cost,"current_cost":current_cost,"cumulative_expenditure":expenditure,"approval_date":approval.isoformat(),"original_completion_date":"2026-06-01","revised_completion_date":completion.isoformat(),"remaining_schedule_months":4 if scenario in {"HIGH_REQUIRED_FUTURE_VELOCITY","MULTI_PRESSURE_PROJECT"} and i==23 else max(0,23-i),"required_future_velocity":11.25 if scenario=="HIGH_REQUIRED_FUTURE_VELOCITY" and i==23 else 14.5 if scenario=="MULTI_PRESSURE_PROJECT" and i==23 else round((100-float(actual))/max(1,23-i),3) if actual!="" else "","report_stale":str(scenario=="STALE_REPORTING" and i==23).upper(),"source_availability":source_availability,"provenance_complete":str(bool(source_refs)).upper(),"source_ref":"|".join(source_refs),"scenario_id":scenario,"data_origin":DATA_ORIGIN,"synthetic_dataset_version":registry["registry_version"]})
        anchor="2026-06"
        delayed=scenario in {"MILESTONE_DELAY","MULTIPLE_MILESTONE_DELAYS","WORSENING_MILESTONE_SLIPPAGE","MULTI_PRESSURE_PROJECT"}
        for j in range(2 if scenario in {"MULTIPLE_MILESTONE_DELAYS","MULTI_PRESSURE_PROJECT"} else 1):
            milestones.append({"canonical_project_id":pid,"reporting_month":anchor,"milestone_id":f"{pid}-M{j+1}","label":f"Synthetic milestone {j+1}","family":"COMMISSIONING","applicable":"TRUE","planned_date":("2025-12-01" if delayed else "2026-12-01"),"actual_date":"","scenario_id":scenario,"data_origin":DATA_ORIGIN})
        land_pending=scenario in {"LAND_ACQUISITION_PENDING","LAND_DEADLINE_CONFLICT","MULTI_PRESSURE_PROJECT"}
        lands.append({"canonical_project_id":pid,"reporting_month":anchor,"applicable":"TRUE","required":100,"acquired":65 if land_pending else 100,"remaining_pct":35 if land_pending else 0,"acquisition_complete":str(not land_pending).upper(),"expected_completion_date":"2027-01-01" if scenario=="LAND_DEADLINE_CONFLICT" else "2026-05-01","scenario_id":scenario,"data_origin":DATA_ORIGIN})
        rows.append({"canonical_project_id":pid,"reporting_month":anchor,"applicable":"TRUE","pending":str(scenario in {"ROW_PENDING","MULTI_PRESSURE_PROJECT"}).upper(),"availability_pct":70 if scenario in {"ROW_PENDING","MULTI_PRESSURE_PROJECT"} else 100,"scenario_id":scenario,"data_origin":DATA_ORIGIN})
        clearance_count=2 if scenario in {"MULTIPLE_CLEARANCES_PENDING","MULTI_PRESSURE_PROJECT"} else 1
        for j in range(clearance_count):
            clearances.append({"canonical_project_id":pid,"reporting_month":anchor,"clearance_id":f"{pid}-C{j+1}","category":"FOREST" if j==0 else "ENVIRONMENTAL","applicable":"TRUE","status":"PENDING" if scenario in {"CLEARANCE_PENDING","MULTIPLE_CLEARANCES_PENDING","MULTI_PRESSURE_PROJECT"} else "APPROVED","due_date":"2026-03-01","scenario_id":scenario,"data_origin":DATA_ORIGIN})
        tender_pending=scenario in {"TENDER_AWARD_PENDING","PROLONGED_TENDER_CYCLE","MULTI_PRESSURE_PROJECT"}
        tenders.append({"canonical_project_id":pid,"reporting_month":anchor,"tender_id":f"{pid}-T1","applicable":"TRUE","publish_date":"2025-12-01" if scenario=="PROLONGED_TENDER_CYCLE" else "2026-05-01","award_date":"" if tender_pending else "2026-05-20","expected_award_date":"2026-05-15","scenario_id":scenario,"data_origin":DATA_ORIGIN})
        funding.append({"canonical_project_id":pid,"reporting_month":anchor,"total_project_cost":round(original_cost*revised_factor,2),"total_funding":round(original_cost*revised_factor,2),"central_support":round(original_cost*.6,2),"state_support":round(original_cost*.4,2),"scenario_id":scenario,"data_origin":DATA_ORIGIN})
    files={
        "project_master.csv":(masters,list(masters[0])),"project_month.csv":(months,list(months[0])),"milestones.csv":(milestones,list(milestones[0])),"land.csv":(lands,list(lands[0])),"row.csv":(rows,list(rows[0])),"clearances.csv":(clearances,list(clearances[0])),"tenders.csv":(tenders,list(tenders[0])),"funding.csv":(funding,list(funding[0])),"scenario_catalog.csv":(catalog,list(catalog[0])),
    }
    paths=[]
    for name,(items,fields) in files.items():
        path=output/name; _write_csv(path,items,fields); paths.append(path)
    invalid = {
        "data_origin": DATA_ORIGIN, "fixture_purpose": "VALIDATOR_TEST_ONLY", "excluded_from_portfolio": True,
        "cases": [
            {"case":"NEGATIVE_PROGRESS","actual_physical_progress":-1}, {"case":"PROGRESS_ABOVE_100","actual_physical_progress":101},
            {"case":"LAND_REMAINING_ABOVE_100","remaining_pct":110}, {"case":"FUTURE_ACTUAL_MILESTONE_AT_PAST_ANCHOR","actual_date":"2027-01-01","as_of":"2026-06-01"},
            {"case":"TENDER_AWARD_BEFORE_PUBLICATION","publish_date":"2026-05-01","award_date":"2026-04-01"}, {"case":"MISSING_APPLICABILITY","applicable":None},
            {"case":"INVALID_DATE_CHRONOLOGY","approval_date":"2026-07-01","completion_date":"2026-06-01"}, {"case":"DECREASING_CUMULATIVE_EXPENDITURE","prior":100,"current":90},
            {"case":"DUPLICATE_MILESTONE_IDS","milestone_ids":["M1","M1"]}, {"case":"UNKNOWN_CLEARANCE_CATEGORY","category":"UNMAPPED_TEST_CATEGORY"},
            {"case":"SOURCE_GAP","source_availability":"SOURCE_GAP"}
        ]
    }
    invalid_path=output/"invalid_validation_fixtures.json"; invalid_path.write_text(json.dumps(invalid,indent=2)+"\n",encoding="utf-8"); paths.append(invalid_path)
    fingerprint=_fingerprint(paths)
    metadata={"data_origin":DATA_ORIGIN,"synthetic_dataset_version":registry["registry_version"],"generator_version":registry["generator_version"],"seed":registry["seed"],"generated_at":registry["generated_at"],"project_count":count,"curated_project_count":curated,"project_month_count":len(months),"dataset_fingerprint_sha256":fingerprint,"files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
    (output/"generation_metadata.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return metadata


def _expected_status(scenario: str) -> str:
    if scenario in {"REPORTING_GAP","POOR_PROVENANCE","DATA_INSUFFICIENT_PROJECT"}: return "DATA_INSUFFICIENT"
    if scenario in {"HEALTHY_ON_TRACK","STALE_REPORTING","RECOVERY_AFTER_STAGNATION","IMPROVING_PROJECT"}: return "CLEAR"
    if scenario in {"PHYSICAL_PROGRESS_LAG","PHYSICAL_STAGNATION","HIGH_REQUIRED_FUTURE_VELOCITY","FINANCIAL_PHYSICAL_DIVERGENCE","MILESTONE_DELAY","MULTIPLE_MILESTONE_DELAYS","WORSENING_MILESTONE_SLIPPAGE","LAND_ACQUISITION_PENDING","LAND_DEADLINE_CONFLICT","CLEARANCE_PENDING","MULTIPLE_CLEARANCES_PENDING","MULTI_PRESSURE_PROJECT"}: return "ELEVATED"
    return "WATCH"


if __name__ == "__main__":
    print(json.dumps(generate_sandbox(), indent=2))
