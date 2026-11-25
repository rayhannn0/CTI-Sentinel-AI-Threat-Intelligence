"""Start and initialize 3-node Docker replica set for Lab 10."""
import subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def call(*args,check=True):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)

def mongo(code):
    r=call('docker','compose','exec','-T','mongo1','mongosh','--quiet','--eval',code,check=False)
    return r.returncode, (r.stdout+r.stderr).strip()

def main():
    print('Starting MongoDB Lab 10 nodes...')
    r=subprocess.run(['docker','compose','up','-d','mongo1','mongo2','mongo3'],cwd=ROOT)
    if r.returncode:sys.exit(r.returncode)
    for i in range(60):
        rc,txt=mongo('db.adminCommand({ping:1}).ok')
        if rc==0 and '1' in txt:break
        time.sleep(2)
    else:sys.exit('MongoDB failed to start. Check docker compose logs.')
    rc,txt=mongo('rs.status().ok')
    if rc!=0:
        rc,txt=mongo("rs.initiate({_id:'rs10',members:[{_id:0,host:'mongo1:27017',priority:2},{_id:1,host:'mongo2:27017',priority:1},{_id:2,host:'mongo3:27017',priority:1}]})")
        if rc!=0 and 'already initialized' not in txt.lower(): sys.exit('Replica set init failed: '+txt)
    for i in range(75):
        rc,txt=mongo('rs.status().members.map(m=>m.stateStr).join(",")')
        if rc==0 and txt.count('PRIMARY')==1 and txt.count('SECONDARY')==2:
            print('READY replica set rs10:',txt)
            print('Compass: mongodb://127.0.0.1:27417/?directConnection=true')
            return
        time.sleep(2)
    sys.exit('Replica set not ready: '+txt)

if __name__=='__main__':main()
