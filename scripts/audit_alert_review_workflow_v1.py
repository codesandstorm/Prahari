#!/usr/bin/env python3
"""Repository-integrity audit for Alert/Review Workflow V1."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    alert=json.loads((ROOT/'config'/'alert_policy_v1.json').read_text());review=json.loads((ROOT/'config'/'officer_review_policy_v1.json').read_text());demo=json.loads((ROOT/'outputs'/'alert_review_workflow_v1'/'demo_workflows.json').read_text())
    porcelain=subprocess.run(['git','status','--porcelain'],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines()
    changed=[line[3:].split(' -> ')[-1].replace('\\','/') for line in porcelain]
    forbidden=[x for x in changed if x.startswith(('frontend/','data/raw/')) or 'schedule_prediction_final_v3' in x or 'cost_prediction' in x]
    required=['backend/workflow_service.py','backend/workflow_api.py','src/workflow/alert_policy.py','src/workflow/lifecycle.py','alembic/versions/20260913_02_alert_review_workflow_v1.py','docs/alerts/PRAHARI_ALERT_SYSTEM_V1.md','docs/review/PRAHARI_REVIEW_API_CONTRACT.md']
    service=(ROOT/'backend'/'workflow_service.py').read_text();api=(ROOT/'backend'/'workflow_api.py').read_text()
    checks={'policy_versioned':alert['policy_version']=='alert-policy-v1.0' and review['policy_version']=='officer-review-v1.0','required_artifacts_present':all((ROOT/x).exists() for x in required),'raw_probability_trigger_disabled':alert['raw_probability_can_trigger'] is False,'raw_watch_trigger_disabled':alert['raw_watch_signal_can_trigger'] is False,'benchmark_trigger_disabled':alert['benchmark_can_trigger'] is False,'predictions_withheld':demo['schedule_prediction_status']=='WITHHELD' and demo['cost_prediction_status']=='WITHHELD','recovery_resolves':demo['recovery_state']=='RESOLVED','recurrence_reopens':demo['reopen_state']=='REOPENED','opening_and_current_evidence_separate':'initial_evidence_snapshot' in service and 'latest_evidence_snapshot' in service,'mode_filtered_queues':'Alert.data_origin==_mode(mode)' in api and 'OfficerReview.data_origin==_mode(mode)' in api,'frontend_or_scientific_changes':forbidden}
    checks['status']='PASS' if all(v is True or v==[] for v in checks.values()) else 'FAIL';print(json.dumps(checks,indent=2));raise SystemExit(0 if checks['status']=='PASS' else 1)
if __name__=='__main__':main()
