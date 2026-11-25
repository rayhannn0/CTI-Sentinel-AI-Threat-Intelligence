#!/usr/bin/env python3
"""Provision keyfile and authenticated rs13 replica set; safe to rerun."""
from pathlib import Path
import subprocess,time,secrets,string,os,base64
R=Path(__file__).resolve().parent
os.chdir(R)
def dc(*a,check=True):
 return subprocess.run(['docker','compose',*a],capture_output=True,text=True,check=check)
def mongo(js,auth=False):
 args=['exec','-T','mongo1','mongosh','--quiet','--eval',js]
 if auth:
  pw=read_password()
  # avoid including secret in command line: pass via mongosh stdin and connect with environment passed to container
  env_cmd=['exec','-T','-e','MONGO_LAB_PASSWORD='+pw,'mongo1','mongosh','--quiet','--eval',
   'const pw=process.env.MONGO_LAB_PASSWORD;db.getSiblingDB("admin").auth("lab13_admin",pw);'+js]
  return dc(*env_cmd,check=False)
 return dc(*args,check=False)
def read_password():
 for ln in (R/'.env').read_text().splitlines():
  if ln.startswith('ROOT_PASSWORD='):return ln.split('=',1)[1]
 raise RuntimeError('Missing ROOT_PASSWORD')
if not (R/'keyfile').exists():
 # ASCII-only 1024-ish chars, strict permission, not included in image
 (R/'keyfile').write_text(base64.b64encode(secrets.token_bytes(756)).decode()+'\n')
 os.chmod(R/'keyfile',0o400)
if not (R/'.env').exists():
 chars=string.ascii_letters+string.digits
 pwd=''.join(secrets.choice(chars) for _ in range(36))
 (R/'.env').write_text('ROOT_PASSWORD='+pwd+'\n')
 os.chmod(R/'.env',0o600)
print('Starting 3 MongoDB nodes ...')
x=dc('up','-d','mongo1','mongo2','mongo3',check=False)
if x.returncode:raise SystemExit(x.stderr)
for i in range(75):
 r=mongo('db.adminCommand({ping:1})')
 if r.returncode==0:break
 time.sleep(2)
else:raise RuntimeError('mongo1 not responding: '+r.stderr[-500:])
# unauthenticated localhost exception only exists before first user
r=mongo('try {print(rs.status().ok)} catch(e) {print(e.codeName)}')
if 'NotYetInitialized' in r.stdout or 'no replset config has been received' in r.stdout:
 js='rs.initiate({_id:"rs13",members:[{_id:0,host:"mongo1:27017"},{_id:1,host:"mongo2:27017"},{_id:2,host:"mongo3:27017"}]})'
 rr=mongo(js)
 if rr.returncode:raise RuntimeError('rs.initiate failed: '+rr.stdout+rr.stderr)
print('Waiting for primary election ...')
for i in range(65):
 rr=mongo('print(db.hello().isWritablePrimary)')
 if 'true' in rr.stdout:break
 time.sleep(2)
else:raise RuntimeError('Primary election timeout')
# Create user via localhost exception if absent; if already created, authenticated verification succeeds.
pwd=read_password()
admin_check=mongo('print(db.runCommand({connectionStatus:1}).ok)',auth=True)
if admin_check.returncode!=0 or '1' not in admin_check.stdout:
 # pass via docker exec env to avoid embedding in JS source
 js='const a=db.getSiblingDB("admin");if(!a.getUser("lab13_admin"))a.createUser({user:"lab13_admin",pwd:process.env.MONGO_LAB_PASSWORD,roles:[{role:"root",db:"admin"}]});'
 cr=dc('exec','-T','-e','MONGO_LAB_PASSWORD='+pwd,'mongo1','mongosh','--quiet','--eval',js,check=False)
 if cr.returncode:raise RuntimeError('Admin creation failed: '+cr.stderr[-400:])
for i in range(60):
 check=mongo('const s=rs.status();print(s.members.map(m=>m.stateStr).join(","))',auth=True)
 if check.returncode==0 and 'PRIMARY' in check.stdout and check.stdout.count('SECONDARY')==2:
  print('READY: '+check.stdout.strip());break
 time.sleep(2)
else: raise RuntimeError('Replica set not healthy: '+check.stdout+' '+check.stderr[-400:])
print('RUN: docker compose --profile runner build labrunner')
print('RUN: docker compose --profile runner run --rm labrunner')
print('COMPASS NOTE: host port 27717 is direct node access, not full seed list')
