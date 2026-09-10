"""Bounded HTTP smoke checks for an already-running local PRAHARI backend."""
from __future__ import annotations
import json,time,urllib.error,urllib.request
BASE='http://127.0.0.1:8000/api/v1'
def call(name,path,body=None):
    request=urllib.request.Request(BASE+path,data=json.dumps(body).encode() if body else None,headers={'Content-Type':'application/json'},method='POST' if body else 'GET');started=time.perf_counter()
    try:
        with urllib.request.urlopen(request,timeout=90) as response:data=json.loads(response.read());ok=response.status==200
    except Exception as exc:return {'name':name,'status':'FAIL','seconds':round(time.perf_counter()-started,3),'reason':type(exc).__name__}
    return {'name':name,'status':'PASS' if ok else 'FAIL','seconds':round(time.perf_counter()-started,3),'route':data.get('route'),'fallback':data.get('fallback_used')}
def main():
    checks=[call('health','/health'),call('projects','/projects?page=1&page_size=5'),call('detail','/projects/PRH-400010'),call('history','/projects/PRH-400010/history'),call('queue','/review-queue?page=1&page_size=10'),call('rag','/assistant/query',{'request_id':'smoke-rag','question':'What is PAIMANA?'}),call('withheld','/assistant/query',{'request_id':'smoke-project','question':'Why is this prediction withheld?','canonical_project_id':'PRH-400010'}),call('safety','/assistant/query',{'request_id':'smoke-safe','question':'Which contractor caused this delay and who should be punished?','canonical_project_id':'PRH-400010'})];print(json.dumps(checks,indent=2));return 0 if all(x['status']=='PASS' for x in checks) else 1
if __name__=='__main__':raise SystemExit(main())
