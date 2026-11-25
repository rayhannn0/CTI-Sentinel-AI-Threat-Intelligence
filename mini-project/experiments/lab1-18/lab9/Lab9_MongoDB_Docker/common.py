import json,time,sys,traceback
from pathlib import Path
from pymongo.write_concern import WriteConcern
from connection import get_client,DB
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
def log_result(name,data):
 p=OUT/(name+'.json');p.write_text(json.dumps(data,indent=2,default=str));print('Saved:',p)
def log_text(name,text):
 p=OUT/(name+'.txt');p.write_text(text);print('Saved:',p)
def run_writes(label,w,j=None,n=1000,timeout_ms=5000):
 """One insert_one per write, return actual elapsed + results; preserve errors as results."""
 from pymongo.errors import PyMongoError
 with get_client(timeout=12000) as c:
  coll=c[DB]['write_concern_'+label].with_options(write_concern=WriteConcern(w=w,j=j,wtimeout=timeout_ms))
  coll.database.client[DB]['write_concern_'+label].drop()
  t=time.perf_counter();ok=0;fail=0;errors=[]
  for i in range(n):
   try:
    coll.insert_one({'experiment':label,'sequence':i,'payload':'x'*96,'created_utc':time.time()});ok+=1
   except PyMongoError as e:
    fail+=1
    if len(errors)<3:errors.append(f'{type(e).__name__}: {e}')
  ms=(time.perf_counter()-t)*1000
  row={'run':label,'w':w,'j':j,'attempted':n,'acknowledged':ok,'errors':fail,'total_ms':round(ms,2),'avg_ms_per_attempt':round(ms/n,3),'error_samples':errors}
  print(row,flush=True)
  return row
