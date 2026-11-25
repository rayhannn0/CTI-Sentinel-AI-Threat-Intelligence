"""HOST-side controlled partition in lab9_isolated only; ALWAYS reconnects nodes in finally.
Requires healthy three-voter replica set and Docker Desktop; never touches Lab 8 containers.
"""
import subprocess,time,json,sys,traceback,signal
from pathlib import Path
from pymongo import MongoClient
from pymongo.write_concern import WriteConcern
from pymongo.errors import PyMongoError
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
HOSTS={'mongo1':27317,'mongo2':27318,'mongo3':27319}

def shell(args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
def compose(*args):return shell(['docker','compose',*args])
def direct(n):return MongoClient(f'mongodb://127.0.0.1:{HOSTS[n]}/?directConnection=true',serverSelectionTimeoutMS=1500)
def state():
 for n in HOSTS:
  try:
   with direct(n) as c:
    h=c.admin.command('hello')
    if h.get('isWritablePrimary'):return n,[x for x in HOSTS if x!=n]
  except PyMongoError:pass
 return None,[]
def container(n):return compose('ps','-q',n)
def network(cid):
 info=json.loads(shell(['docker','inspect',cid]))[0]
 nets=list(info['NetworkSettings']['Networks'])
 matching=[n for n in nets if n.startswith('lab9_isolated_')]
 if len(matching)!=1:raise RuntimeError(f'Expected exactly one lab9_isolated network on {cid}, found {nets}')
 return matching[0]
def wait_status(n,should_primary=None,seconds=12):
 until=time.monotonic()+seconds
 while time.monotonic()<until:
  try:
   with direct(n) as c:
    h=c.admin.command('hello')
    if should_primary is None or bool(h.get('isWritablePrimary'))==should_primary:return True
  except PyMongoError:pass
  time.sleep(1)
 return False

def write(n,w,label):
 try:
  with direct(n) as c:
   t=time.perf_counter();c['lab9']['partition_writes'].with_options(write_concern=WriteConcern(w=w,wtimeout=3000)).insert_one({'scenario':label,'w':w,'at':time.time()})
   return {'label':label,'w':w,'ack':True,'ms':round((time.perf_counter()-t)*1000,2)}
 except PyMongoError as e:return {'label':label,'w':w,'ack':False,'error':type(e).__name__+': '+str(e)[:180]}

def main():
 print('WARNING: disconnecting Docker networking temporarily on lab9_isolated only.')
 primary,sec=state()
 if not primary or len(sec)!=2:raise RuntimeError('No stable primary; run python3 bootstrap.py and wait for 1 primary + 2 secondaries')
 with direct(primary) as c:
  m=c.admin.command('replSetGetStatus')['members']
  if len(m)!=3 or sorted(x['stateStr'] for x in m)!=['PRIMARY','SECONDARY','SECONDARY'] or not all(x['health']==1 for x in m):
   raise RuntimeError('Requires exactly three healthy data-bearing members, no arbiter. This lab uses a separate cluster.')
 ids={n:container(n) for n in sec}
 net=network(ids[sec[0]])
 if network(ids[sec[1]])!=net:raise RuntimeError('Secondaries are not on same Docker network')
 disconnected=[];results=[]
 try:
  print('Primary:',primary,'Secondaries:',sec,'Network:',net,flush=True)
  # Isolate first secondary, majority remains two of three.
  shell(['docker','network','disconnect',net,ids[sec[0]]]);disconnected.append(sec[0]);print('PARTITION first secondary:',sec[0],flush=True)
  time.sleep(5)
  results.extend([write(primary,1,'one_secondary_isolated'),write(primary,'majority','one_secondary_isolated')])
  print('Holding first partition 30 seconds ...',flush=True);time.sleep(30)
  # Isolate second secondary; primary loses voting majority, normally steps down.
  shell(['docker','network','disconnect',net,ids[sec[1]]]);disconnected.append(sec[1]);print('PARTITION second secondary:',sec[1],flush=True)
  time.sleep(7)
  results.extend([write(primary,1,'both_secondaries_isolated'),write(primary,'majority','both_secondaries_isolated')])
 finally:
  for n in reversed(disconnected):
   try:
    shell(['docker','network','connect','--alias',n,net,ids[n]]);print('RECONNECTED:',n,flush=True)
   except Exception as e:print('URGENT: reconnect manually:',f'docker network connect {net} {ids[n]}','reason:',e,flush=True)
  time.sleep(10)
  now,_=state();print('Primary after recovery:',now,flush=True)
  report={'original_primary':primary,'secondary_order':sec,'network':net,'results':results,'primary_after_recovery':now}
  (OUT/'lab_9_2_partition.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':
 try:main()
 except (subprocess.CalledProcessError,RuntimeError) as e:
  print('ERROR:',e,file=sys.stderr);sys.exit(1)
