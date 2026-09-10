"""Deterministic human-adjudication package builder and validator."""
from __future__ import annotations
import csv, hashlib, html, json, random, re
from datetime import date
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pdfplumber
from src.ml.final_prediction import add_month, approved_doc, month_date, value

SEED=26103
LABELS=("CONFIRMED_FIRST_SCHEDULE_DETERIORATION","CONFIRMED_FURTHER_DETERIORATION","CORRECTION_NOT_EVENT","DATE_NORMALIZATION_ARTIFACT","IDENTITY_UNCERTAIN","SOURCE_INCONSISTENCY","INSUFFICIENT_EVIDENCE","OTHER")
HUMAN_FIELDS=("manual_label","reviewer_name_or_id","review_confidence","review_notes","evidence_verified","source_page_verified","identity_verified","review_timestamp")
EVIDENCE_FIELDS=("review_row_id","review_stratum","target_family","canonical_project_id","project_name","anchor_month","target_horizon","identity_status","identity_method","original_approved_completion_date","approved_date_at_t","t_minus_1_date","t_date","t_plus_1_date","t_plus_2_date","t_plus_3_date","machine_event","machine_event_month","machine_event_date","baseline_date","date_change_days","date_change_months","completed_at_t","source_schema","source_transition_flag","correction_like_flag","original_date_change_flag","large_jump_flag","date_decrease_nearby_flag","missing_field_flag","technical_warning_flags","source_report_ids","source_paths","source_sha256s","source_availability","page_table_provenance","source_evidence_excerpt","timeline","current_machine_label")

def read_csv(path:Path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write_csv(path:Path,rows):
    rows=list(rows);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else list(EVIDENCE_FIELDS+HUMAN_FIELDS));w.writeheader();w.writerows(rows)
def sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def _date(row):
    d=approved_doc(row) if row else None
    return d.isoformat() if d else ""
def _days(left,right):
    try:a=date.fromisoformat(left);b=date.fromisoformat(right)
    except (TypeError,ValueError):return ""
    return (b-a).days if a and b else ""

class PageEvidence:
    def __init__(self, raw_root:Path, manifest:list[dict[str,str]]):
        self.raw_root=raw_root;self.manifest={r['source_id']:r for r in manifest};self.readers={};self.cache={}
    def source(self,source_id):
        m=self.manifest.get(source_id,{})
        rel=m.get('relative_path','');path=self.raw_root/Path(rel).relative_to('data/raw') if rel.startswith('data/raw') else self.raw_root/rel
        if not path.is_file():return m,path,'SOURCE_UNAVAILABLE'
        try:
            reader=self.readers.setdefault(str(path),pdfplumber.open(path))
            return m,path,'SOURCE_AVAILABLE' if len(reader.pages)>0 else 'SOURCE_UNREADABLE'
        except Exception:return m,path,'SOURCE_UNREADABLE'
    def excerpt(self,source_id,page_index,needles):
        m,path,status=self.source(source_id)
        if status!='SOURCE_AVAILABLE':return '',status
        try: idx=int(page_index)
        except Exception:return '', 'SOURCE_UNREADABLE'
        key=(str(path),idx)
        try:
            reader=self.readers[str(path)]
            if idx<0 or idx>=len(reader.pages):return '', 'SOURCE_UNREADABLE'
            text=self.cache.setdefault(key,reader.pages[idx].extract_text() or '')
            normalized=' '.join(text.split())
            if not normalized:return '', 'SOURCE_UNREADABLE'
            pos=-1
            for needle in needles:
                if needle and (p:=normalized.lower().find(needle.lower()))>=0:pos=p;break
            if pos<0:return normalized[:900],status
            return normalized[max(0,pos-250):pos+850],status
        except Exception:return '', 'SOURCE_UNREADABLE'

def build_master(root:Path,raw_root:Path):
    project=read_csv(root/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv')
    manifest=read_csv(root/'data/metadata/source_manifest.csv'); pe=PageEvidence(raw_root,manifest)
    by=defaultdict(dict)
    for r in project:by[r['canonical_project_id']][r['reporting_month']]=r
    results=[]; source_ids=set()
    for target in ('S1','S2'):
        events=read_csv(root/'outputs/ml/final_prediction_v1'/f'{target.lower()}_event_ledger.csv')
        for e in events:
            lookup=by[e['canonical_project_id']];a=lookup[e['anchor_month']]
            months=[add_month(e['anchor_month'],i) for i in (-1,0,1,2,3)]
            timeline=[];dates=[];prov=[];excerpts=[];avail=[];ids=[];paths=[];hashes=[]
            previous=None;decrease=False;multiple=0
            for m in months:
                r=lookup.get(m);d=_date(r);dates.append(d)
                if previous and d and d!=previous:
                    multiple+=1
                    if date.fromisoformat(d)<date.fromisoformat(previous):decrease=True
                if d:previous=d
                if r:
                    sid=r.get('source_id','');source_ids.add(sid);ids.append(sid)
                    meta,path,status=pe.source(sid);avail.append(status);paths.append(str(path));hashes.append(meta.get('sha256',''))
                    prov.append(f"{m}:{sid}:physical_index={r.get('pdf_page_index','')}:printed={r.get('printed_page_number','')}:table={r.get('source_table','')}:locator={r.get('raw_row_locator','')}")
                timeline.append(f"{m}: original={value(r or {},'original_target_doc_raw','reported_original_target_doc') or 'MISSING'}; revised={value(r or {},'revised_doc_raw','reported_revised_doc') or 'MISSING'}; effective={d or 'MISSING'}")
            flags=[]
            if e.get('possible_correction_flag','').lower()=='true':flags.append('CORRECTION_LIKE')
            if e.get('original_date_changed','').lower()=='true':flags.append('ORIGINAL_DATE_CHANGED')
            if decrease:flags.append('DATE_REVERTED_LATER')
            change=int(e.get('date_change_months') or 0)
            flags.append('LARGE_DATE_JUMP' if change>=12 else 'SMALL_DATE_CHANGE' if change<=2 else 'MODERATE_DATE_CHANGE')
            if e.get('source_schema_transition','').lower()=='true':flags.append('SCHEMA_TRANSITION')
            if a.get('identity_method')=='VERIFIED_LEGACY_OCMS_BRIDGE':flags.append('LEGACY_IDENTITY_BRIDGE')
            if multiple>1:flags.append('MULTIPLE_CHANGES_WITHIN_HORIZON')
            if any(x!='SOURCE_AVAILABLE' for x in avail):flags.append('SOURCE_UNAVAILABLE')
            row={"review_row_id":"","review_stratum":"","target_family":target,"canonical_project_id":e['canonical_project_id'],"project_name":value(a,'project_name_raw','reported_project_name'),"anchor_month":e['anchor_month'],"target_horizon":3,"identity_status":a.get('identity_status',''),"identity_method":a.get('identity_method',''),"original_approved_completion_date":value(a,'original_target_doc_raw','reported_original_target_doc'),"approved_date_at_t":_date(a),"t_minus_1_date":dates[0],"t_date":dates[1],"t_plus_1_date":dates[2],"t_plus_2_date":dates[3],"t_plus_3_date":dates[4],"machine_event":1,"machine_event_month":e['event_month'],"machine_event_date":e['event_approved_date'],"baseline_date":e['baseline_approved_date'],"date_change_days":_days(e['baseline_approved_date'],e['event_approved_date']),"date_change_months":change,"completed_at_t":False,"source_schema":a.get('schema_family',''),"source_transition_flag":e.get('source_schema_transition',''),"correction_like_flag":e.get('possible_correction_flag',''),"original_date_change_flag":e.get('original_date_changed',''),"large_jump_flag":change>=12,"date_decrease_nearby_flag":decrease,"missing_field_flag":any(not x for x in dates[1:]),"technical_warning_flags":"|".join(flags),"source_report_ids":"|".join(dict.fromkeys(ids)),"source_paths":"|".join(dict.fromkeys(paths)),"source_sha256s":"|".join(dict.fromkeys(hashes)),"source_availability":"|".join(sorted(set(avail))),"page_table_provenance":" || ".join(prov),"source_evidence_excerpt":" || ".join(excerpts),"timeline":" || ".join(timeline),"current_machine_label":f"MACHINE_{target}_EVENT"}
            results.append(row)
    # Audit every report referenced by machine events.
    audit=[]
    for sid in sorted(source_ids):
        m,path,status=pe.source(sid); actual=sha256(path) if status=='SOURCE_AVAILABLE' else ''
        readable=m.get('text_extractable','').upper()=='YES';pages=''
        if status=='SOURCE_AVAILABLE':
            try:r=pe.readers[str(path)];pages=len(r.pages)
            except Exception:status='SOURCE_UNREADABLE'
        report_month=(f"{int(m.get('report_year')):04d}-{int(m.get('report_month')):02d}" if m.get('report_year') and m.get('report_month') else m.get('reporting_month',''))
        audit.append({'reporting_month':report_month,'source_id':sid,'relative_source_path':m.get('relative_path',''),'manifest_sha256':m.get('sha256',''),'actual_sha256':actual,'hash_matches':bool(actual and actual==m.get('sha256','')),'pdf_status':status,'page_count':pages,'physical_pages_available':bool(pages),'manifest_text_extractable':m.get('text_extractable',''),'sampled_pages_text_extracted':readable})
    return results,audit

def enrich_sample_excerpts(root:Path,raw_root:Path,samples:list[dict[str,Any]]):
    project=read_csv(root/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv');manifest=read_csv(root/'data/metadata/source_manifest.csv');pe=PageEvidence(raw_root,manifest)
    lookup={(r['canonical_project_id'],r['reporting_month']):r for r in project}
    for sample in samples:
        excerpts=[]
        for offset in (-1,0,1,2,3):
            month=add_month(sample['anchor_month'],offset);r=lookup.get((sample['canonical_project_id'],month))
            if not r:continue
            excerpt,status=pe.excerpt(r.get('source_id',''),r.get('pdf_page_index',''),[r.get('project_code',''),r.get('project_name_raw',''),r.get('reported_project_name','')])
            if excerpt:excerpts.append(f"[{month} {r.get('source_id','')} page-index {r.get('pdf_page_index','')}] {excerpt}")
            elif status!='SOURCE_AVAILABLE':excerpts.append(f"[{month} {r.get('source_id','')}] {status}")
        sample['source_evidence_excerpt']=' || '.join(excerpts)
    return samples

def choose_sample(master,target):
    positives=[r.copy() for r in master if r['target_family']==target]
    rng=random.Random(SEED+(1 if target=='S2' else 0));rng.shuffle(positives)
    quotas=[('CORRECTION_LIKE',12),('WEAK_REGIME',12),('ORIGINAL_DATE_CHANGED',6),('LEGACY_IDENTITY',6),('LARGE_JUMP',6),('SMALL_CHANGE',6),('ORDINARY_POSITIVE',7)] if target=='S1' else [('CORRECTION_LIKE',6),('WEAK_REGIME',10),('ORIGINAL_DATE_CHANGED',5),('LEGACY_IDENTITY',7),('LARGE_JUMP',8),('SMALL_CHANGE',8),('ORDINARY_POSITIVE',15)]
    def match(r,s):
        return {'CORRECTION_LIKE':r['correction_like_flag'].lower()=='true','WEAK_REGIME':'2025-07'<=r['anchor_month']<='2025-11','ORIGINAL_DATE_CHANGED':r['original_date_change_flag'].lower()=='true','LEGACY_IDENTITY':r['identity_method']=='VERIFIED_LEGACY_OCMS_BRIDGE','LARGE_JUMP':int(r['date_change_months'])>=12,'SMALL_CHANGE':int(r['date_change_months'])<=2,'ORDINARY_POSITIVE':True}[s]
    picked=[];used=set()
    for stratum,n in quotas:
        for r in positives:
            key=(r['canonical_project_id'],r['anchor_month'])
            if len([x for x in picked if x['review_stratum']==stratum])>=n:break
            if key not in used and match(r,stratum):r['review_stratum']=stratum;picked.append(r);used.add(key)
    for r in positives:
        if len(picked)>=60:break
        key=(r['canonical_project_id'],r['anchor_month'])
        if key not in used:r['review_stratum']='FALLBACK_POSITIVE';picked.append(r);used.add(key)
    picked=picked[:60]
    for i,r in enumerate(picked,1):
        r['review_row_id']=f'{target}-VAL-{i:04d}'
        for field in HUMAN_FIELDS:r[field]=''
    return picked

def negative_controls(root:Path,raw_root:Path,target:str,n:int=6):
    candidates=[r for r in read_csv(root/'outputs/ml/final_prediction_v1'/f'{target.lower()}_candidate_ledger.csv') if r['status']=='ELIGIBLE' and r['event']=='0']
    project=read_csv(root/'data/processed/longitudinal_2023_07_2026_06_mixed/project_month.csv');lookup={(r['canonical_project_id'],r['reporting_month']):r for r in project}
    random.Random(SEED+99+(target=='S2')).shuffle(candidates);out=[]
    for c in candidates[:n]:
        a=lookup[(c['canonical_project_id'],c['anchor_month'])];months=[add_month(c['anchor_month'],i) for i in (-1,0,1,2,3)];rows=[lookup.get((c['canonical_project_id'],m)) for m in months]
        timeline=' || '.join(f"{m}: original={value(r or {},'original_target_doc_raw','reported_original_target_doc') or 'MISSING'}; revised={value(r or {},'revised_doc_raw','reported_revised_doc') or 'MISSING'}; effective={_date(r) or 'MISSING'}" for m,r in zip(months,rows))
        ids=[];paths=[];hashes=[];avail=[];prov=[];manifest={r['source_id']:r for r in read_csv(root/'data/metadata/source_manifest.csv')};pe=PageEvidence(raw_root,list(manifest.values()))
        for m,r in zip(months,rows):
            if not r:continue
            sid=r.get('source_id','');meta,path,status=pe.source(sid);ids.append(sid);paths.append(str(path));hashes.append(meta.get('sha256',''));avail.append(status);prov.append(f"{m}:{sid}:physical_index={r.get('pdf_page_index','')}:printed={r.get('printed_page_number','')}:table={r.get('source_table','')}:locator={r.get('raw_row_locator','')}")
        dates=[_date(r) for r in rows]
        out.append({"review_row_id":"","review_stratum":"NEGATIVE_CONTROL","target_family":target,"canonical_project_id":c['canonical_project_id'],"project_name":value(a,'project_name_raw','reported_project_name'),"anchor_month":c['anchor_month'],"target_horizon":3,"identity_status":a.get('identity_status',''),"identity_method":a.get('identity_method',''),"original_approved_completion_date":value(a,'original_target_doc_raw','reported_original_target_doc'),"approved_date_at_t":_date(a),"t_minus_1_date":dates[0],"t_date":dates[1],"t_plus_1_date":dates[2],"t_plus_2_date":dates[3],"t_plus_3_date":dates[4],"machine_event":0,"machine_event_month":"","machine_event_date":"","baseline_date":c.get('baseline_approved_date',''),"date_change_days":"","date_change_months":"","completed_at_t":False,"source_schema":a.get('schema_family',''),"source_transition_flag":False,"correction_like_flag":False,"original_date_change_flag":False,"large_jump_flag":False,"date_decrease_nearby_flag":False,"missing_field_flag":any(not x for x in dates[1:]),"technical_warning_flags":"NEGATIVE_CONTROL","source_report_ids":"|".join(dict.fromkeys(ids)),"source_paths":"|".join(dict.fromkeys(paths)),"source_sha256s":"|".join(dict.fromkeys(hashes)),"source_availability":"|".join(sorted(set(avail))),"page_table_provenance":" || ".join(prov),"source_evidence_excerpt":"","timeline":timeline,"current_machine_label":f"MACHINE_{target}_NON_EVENT"})
    return out

def validate_review(canonical:list[dict[str,str]],submitted:list[dict[str,str]]):
    errors=[];base={r['review_row_id']:r for r in canonical};seen=set();counts=Counter()
    for row in submitted:
        rid=row.get('review_row_id','')
        if rid not in base:errors.append(f'UNKNOWN_ROW_ID:{rid}');continue
        if rid in seen:errors.append(f'DUPLICATE_REVIEW:{rid}');continue
        seen.add(rid)
        for f in EVIDENCE_FIELDS:
            if row.get(f,'')!=base[rid].get(f,''):errors.append(f'TAMPERED_EVIDENCE:{rid}:{f}')
        label=row.get('manual_label','').strip()
        if not label:continue
        if label not in LABELS:errors.append(f'INVALID_LABEL:{rid}:{label}')
        for f in ('reviewer_name_or_id','review_confidence','evidence_verified','source_page_verified','identity_verified','review_timestamp'):
            if not row.get(f,'').strip():errors.append(f'MISSING_REVIEW_FIELD:{rid}:{f}')
        if row.get('review_confidence') not in ('HIGH','MEDIUM','LOW'):errors.append(f'INVALID_CONFIDENCE:{rid}')
        counts[label]+=1
    return {'valid':not errors,'errors':errors,'reviewed':sum(counts.values()),'total':len(canonical),'unresolved':len(canonical)-sum(counts.values()),'labels':dict(counts)}

def render_html(samples,out):
    payload=json.dumps(samples).replace('</','<\\/')
    options=''.join(f'<option>{html.escape(x)}</option>' for x in LABELS)
    doc=f'''<!doctype html><meta charset="utf-8"><title>PRAHARI Target Adjudication V1</title><style>body{{font:15px system-ui;margin:0;background:#eef2f6;color:#172033}}header{{position:sticky;top:0;background:#102a43;color:white;padding:16px 5%;z-index:2}}main{{max-width:1200px;margin:24px auto;padding:0 18px}}article{{background:white;border-radius:12px;padding:20px;margin:16px 0;box-shadow:0 2px 10px #0001}}.flags{{color:#9b2c2c;font-weight:650}}pre{{white-space:pre-wrap;background:#f6f8fa;padding:12px;max-height:260px;overflow:auto}}label{{display:block;margin:9px 0}}select,textarea,input{{width:100%;padding:8px;box-sizing:border-box}}button{{padding:10px 16px}}</style><header><b>PRAHARI S1/S2 Target Adjudication V1</b> - decisions remain human-owned <button onclick="download()">Export reviewed JSON</button></header><main id="app"></main><script>const cases={payload};const opts={json.dumps(options)};const app=document.getElementById('app');cases.forEach((c,i)=>{{let a=document.createElement('article');a.innerHTML=`<h2>${{c.review_row_id}} - ${{c.target_family}} - ${{c.canonical_project_id}}</h2><p>${{c.project_name}} | anchor ${{c.anchor_month}} | stratum ${{c.review_stratum}}</p><p class=flags>${{c.technical_warning_flags||'NO TECHNICAL FLAGS'}}</p><h3>Timeline</h3><pre>${{c.timeline}}</pre><h3>Source evidence</h3><pre>${{c.source_evidence_excerpt||'SOURCE TEXT UNAVAILABLE - inspect referenced page'}}</pre><p><b>Provenance:</b> ${{c.page_table_provenance}}</p><label>Manual label<select data-i="${{i}}" data-f="manual_label"><option value=""></option>${{opts}}</select></label><label>Reviewer ID<input data-i="${{i}}" data-f="reviewer_name_or_id"></label><label>Confidence<select data-i="${{i}}" data-f="review_confidence"><option></option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></label><label>Notes<textarea data-i="${{i}}" data-f="review_notes"></textarea></label>`;app.appendChild(a)}});document.addEventListener('input',e=>{{if(e.target.dataset.f)cases[e.target.dataset.i][e.target.dataset.f]=e.target.value}});function download(){{let b=new Blob([JSON.stringify(cases,null,2)],{{type:'application/json'}}),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='prahari_completed_reviews.json';a.click();URL.revokeObjectURL(u)}}</script>'''
    verification='''<label>Evidence verified<select data-i="${i}" data-f="evidence_verified"><option></option><option>YES</option><option>NO</option></select></label><label>Source page verified<select data-i="${i}" data-f="source_page_verified"><option></option><option>YES</option><option>NO</option></select></label><label>Identity verified<select data-i="${i}" data-f="identity_verified"><option></option><option>YES</option><option>NO</option></select></label><label>Review timestamp<input type="datetime-local" data-i="${i}" data-f="review_timestamp"></label>'''
    doc=doc.replace('<label>Notes',verification+'<label>Notes')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(doc,encoding='utf-8')
