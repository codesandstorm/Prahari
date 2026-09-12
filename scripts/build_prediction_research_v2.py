"""Build immutable-source PRAHARI Prediction Research V2 artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter,defaultdict
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from src.ml.final_prediction import add_month, build_compact_v2
from src.ml.provisional_research import approved_doc,month_index,number
from src.ml.prediction_research_v2 import (
    BASIC_LONG_HISTORY_V1, EXPECTED_COUNTS, HISTORICAL_MONTHS, RECOVERY, V2_VERSION,
    build_basic_long_history, build_research_target, dataset_fingerprint, expanding_folds,
    read_csv, restrict_feature_anchors, rolling_folds, source_path, validate_transfer_rows, write_csv,
)
from src.pipeline.build_mixed_coverage_dataset import discover_table, extract_project_month, sha256

V1=ROOT/"data/processed/longitudinal_2023_07_2026_06_mixed"
DATA=ROOT/"data/processed/longitudinal_2022_08_2026_06_research_v2"
OUT=ROOT/"outputs/ml/prediction_research_v2"
TRANSFER=ROOT/"validation/historical_target_transfer_v2"


def months_between(start: str,end: str):
    result=[]; cursor=start
    while cursor<=end: result.append(cursor); cursor=add_month(cursor,1)
    return result


def stable_pick(rows,n,salt):
    return sorted(rows,key=lambda row:hashlib.sha256(f"{salt}|{row['canonical_project_id']}|{row['anchor_month']}".encode()).hexdigest())[:n]


def make_transfer(target,cohort,ledger,all_rows):
    eligible={(r["canonical_project_id"],r["anchor_month"]):r for r in ledger if r["status"]=="ELIGIBLE"}
    historic=[r for r in cohort if "2022-09"<=r["anchor_month"]<="2023-06"]
    positives=[r for r in historic if int(r["event"])==1]
    negatives=[r for r in historic if int(r["event"])==0]
    ambiguous=[r for r in positives if abs(int(eligible[(r["canonical_project_id"],r["anchor_month"])].get("date_change_months") or 0))>24]
    ambiguous=stable_pick(ambiguous,10,target+"-ambiguous")
    ambiguous_keys={(r["canonical_project_id"],r["anchor_month"]) for r in ambiguous}
    selected=[("MACHINE_POSITIVE",r) for r in stable_pick([r for r in positives if (r["canonical_project_id"],r["anchor_month"]) not in ambiguous_keys],30,target+"-positive")]
    selected += [("MACHINE_NEGATIVE_CONTROL",r) for r in stable_pick(negatives,20,target+"-negative")]
    selected += [("CORRECTION_OR_AMBIGUOUS",r) for r in ambiguous]
    quotas=defaultdict(int)
    for kind,_ in selected: quotas[kind]+=1
    required={"MACHINE_POSITIVE":30,"MACHINE_NEGATIVE_CONTROL":20,"CORRECTION_OR_AMBIGUOUS":10}
    if dict(quotas)!=required: raise RuntimeError(f"{target} transfer sample insufficient: {dict(quotas)}")
    lookup={(r["canonical_project_id"],r["reporting_month"]):r for r in all_rows}
    first_month={}
    for row in all_rows: first_month[row["canonical_project_id"]]=min(first_month.get(row["canonical_project_id"],row["reporting_month"]),row["reporting_month"])
    output=[]
    for review_number,(kind,item) in enumerate(selected,1):
        pid=item["canonical_project_id"]; anchor=item["anchor_month"]; candidate=eligible[(pid,anchor)]
        timeline=[]
        for offset in (-1,0,1,2,3):
            month=add_month(anchor,offset); row=lookup.get((pid,month),{})
            timeline.append({"relative_month":f"T{offset:+d}" if offset else "T","reporting_month":month,
                             "original_completion":row.get("original_target_doc_raw",""),"revised_completion":row.get("revised_doc_raw",""),
                             "anticipated_completion":row.get("anticipated_doc_raw",""),"source_id":row.get("source_id",""),
                             "sha256":row.get("source_sha256",""),"physical_page":row.get("pdf_page_index",""),
                             "printed_page":row.get("printed_page_number","")})
        anchor_row=lookup[(pid,anchor)]
        cost=number(anchor_row.get("original_cost_raw","")); cost_band=("UNKNOWN" if not math.isfinite(cost) else "LT_500" if cost<500 else "500_TO_2000" if cost<2000 else "GE_2000")
        semantics=("REVISED_AND_ANTICIPATED" if anchor_row.get("revised_doc_raw") and anchor_row.get("anticipated_doc_raw") else "REVISED" if anchor_row.get("revised_doc_raw") else "ANTICIPATED" if anchor_row.get("anticipated_doc_raw") else "ORIGINAL_ONLY")
        history_months=month_index(anchor)-month_index(first_month[pid])+1
        history_class="FIRST_APPEARANCE" if history_months==1 else ("LONG_RUNNING" if history_months>=12 else "ESTABLISHED")
        future_dates=[approved_doc(lookup.get((pid,add_month(anchor,offset)),{})) for offset in range(0,4)]
        reversion=any(a and b and b<a for a,b in zip(future_dates,future_dates[1:]))
        warning=[]
        if kind=="CORRECTION_OR_AMBIGUOUS": warning.append("LARGE_DATE_CHANGE_REQUIRES_SOURCE_REVIEW")
        if anchor_row.get("schema_family")=="OCMS": warning.append("HISTORICAL_SCHEMA_TARGET_TRANSFER_PENDING")
        output.append({"review_id":f"HTV2-{target}-{review_number:03d}","sample_stratum":kind,"canonical_project_id":pid,
                       "project_name":anchor_row.get("project_name_raw",""),"target_family":target,"anchor_month":anchor,
                       "period_stratum":"2022_H2" if anchor.startswith("2022-") else "2023_H1","sector_stratum":anchor_row.get("sector_raw") or "STRUCTURALLY_UNAVAILABLE_OCMS",
                       "cost_band":cost_band,"date_semantics_stratum":semantics,"history_stratum":history_class,"reversion_flag":str(reversion).upper(),
                       "change_band":"LARGE_GT_24M" if abs(int(candidate.get("date_change_months") or 0))>24 else "SMALL_TO_MODERATE_LE_24M",
                       "t_minus_1":add_month(anchor,-1),"t":anchor,"t_plus_1":add_month(anchor,1),"t_plus_2":add_month(anchor,2),"t_plus_3":add_month(anchor,3),
                       "original_completion":anchor_row.get("original_target_doc_raw",""),"revised_completion":anchor_row.get("revised_doc_raw",""),
                       "anticipated_completion":anchor_row.get("anticipated_doc_raw",""),"machine_event_month":candidate.get("event_month") or "",
                       "machine_event_date":candidate.get("event_approved_date") or "","machine_label":str(item["event"]),
                       "source_report":anchor_row.get("source_id",""),"source_sha256":anchor_row.get("source_sha256",""),
                       "physical_page":anchor_row.get("pdf_page_index",""),"printed_page":anchor_row.get("printed_page_number",""),
                       "source_table":anchor_row.get("source_table",""),"raw_row":json.dumps({field:anchor_row.get(field,"") for field in ("serial_number_raw","project_identity_cell_raw","approval_start_cell_raw","doc_cell_raw","cost_cell_raw","cumulative_expenditure_raw","milestones_raw")},separators=(",",":")),
                       "extracted_source_text":" | ".join(str(anchor_row.get(field,"")) for field in ("project_identity_cell_raw","doc_cell_raw","cost_cell_raw","milestones_raw")),
                       "timeline_json":json.dumps(timeline,separators=(",",":")),"schema_family":anchor_row.get("schema_family",""),
                       "warning_flags":"|".join(warning),"reviewer":"","manual_label":"","confidence":"","evidence_verified":"",
                       "source_page_verified":"","identity_verified":"","review_notes":"","review_timestamp":""})
    return output


def main(raw_root: Path):
    if not raw_root.is_dir(): raise FileNotFoundError(raw_root)
    v1_rows=read_csv(V1/"project_month.csv"); v1_fields=list(v1_rows[0])
    id_map={r.get("project_code_raw",""):r["canonical_project_id"] for r in v1_rows if r.get("project_code_raw")}
    extracted=[]; ledger=[]; summaries={}
    for month in (*HISTORICAL_MONTHS,*RECOVERY):
        path=source_path(raw_root,month)
        if not path.is_file(): raise FileNotFoundError(path)
        discovery=discover_table(path); rows,summary=extract_project_month(path,month,discovery)
        if len(rows)!=EXPECTED_COUNTS[month]: raise RuntimeError(f"{month}: expected {EXPECTED_COUNTS[month]}, got {len(rows)}")
        for row in rows:
            code=str(row.get("project_code_raw","")).strip(); row["canonical_project_id"]=id_map.get(code,f"PRH-{code}")
            row["project_code"]=code; row["identity_status"]="RESOLVED_EXACT"; row["identity_method"]="EXACT_AUTHORITATIVE_PROJECT_CODE"
            for raw,reported in (("project_name_raw","reported_project_name"),("agency_raw","reported_agency"),("state_raw","reported_state"),("approval_date_raw","reported_approval_date"),("original_target_doc_raw","reported_original_target_doc"),("revised_doc_raw","reported_revised_doc"),("original_cost_raw","reported_original_cost"),("revised_cost_raw","reported_revised_cost"),("cumulative_expenditure_raw","reported_cumulative_expenditure"),("physical_progress_raw","reported_physical_progress"),("start_date_raw","reported_start_date")): row[reported]=row.get(raw,"")
        extracted.extend(rows); summaries[month]=summary
        document=fitz.open(path); page_count=document.page_count; sample="".join(document[i].get_text() for i in range(min(3,page_count))); document.close()
        portable_path=(Path("data/raw")/path.relative_to(raw_root)).as_posix()
        ledger.append({"source_id":f"SRC-{month}","reporting_month":month,"source_path":portable_path,"sha256":sha256(path),"page_count":page_count,
                       "text_extractable":"YES" if sample.strip() else "NO","schema_family":discovery["schema_family"],"schema_confidence":discovery["confidence"],
                       "project_rows":len(rows),"table_first_page":discovery["first_page"],"table_last_page":discovery["last_page"],
                       "official_project_count":discovery.get("official_project_count",len(rows)),"row_accounting_status":"PASS",
                       "multipart_status":"PROJECT_LEVEL_PART" if month in RECOVERY else "SINGLE_FILE","project_level_status":"ACCEPTED_RESEARCH_V2",
                       "canonical_v1_use":"NO","v2_use":"PROJECT_LEVEL","reason":"complete project table; exact authoritative project code",
                       "provenance_status":"LOCAL_OFFICIAL_REPORT; DOWNLOAD_URL/TIMESTAMP_NOT_RECORDED"})
    rows=v1_rows+extracted
    fields=list(dict.fromkeys(v1_fields+[key for row in extracted for key in row]))
    for row in rows:
        for field in fields: row.setdefault(field,"")
    rows.sort(key=lambda r:(r["reporting_month"],r["canonical_project_id"]))
    keys=[(r["canonical_project_id"],r["reporting_month"]) for r in rows]
    if len(keys)!=len(set(keys)): raise RuntimeError("duplicate project-month key")
    by_project=defaultdict(list)
    for row in rows: by_project[row["canonical_project_id"]].append(row)
    for observations in by_project.values():
        observations.sort(key=lambda r:r["reporting_month"])
        for index,row in enumerate(observations):
            prev=observations[index-1]["reporting_month"] if index else ""; nxt=observations[index+1]["reporting_month"] if index+1<len(observations) else ""
            row["previous_project_observation_month"]=prev; row["next_project_observation_month"]=nxt
            row["months_since_previous_project_observation"]=(month_index(row["reporting_month"])-month_index(prev)) if prev else ""
            row["months_to_next_project_observation"]=(month_index(nxt)-month_index(row["reporting_month"])) if nxt else ""
            row["calendar_gap_present"]="TRUE" if (prev and add_month(prev,1)!=row["reporting_month"]) else "FALSE"
    write_csv(DATA/"project_month.csv",rows,fields)
    coverage={month:"PROJECT_LEVEL" for month in months_between("2022-08","2026-06")}
    for month in ("2023-12","2024-04","2024-05"): coverage[month]="AGGREGATE_ONLY"
    coverage["2025-02"]="MISSING_SOURCE"
    report_rows=[{"reporting_month":m,"coverage_class":coverage[m],"project_rows":sum(r["reporting_month"]==m for r in rows),
                  "temporal_use":"ELIGIBLE_WHERE_CONTIGUOUS" if coverage[m]=="PROJECT_LEVEL" else "CENSOR_CROSSING_HORIZONS"} for m in months_between("2022-08","2026-06")]
    write_csv(DATA/"report_month.csv",report_rows)
    masters=[]
    for pid,observations in sorted(by_project.items()):
        observations.sort(key=lambda r:r["reporting_month"]); latest=observations[-1]
        masters.append({"canonical_project_id":pid,"project_code":latest.get("project_code_raw",""),"project_name":latest.get("project_name_raw",""),
                        "first_observed_month":observations[0]["reporting_month"],"last_observed_month":latest["reporting_month"],"observed_months":len(observations),
                        "identity_status":"RESOLVED_EXACT" if all(r.get("identity_status")=="RESOLVED_EXACT" for r in observations) else "MIXED"})
    write_csv(DATA/"project_master.csv",masters)
    for row in read_csv(ROOT/"data/metadata/source_coverage_2023_07_2026_06.csv"):
        month=row["reporting_month"]
        if month in RECOVERY: continue
        ledger.append({"source_id":row["source_id"],"reporting_month":month,"source_path":row["source_path"],"sha256":row["sha256"],"page_count":row["page_count"],
                       "text_extractable":row["text_extractability"],"schema_family":next((r["schema_family"] for r in v1_rows if r["reporting_month"]==month),"UNKNOWN"),
                       "project_rows":sum(r["reporting_month"]==month for r in v1_rows),
                       "table_first_page":min((int(r["pdf_page_index"]) for r in v1_rows if r["reporting_month"]==month),default=""),
                       "table_last_page":max((int(r["pdf_page_index"]) for r in v1_rows if r["reporting_month"]==month),default=""),
                       "official_project_count":sum(r["reporting_month"]==month for r in v1_rows) if row["coverage_class"]=="PROJECT_LEVEL" else "",
                       "row_accounting_status":"PASS" if row["coverage_class"]=="PROJECT_LEVEL" else "NOT_APPLICABLE",
                       "schema_confidence":"HIGH" if row["coverage_class"]=="PROJECT_LEVEL" else "N/A","multipart_status":"SINGLE_FILE","project_level_status":row["coverage_class"],
                       "canonical_v1_use":"YES","v2_use":row["coverage_class"],"reason":row["reason"],"provenance_status":"V1_MANIFEST_VERIFIED"})
    write_csv(DATA/"source_ledger.csv",sorted(ledger,key=lambda r:r["reporting_month"]))
    schemas=[]
    for month in months_between("2022-08","2026-06"):
        sample=next((r for r in rows if r["reporting_month"]==month),None)
        schemas.append({"reporting_month":month,"schema_family":sample.get("schema_family") if sample else "UNAVAILABLE",
                        "classification_basis":"observed table structure and field evidence; not year","project_code":"AVAILABLE" if sample else "UNKNOWN",
                        "physical_progress":"AVAILABLE" if sample and sample.get("physical_progress_schema_available")=="TRUE" else ("STRUCTURALLY_UNAVAILABLE" if sample else "UNKNOWN")})
    write_csv(DATA/"schema_ledger.csv",schemas)
    availability=[]
    for month in months_between("2022-08","2026-06"):
        sample=[r for r in rows if r["reporting_month"]==month]
        for field,flag in (("project_code_raw","project_code_schema_available"),("physical_progress_raw","physical_progress_schema_available"),("anticipated_doc_raw","anticipated_doc_schema_available"),("anticipated_cost_raw","anticipated_cost_schema_available")):
            state="UNKNOWN" if not sample else ("STRUCTURALLY_UNAVAILABLE" if sample[0].get(flag)!="TRUE" else ("AVAILABLE" if any(str(r.get(field,"")).strip() for r in sample) else "UNREPORTED"))
            availability.append({"reporting_month":month,"field":field,"availability_state":state,"schema_family":sample[0].get("schema_family","") if sample else ""})
    write_csv(DATA/"field_availability.csv",availability)
    identity=[]
    for left,right in zip(months_between("2022-08","2026-06"),months_between("2022-08","2026-06")[1:]):
        a={r["canonical_project_id"] for r in rows if r["reporting_month"]==left}; b={r["canonical_project_id"] for r in rows if r["reporting_month"]==right}
        identity.append({"from_month":left,"to_month":right,"exact_overlap":len(a&b),"from_projects":len(a),"to_projects":len(b),
                         "boundary_status":"CONTIGUOUS_PROJECT_LEVEL" if coverage[left]==coverage[right]=="PROJECT_LEVEL" else "BLOCKED_BY_SOURCE_COVERAGE"})
    write_csv(DATA/"identity_continuity.csv",identity)
    metadata={"version":V2_VERSION,"status":"PROVISIONAL_RESEARCH; HUMAN TARGET TRANSFER PENDING","row_count":len(rows),"project_count":len(by_project),
              "report_months":47,"project_level_months":sum(v=="PROJECT_LEVEL" for v in coverage.values()),"aggregate_only_months":3,"missing_months":["2025-02"],
              "dataset_fingerprint":dataset_fingerprint(rows),"v1_source_unchanged":True,"raw_sources_read_only":True,"july_2026_included":False}
    DATA.mkdir(parents=True,exist_ok=True); (DATA/"dataset_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    summary_rows=[]; all_target_data={}
    for target in ("S1","S2"):
        for horizon in (3,6,12):
            cohort,candidates,events=build_research_target(rows,coverage,target,horizon,build_basic_long_history,"basic-long-history-v1")
            stem=f"{target.lower()}_{horizon}m_basic"
            write_csv(OUT/f"{stem}_cohort.csv",cohort); write_csv(OUT/f"{stem}_candidate_ledger.csv",candidates); write_csv(OUT/f"{stem}_events.csv",events)
            folds=expanding_folds(cohort,horizon); write_csv(OUT/f"{stem}_expanding_folds.csv",folds)
            for window in (12,18,24):
                write_csv(OUT/f"{stem}_rolling_{window}m_folds.csv",rolling_folds(cohort,horizon,window))
            summary_rows.append({"target":target,"horizon_months":horizon,"feature_contract":"basic-long-history-v1","eligible_rows":len(cohort),"events":sum(int(r["event"]) for r in cohort),
                                 "event_prevalence":sum(int(r["event"]) for r in cohort)/len(cohort) if cohort else 0,
                                 "status":"TWELVE_MONTH_HORIZON_INSUFFICIENT_SUPPORT" if horizon==12 else "MACHINE_PROVISIONAL_HUMAN_TRANSFER_PENDING"})
            all_target_data[(target,horizon)]=(cohort,candidates,events)
        # Target truth always sees the complete longitudinal history.  Filtering
        # OCMS rows before S1 construction would erase prior deteriorations and
        # manufacture false "first" events.  Restrict only the resulting feature
        # anchors to months where the richer schema supports physical progress.
        cohort,candidates,events=build_research_target(rows,coverage,target,3,build_compact_v2,"compact-v2.1-calendar-safe")
        compatible={(r["canonical_project_id"],r["reporting_month"]) for r in rows if r.get("physical_progress_schema_available")=="TRUE"}
        cohort,candidates,events=restrict_feature_anchors(cohort,candidates,events,compatible)
        write_csv(OUT/f"{target.lower()}_3m_compact_v2_cohort.csv",cohort); write_csv(OUT/f"{target.lower()}_3m_compact_v2_candidate_ledger.csv",candidates)
        summary_rows.append({"target":target,"horizon_months":3,"feature_contract":"compact-v2.1-calendar-safe","eligible_rows":len(cohort),"events":sum(int(r["event"]) for r in cohort),
                             "event_prevalence":sum(int(r["event"]) for r in cohort)/len(cohort) if cohort else 0,"status":"MACHINE_PROVISIONAL_HUMAN_TRANSFER_PENDING"})
        basic_keys={(r["canonical_project_id"],r["anchor_month"]) for r in all_target_data[(target,3)][0]}
        compact_keys={(r["canonical_project_id"],r["anchor_month"]) for r in cohort}
        write_csv(OUT/f"{target.lower()}_3m_common_anchor_keys.csv",
                  [{"canonical_project_id":pid,"anchor_month":month} for pid,month in sorted(basic_keys & compact_keys)])
    write_csv(OUT/"target_support_summary.csv",summary_rows)
    transfer=[]
    for target in ("S1","S2"): transfer.extend(make_transfer(target,*all_target_data[(target,3)][:2],rows))
    evidence_fields=[field for field in transfer[0] if field not in {"reviewer","manual_label","confidence","evidence_verified","source_page_verified","identity_verified","review_notes","review_timestamp"}]
    evidence_hashes={row["review_id"]:hashlib.sha256("|".join(str(row.get(field,"")) for field in evidence_fields).encode()).hexdigest() for row in transfer}
    manifest={"version":"historical-target-transfer-v2","row_count":120,"evidence_fields":evidence_fields,"evidence_hashes":evidence_hashes,
              "status":"AWAITING_HUMAN_REVIEW","allowed_manual_labels":["GENUINE_DETERIORATION","NO_DETERIORATION","CORRECTION","NORMALIZATION_ARTIFACT","SOURCE_INCONSISTENCY","INSUFFICIENT_EVIDENCE","OTHER"]}
    write_csv(TRANSFER/"historical_target_transfer_v2.csv",transfer)
    (TRANSFER/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    sampling_audit={"rows":120,"periods":dict(Counter(row["period_stratum"] for row in transfer)),
                    "cost_bands":dict(Counter(row["cost_band"] for row in transfer)),"date_semantics":dict(Counter(row["date_semantics_stratum"] for row in transfer)),
                    "reversions":dict(Counter(row["reversion_flag"] for row in transfer)),
                    "limitations":{"sector":"STRUCTURALLY_UNAVAILABLE in the admitted OCMS-era sample; no sector value fabricated",
                                   "first_appearance":"not eligible because target construction requires prior-month history",
                                   "long_running":"not observable within August 2022–June 2023 anchors; no history fabricated"}}
    (TRANSFER/"sampling_audit.json").write_text(json.dumps(sampling_audit,indent=2),encoding="utf-8")
    errors=validate_transfer_rows(transfer,manifest)
    if errors: raise RuntimeError(errors[:3])
    registry={"version":V2_VERSION,"model_execution_status":"BLOCKED_PENDING_HUMAN_TARGET_TRANSFER","primary_horizon_months":3,
              "research_horizon_6m":"COHORT_BUILT_NOT_OPERATIONAL","research_horizon_12m":"TWELVE_MONTH_HORIZON_INSUFFICIENT_SUPPORT",
              "models_planned":["logistic_regression","random_forest","hist_gradient_boosting","xgboost","equal_soft_vote"],
              "fitting_contract":"all preprocessing, calibration, thresholds and optional weights fit on temporally prior mature outcomes only",
              "july_2026":"UNTOUCHED_PROSPECTIVE_EVIDENCE"}
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"experiment_registry.json").write_text(json.dumps(registry,indent=2),encoding="utf-8")
    status={"version":V2_VERSION,"source_status":"13 NEW PROJECT-LEVEL SOURCES ACCEPTED; 3 AGGREGATE-ONLY; FEBRUARY 2025 MISSING",
            "dataset_counts":metadata,"feature_contracts":{"basic_long_history_v1":list(BASIC_LONG_HISTORY_V1),"compact_v2":"UNCHANGED; RICH-SCHEMA MONTHS ONLY"},
            "target_status":"S1/S2 3M, 6M AND SUPPORT-ONLY 12M MACHINE-PROVISIONAL","adjudication_status":"120-CASE PACKAGE GENERATED; HUMAN REVIEW PENDING",
            "folds":"PREDECLARED EXPANDING AND ROLLING SENSITIVITY INFRASTRUCTURE; ADMISSION RECALCULATED PER COHORT","models":"HARNESS IMPLEMENTED; NOT EXECUTED BEFORE HUMAN TARGET TRANSFER",
            "ensembles":"EQUAL SOFT VOTE IMPLEMENTED BUT NOT EVALUATED","horizons":{"3m":"PRIMARY","6m":"RESEARCH_ONLY_PENDING_VALIDATION","12m":"TWELVE_MONTH_HORIZON_INSUFFICIENT_SUPPORT"},
            "holdout_state":"JULY 2026 UNTOUCHED","blockers":["HISTORICAL_TARGET_TRANSFER_PENDING","V1_TARGET_ADJUDICATION_PENDING"]}
    (OUT/"v2_status.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
    print(json.dumps({"dataset":metadata,"target_support":summary_rows,"transfer_rows":len(transfer)},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--raw-root",type=Path,default=os.environ.get("PRAHARI_RAW_ROOT"))
    args=parser.parse_args()
    if args.raw_root is None: parser.error("--raw-root or PRAHARI_RAW_ROOT is required")
    main(args.raw_root.resolve())
