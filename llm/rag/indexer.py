from __future__ import annotations
import json
from pathlib import Path
from .ingest import CHUNKING_VERSION,extract_chunks
from .inventory import discover_sources

INDEX_VERSION="rag-v1-src-2026-06-frontmatter-p1-21"
def build_index(root:Path)->Path:
    inventory=discover_sources(root);out=root/"outputs/llm/rag";out.mkdir(parents=True,exist_ok=True)
    (out/"source_inventory.json").write_text(json.dumps([x.to_dict() for x in inventory],indent=2),encoding="utf-8")
    selected=[x for x in inventory if x.approved_for_rag]
    if not selected:raise RuntimeError("no approved documents")
    index=out/"index"/INDEX_VERSION
    if index.exists():raise FileExistsError(f"immutable index already exists: {index}")
    index.mkdir(parents=True)
    chunks=[];pages=[]
    for source in selected:
        source_chunks,status=extract_chunks(root,source,max_page=21);chunks.extend(source_chunks);pages.extend(status)
    (index/"source_manifest.json").write_text(json.dumps([x.to_dict() for x in selected],indent=2),encoding="utf-8")
    (index/"chunks.jsonl").write_text("\n".join(json.dumps(x.to_dict(),ensure_ascii=False) for x in chunks)+"\n",encoding="utf-8")
    (index/"extraction_status.json").write_text(json.dumps(pages,indent=2),encoding="utf-8")
    (index/"retrieval_config.json").write_text(json.dumps({"method":"BM25 lexical","top_k":5,"minimum_score":.01,"tokenizer":"lowercase alphanumeric; English stopword removal","query_expansion":"three explicit transparent PAIMANA/major/mega definition expansions"},indent=2),encoding="utf-8")
    (index/"embedding_metadata.json").write_text(json.dumps({"enabled":False,"reason":"transparent lexical baseline avoids new model/dependency and is sufficient for the bounded official corpus"},indent=2),encoding="utf-8")
    metadata={"index_version":INDEX_VERSION,"chunking_version":CHUNKING_VERSION,"retriever_version":"bm25-local-v1","approved_page_scope":"physical pages 1-21: title, methodology note, overview and ministry summaries; project tables excluded because project facts belong to Domain A","documents":len(selected),"chunks":len(chunks),"extracted_pages":sum(x["status"]=="EXTRACTED" for x in pages),"unreadable_pages":sum(x["status"]=="UNREADABLE_OR_EMPTY" for x in pages),"out_of_scope_pages":sum(x["status"]=="OUT_OF_APPROVED_SCOPE" for x in pages)}
    (index/"index_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    return index
