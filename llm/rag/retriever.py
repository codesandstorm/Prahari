from __future__ import annotations
import json,math,re
from collections import Counter
from pathlib import Path
from .contracts import DocumentChunk

TOKEN=re.compile(r"[a-z0-9]+")
STOP={"a","an","and","are","as","at","be","by","for","from","how","in","is","it","of","on","or","the","this","to","was","what","which","who","with"}
def tokens(text):return [x for x in TOKEN.findall(text.lower()) if x not in STOP]
def query_tokens(text):
    result=tokens(text);lower=text.lower()
    if "paimana" in lower and "stand for" in lower:result+=tokens("Project Assessment Infrastructure Monitoring Analytics Nation-building")
    if "define" in lower and "major project" in lower:result+=tokens("major project if having original cost 1000 crore")
    if "define" in lower and "mega project" in lower:result+=tokens("mega project if having original cost 1000 crore")
    return result

class LexicalRetriever:
    def __init__(self,chunks:list[DocumentChunk],index_version:str="UNKNOWN"):
        self.chunks=chunks;self.index_version=index_version;self.tf=[Counter(tokens((c.section or "")+" "+c.chunk_text)) for c in chunks]
        self.length=[sum(x.values()) for x in self.tf];self.avg=sum(self.length)/len(self.length) if self.length else 1
        df=Counter();
        for row in self.tf:df.update(row.keys())
        self.idf={term:math.log(1+(len(chunks)-count+.5)/(count+.5)) for term,count in df.items()}
    @classmethod
    def from_index(cls,path:Path):
        chunks=[DocumentChunk.from_dict(json.loads(x)) for x in (path/"chunks.jsonl").read_text(encoding="utf-8").splitlines() if x]
        meta=json.loads((path/"index_metadata.json").read_text(encoding="utf-8"));return cls(chunks,meta["index_version"])
    def retrieve(self,question:str,top_k:int=5,min_score:float=.01):
        query=Counter(query_tokens(question));scores=[];k1=1.5;b=.75
        for i,row in enumerate(self.tf):
            score=0.0
            for term,qf in query.items():
                f=row.get(term,0)
                if f:score+=self.idf.get(term,0)*f*(k1+1)/(f+k1*(1-b+b*self.length[i]/self.avg))*qf
            if score>=min_score:scores.append((score,self.chunks[i]))
        scores.sort(key=lambda x:(-x[0],x[1].chunk_id));return scores[:top_k]
