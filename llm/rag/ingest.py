from __future__ import annotations
import hashlib,re
from pathlib import Path
import pymupdf
from .contracts import DocumentChunk,SourceDocument

CHUNKING_VERSION="page-paragraph-v1-450w-40w-overlap"
def clean(text:str)->str:return re.sub(r"\s+"," ",text.replace("\x00"," ")).strip()
def make_chunk_id(document_id:str,page:int,part:int,text:str)->tuple[str,str]:
    text_hash=hashlib.sha256(text.encode()).hexdigest()
    return f"{document_id}-p{page:04d}-c{part:02d}-{text_hash[:12]}",text_hash
def _section(text:str)->str|None:
    line=clean(text)[:120]
    return line if line else None
def extract_chunks(root:Path,source:SourceDocument,target_words:int=450,overlap_words:int=40,max_page:int|None=None)->tuple[list[DocumentChunk],list[dict]]:
    if not source.approved_for_rag:raise ValueError("source is not approved for RAG")
    path=(root/source.source_path).resolve(); doc=pymupdf.open(path); chunks=[]; page_status=[]; pending_heading=None
    for page_index,page in enumerate(doc):
        text=clean(page.get_text("text")); page_no=page_index+1
        if max_page is not None and page_no>max_page:
            page_status.append({"document_id":source.document_id,"page":page_no,"status":"OUT_OF_APPROVED_SCOPE","characters":len(text)});continue
        if len(text)<40:
            page_status.append({"document_id":source.document_id,"page":page_no,"status":"UNREADABLE_OR_EMPTY","characters":len(text)});continue
        page_status.append({"document_id":source.document_id,"page":page_no,"status":"EXTRACTED","characters":len(text)})
        words=text.split(); start=0; part=0; section=pending_heading or _section(text)
        while start<len(words):
            segment=" ".join(words[start:start+target_words]);chunk_id,text_hash=make_chunk_id(source.document_id,page_no,part,segment)
            chunks.append(DocumentChunk(chunk_id,source.document_id,source.sha256,source.title,page_no,page_no,section,text_hash,segment))
            if start+target_words>=len(words):break
            start+=target_words-overlap_words;part+=1
        pending_heading=_section(text) if len(words)<40 else None
    return chunks,page_status
