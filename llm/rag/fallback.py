from __future__ import annotations
from llm.schemas.evidence import PrahariEvidence
from .contracts import Citation,DocumentChunk,RagResponse
from .router import QuestionRoute

INSUFFICIENT="The approved documents retrieved for this question do not provide sufficient evidence."
def rag_fallback(route:QuestionRoute,project:PrahariEvidence|None,chunks:list[DocumentChunk],reason:str)->RagResponse:
    project_points=list(project.contributors) if project else []
    limitations=[INSUFFICIENT,"Generated answer was unavailable or rejected; deterministic fallback used."]
    if project and project.prediction_status in {"ABSTAIN","WITHHELD"}:limitations.append(f"Project prediction is {project.prediction_status}; probability and risk band remain unavailable.")
    return RagResponse(INSUFFICIENT,project_points,[],limitations,["Verify project evidence and inspect an approved source."],[],route.value=="UNSUPPORTED")
