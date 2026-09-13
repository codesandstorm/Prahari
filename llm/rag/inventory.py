from __future__ import annotations
import csv, hashlib, os
from pathlib import Path
from .contracts import SourceDocument

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def resolve_inventory_source_path(root:Path,relative_path:str)->Path:
    relative=Path(relative_path);local=root/relative
    raw_root=os.environ.get("PRAHARI_RAW_ROOT")
    if not local.is_file() and raw_root and relative.parts[:2]==("data","raw"):
        return Path(raw_root).resolve()/Path(*relative.parts[2:])
    return local

def discover_sources(root:Path)->list[SourceDocument]:
    rows=list(csv.DictReader((root/"data/metadata/source_manifest.csv").open(encoding="utf-8-sig")))
    result=[]
    for row in rows:
        rel=row.get("relative_path",""); path=resolve_inventory_source_path(root,rel) if rel else None; status=row.get("file_status","")
        is_june=row.get("source_id")=="SRC-2026-06"
        classification="APPROVED_OFFICIAL" if is_june else ("EXCLUDE" if status in {"REJECTED_DUPLICATE","MISSING"} else "UNVERIFIED")
        result.append(SourceDocument(row.get("source_id","") or "UNIDENTIFIED",f"MoSPI Flash Report {row.get('report_year','')} {row.get('report_month','')}","Ministry of Statistics and Programme Implementation","Flash Report",f"{row.get('report_year','')}-{str(row.get('report_month','')).zfill(2)}" if row.get('report_year') else None,rel,row.get("sha256","") or (sha256(path) if path and path.is_file() else ""),int(row["page_count"]) if row.get("page_count") else None,classification,is_june,"June 2026 is the validated canonical report selected for bounded prototype RAG" if is_june else "Not page-level approved for RAG; retained in inventory only"))
    for rel in ("docs/reference/OFFICIAL_SOURCE_NOTES.md","docs/reference/CUF_RESEARCH_STATUS.md","docs/research/CUF_COMPLETE_FIELD_BLUEPRINT.md"):
        path=root/rel
        result.append(SourceDocument("INTERNAL-"+path.stem.upper(),path.stem.replace("_"," "),"PRAHARI team","Internal research note",None,rel,sha256(path),None,"PROJECT_INTERNAL",False,"Internal or hypothetical research is not official documentary evidence"))
    return result
