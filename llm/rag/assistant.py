from __future__ import annotations
import json,time
from dataclasses import asdict,dataclass
from pathlib import Path
from typing import Any
from llm.schemas.evidence import PrahariEvidence
from llm.service.assistant import PrahariAssistant
from llm.service.ollama_client import GenerationSettings,OllamaClient
from .contracts import RagResponse
from .fallback import rag_fallback
from .prompt import build_rag_prompt
from .retriever import LexicalRetriever
from .router import QuestionRoute,route_question
from .validation import validate_rag_response

@dataclass(frozen=True)
class UnifiedResult:
    request_id:str;route:str;answer:dict[str,Any];project_evidence_references:list[str]
    document_citations:list[dict[str,Any]];reliability_statement:str|None;limitations:list[str]
    fallback_used:bool;fallback_reason:str|None;model_version:str;rag_index_version:str|None
    latency_metadata:dict[str,float]

class UnifiedPrahariAssistant:
    def __init__(self,retriever:LexicalRetriever|None,client:OllamaClient|None=None,config_path:Path|None=None):
        self.project_assistant=PrahariAssistant(config_path,client);self.client=client or self.project_assistant.client
        self.retriever=retriever;self.config=self.project_assistant.config;self.system=self.project_assistant.system
        self.rag_config=json.loads((Path(__file__).resolve().parents[1]/"rag_config.json").read_text(encoding="utf-8"))
    def answer(self,question:str,project_evidence:dict[str,Any]|None=None,request_id:str="UNSPECIFIED")->UnifiedResult:
        start=time.perf_counter(); project=PrahariEvidence.from_dict(project_evidence) if project_evidence else None
        route=route_question(question,project is not None);retrieval_s=0.;generation_s=0.
        if route==QuestionRoute.PROJECT_EVIDENCE:
            result=self.project_assistant.explain(project_evidence,question)
            return UnifiedResult(request_id,route.value,result.response.to_dict(),[project.canonical_project_id],[],result.response.reliability_explanation,result.response.limitations,result.used_fallback,result.fallback_reason,result.model,None,{"retrieval_seconds":0.,"generation_seconds":result.latency_seconds or 0.,"total_seconds":time.perf_counter()-start})
        chunks=[]
        if route in {QuestionRoute.DOCUMENT_RAG,QuestionRoute.MIXED}:
            if self.retriever is None:
                response=rag_fallback(route,project,[],"retriever unavailable");return self._result(request_id,route,response,project,True,"retriever unavailable",start,0.,0.)
            rt=time.perf_counter();ranked=self.retriever.retrieve(question,self.rag_config["retrieval_top_k"],self.rag_config["minimum_retrieval_score"]);retrieval_s=time.perf_counter()-rt;chunks=[x[1] for x in ranked]
            if not chunks:
                response=rag_fallback(route,project,[],"no relevant approved chunks");return self._result(request_id,route,response,project,True,"no relevant approved chunks",start,retrieval_s,0.)
        if route==QuestionRoute.UNSUPPORTED:
            response=rag_fallback(route,project,[],"unsupported question");return self._result(request_id,route,response,project,True,"unsupported question",start,0.,0.)
        prompt=build_rag_prompt(question,route,chunks,project);settings=GenerationSettings(temperature=self.rag_config["temperature"],seed=self.rag_config["seed"],num_predict=self.rag_config["num_predict"],top_p=self.rag_config["top_p"])
        generated=self.client.generate(self.config["model"],self.system,prompt,settings);generation_s=generated.get("latency_seconds") or 0.;failure=generated.get("error") or generated.get("parse_error")
        checked=validate_rag_response(generated.get("parsed_response"),chunks,project) if not failure else None
        if failure or not checked.valid:
            reason=str(failure or "; ".join(checked.errors));response=rag_fallback(route,project,chunks,reason);return self._result(request_id,route,response,project,True,reason,start,retrieval_s,generation_s)
        return self._result(request_id,route,checked.response,project,False,None,start,retrieval_s,generation_s)
    def _result(self,request_id,route,response,project,fallback,reason,start,retrieval,generation):
        return UnifiedResult(request_id,route.value,response.to_dict(),[project.canonical_project_id] if project else [],[x.to_dict() for x in response.citations],f"Reliability: {project.reliability_band}" if project else None,response.limitations,fallback,reason,self.config["model"],self.retriever.index_version if self.retriever else None,{"retrieval_seconds":retrieval,"generation_seconds":generation,"total_seconds":time.perf_counter()-start})
