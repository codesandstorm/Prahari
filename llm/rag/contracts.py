from __future__ import annotations
from dataclasses import asdict, dataclass, field, fields
from typing import Any

@dataclass(frozen=True)
class SourceDocument:
    document_id:str; title:str; organization:str; document_type:str
    publication_date:str|None; source_path:str; sha256:str; page_count:int|None
    classification:str; approved_for_rag:bool; approval_reason:str
    language:str="English"; version:str="1"
    def to_dict(self):return asdict(self)
    @classmethod
    def from_dict(cls,data):return cls(**data)

@dataclass(frozen=True)
class DocumentChunk:
    chunk_id:str; document_id:str; source_hash:str; title:str
    page_start:int; page_end:int; section:str|None; text_hash:str; chunk_text:str
    def to_dict(self):return asdict(self)
    @classmethod
    def from_dict(cls,data):return cls(**data)

@dataclass(frozen=True)
class Citation:
    document_id:str; title:str; page:int; chunk_id:str; source_hash:str
    def to_dict(self):return asdict(self)
    @classmethod
    def from_dict(cls,data):
        allowed={f.name for f in fields(cls)}
        if set(data)!=allowed:raise ValueError("citation fields do not match contract")
        return cls(**data)

@dataclass(frozen=True)
class RagResponse:
    answer:str; project_evidence_points:list[str]=field(default_factory=list)
    document_evidence_points:list[str]=field(default_factory=list)
    limitations:list[str]=field(default_factory=list)
    recommended_review_areas:list[str]=field(default_factory=list)
    citations:list[Citation]=field(default_factory=list); unsupported_question:bool=False
    @classmethod
    def from_dict(cls,data:dict[str,Any]):
        allowed={f.name for f in fields(cls)}
        if not isinstance(data,dict) or set(data)!=allowed:raise ValueError("RAG response fields do not match contract")
        for key in ("project_evidence_points","document_evidence_points","limitations","recommended_review_areas"):
            if not isinstance(data[key],list) or not all(isinstance(x,str) for x in data[key]):raise ValueError(f"{key} must be strings")
        if not isinstance(data["answer"],str) or not isinstance(data["unsupported_question"],bool):raise ValueError("invalid RAG response types")
        if not isinstance(data["citations"],list):raise ValueError("citations must be a list")
        return cls(**{**data,"citations":[Citation.from_dict(x) for x in data["citations"]]})
    def to_dict(self):return {**asdict(self),"citations":[x.to_dict() for x in self.citations]}
