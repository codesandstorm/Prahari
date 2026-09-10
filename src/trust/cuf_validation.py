"""Versioned schema/rule validation for current Flash Report and future governed CUF inputs."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from datetime import date,datetime
from typing import Any

@dataclass(frozen=True)
class FieldIssue:
    status:str;code:str;field:str;message:str
    def to_dict(self):return asdict(self)

class StructuredInputValidator:
    def __init__(self,contract_version='flash-report-input-v1'):self.contract_version=contract_version
    def validate(self,current:dict[str,Any],previous:dict[str,Any]|None=None)->dict:
        issues=[]
        def issue(status,code,field,message):issues.append(FieldIssue(status,code,field,message))
        required=('canonical_project_id','reporting_month')
        for f in required:
            if not current.get(f):issue('INVALID','REQUIRED_FIELD_MISSING',f,'Governed required field is absent')
        reporting_month=current.get('reporting_month','')
        if reporting_month:
            try:datetime.strptime(str(reporting_month),'%Y-%m')
            except ValueError:issue('INVALID','DATE_FORMAT_FAIL','reporting_month','Expected YYYY-MM')
        for f in ('physical_progress','reported_physical_progress'):
            if f in current and current[f] not in ('',None):
                try:v=float(str(current[f]).replace('%',''))
                except ValueError:issue('INVALID','FIELD_TYPE_FAIL',f,'Expected numeric percentage');continue
                if not 0<=v<=100:issue('INVALID','FIELD_RANGE_FAIL',f,'Percentage must be between 0 and 100')
        numeric_values={}
        for f in ('original_cost','revised_cost','cumulative_expenditure'):
            if f in current and current[f] not in ('',None):
                try:v=float(str(current[f]).replace(',',''))
                except ValueError:issue('INVALID','FIELD_TYPE_FAIL',f,'Expected numeric value');continue
                numeric_values[f]=v
                if v<0:issue('INVALID','NEGATIVE_NUMERIC_FAIL',f,'Negative value is impossible under this contract')
        def parsed(f):
            v=current.get(f)
            if not v:return None
            try:return date.fromisoformat(str(v))
            except ValueError:issue('INVALID','DATE_FORMAT_FAIL',f,'Expected ISO YYYY-MM-DD');return None
        approval=parsed('approval_date');original=parsed('original_completion_date');revised=parsed('revised_completion_date')
        tender_publish=parsed('tender_publish_date');tender_award=parsed('tender_award_date');updated=parsed('update_date')
        if approval and original and original<approval:issue('INVALID','DATE_LOGIC_FAIL','original_completion_date','Completion precedes approval')
        if original and revised and revised<original:issue('WARNING','POSSIBLE_CORRECTION_WARN','revised_completion_date','Revised date moved earlier than original')
        if tender_publish and tender_award and tender_award<tender_publish:issue('INVALID','MILESTONE_SEQUENCE_FAIL','tender_award_date','Tender award precedes tender publication')
        if updated and len(reporting_month)==7:
            try:period_start=date.fromisoformat(f'{reporting_month}-01')
            except ValueError:issue('INVALID','DATE_FORMAT_FAIL','reporting_month','Expected YYYY-MM')
            else:
                if (period_start.year-updated.year)*12+period_start.month-updated.month>=1:issue('WARNING','STALE_UPDATE_TIMESTAMP_WARN','update_date','Update date predates the reporting period')
        original_cost=numeric_values.get('original_cost');revised_cost=numeric_values.get('revised_cost');expenditure=numeric_values.get('cumulative_expenditure')
        if original_cost is not None and revised_cost is not None and revised_cost<original_cost:issue('WARNING','POSSIBLE_COST_CORRECTION_WARN','revised_cost','Revised cost is lower than original cost and requires verification')
        ceiling=revised_cost if revised_cost is not None else original_cost
        if ceiling is not None and expenditure is not None and expenditure>ceiling:issue('WARNING','COST_EXPENDITURE_PLAUSIBILITY_WARN','cumulative_expenditure','Expenditure exceeds the available governed project cost')
        milestones=current.get('milestones')
        if milestones is not None:
            if not isinstance(milestones,list):issue('INVALID','FIELD_TYPE_FAIL','milestones','Expected governed milestone list')
            else:
                for i,m in enumerate(milestones):
                    try:p=date.fromisoformat(m['planned']);r=date.fromisoformat(m['revised']) if m.get('revised') else None;a=date.fromisoformat(m['actual']) if m.get('actual') else None
                    except (KeyError,ValueError):issue('INVALID','DATE_FORMAT_FAIL',f'milestones[{i}]','Invalid planned/revised/actual date');continue
                    if r and r<p:issue('WARNING','MILESTONE_SEQUENCE_WARN',f'milestones[{i}]','Revised milestone precedes planned date')
                    if a and a<p:issue('WARNING','MILESTONE_ACTUAL_SEQUENCE_WARN',f'milestones[{i}]','Actual milestone date precedes planned date')
        status_value=str(current.get('status','')).upper()
        progress=numeric_values.get('physical_progress')
        try:progress=float(str(current.get('physical_progress')).replace('%',''))
        except (TypeError,ValueError):progress=None
        if status_value=='COMPLETED' and progress is not None and progress<100:issue('WARNING','CONTRADICTORY_STATUS_WARN','status','Completed status conflicts with physical progress below 100%')
        if previous:
            try:old=float(previous.get('physical_progress'));new=float(current.get('physical_progress'))
            except (TypeError,ValueError):old=new=None
            if old is not None and new is not None and new<old:issue('WARNING','TEMPORAL_REVERSAL_WARN','physical_progress',f'Progress decreased from {old} to {new}')
            if previous.get('submission_id') and previous.get('submission_id')==current.get('submission_id'):issue('INVALID','DUPLICATE_SUBMISSION','submission_id','Duplicate governed submission ID')
        governed=set(current)-{'canonical_project_id','reporting_month','submission_id'}
        if not governed and not issues:issue('UNKNOWN','NO_GOVERNED_FIELDS_PRESENT','*','No governed domain fields were supplied for validation')
        status='INVALID' if any(x.status=='INVALID' for x in issues) else 'WARNING' if any(x.status=='WARNING' for x in issues) else 'UNKNOWN' if issues else 'VALID'
        return {'contract_version':self.contract_version,'status':status,'issues':[x.to_dict() for x in issues]}
