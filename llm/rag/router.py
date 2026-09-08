from __future__ import annotations
from enum import Enum

class QuestionRoute(str,Enum):
    PROJECT_EVIDENCE="PROJECT_EVIDENCE";DOCUMENT_RAG="DOCUMENT_RAG";MIXED="MIXED";UNSUPPORTED="UNSUPPORTED"
UNSUPPORTED=("punish","blame","corrupt","fraud","negligent","guilty")
PROJECT=("this project","project flagged","risk","probability","reliability","trajectory","contributor","abstain")
DOCUMENT=("paimana","cuf","ipmd","flash report","official","mospi","crip","mega project","major project","harmonized master list","hml","rs. 150","₹150")
def route_question(question:str,has_project_evidence:bool=False)->QuestionRoute:
    q=question.lower()
    if any(x in q for x in UNSUPPORTED):return QuestionRoute.UNSUPPORTED
    project=has_project_evidence and any(x in q for x in PROJECT);document=any(x in q for x in DOCUMENT)
    if project and document:return QuestionRoute.MIXED
    if document:return QuestionRoute.DOCUMENT_RAG
    if has_project_evidence:return QuestionRoute.PROJECT_EVIDENCE
    return QuestionRoute.UNSUPPORTED
