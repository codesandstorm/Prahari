"""Backend adapter for deterministic Officer Decision Layer V1."""
from __future__ import annotations
from collections import Counter
from .data_trust import database_trust
from .repository import ProjectRepository,prediction_dict
from src.decision.governance import DECISION_POLICY_VERSION,decide_review

def review_queue(db):
    repo=ProjectRepository(db);items=[]
    for project in repo.all_projects():
        trust,_,view,release,eligibility=database_trust(db,repo,project)
        stored=repo.latest_prediction(project.canonical_project_id)
        prediction=prediction_dict(repo,stored) if stored else None
        decision=decide_review(trust=trust,eligibility=eligibility,prediction=prediction)
        item=decision.to_dict()|{'project_name':project.canonical_name,'data_trust':view,'model_release':release.to_dict(),'prediction_eligibility':eligibility.to_dict(),'source_provenance_link':None}
        if decision.review_state!='NO_REVIEW_SIGNAL':items.append(item)
    counts=Counter(x['review_state'] for x in items)
    return {'items':items,'status':'ACTIVE_WITH_PREDICTIONS_WITHHELD','policy_version':DECISION_POLICY_VERSION,'counts':dict(counts)}
