"""Host-side initialization: uses Docker Compose CLI, never resets existing volumes."""
import subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(*args,check=True,capture=False):
 cmd=['docker','compose',*args]
 p=subprocess.run(cmd,cwd=ROOT,check=check,text=True,capture_output=capture)
 if not capture: print('+',' '.join(cmd),flush=True)
 return p
def main():
 try:
  run('version')
  run('up','-d','mongo1','mongo2','mongo3')
  for _ in range(40):
   p=run('exec','-T','mongo1','mongosh','--quiet','--eval','db.adminCommand({ping:1}).ok',check=False,capture=True)
   if p.returncode==0 and '1' in p.stdout:break
   time.sleep(2)
  else:raise RuntimeError('mongo1 did not become ready; inspect docker compose logs')
  js="try {rs.status();print('Replica set already initialized')} catch(e) { if(e.codeName==='NotYetInitialized'||e.code===94) {printjson(rs.initiate({_id:'rs9',members:[{_id:0,host:'mongo1:27017',priority:2},{_id:1,host:'mongo2:27017',priority:1},{_id:2,host:'mongo3:27017',priority:1}]}))} else {throw e} }"
  run('exec','-T','mongo1','mongosh','--quiet','--eval',js)
  for _ in range(50):
   p=run('exec','-T','mongo1','mongosh','--quiet','--eval',"try { let s=rs.status().members; print(s.filter(x=>x.stateStr==='PRIMARY').length+':'+s.filter(x=>x.stateStr==='SECONDARY').length) }catch(e){print('waiting')}",check=False,capture=True)
   if '1:2' in p.stdout:
    print('READY: 1 PRIMARY + 2 SECONDARY; w=3 uses all three data-bearing nodes')
    return
   time.sleep(2)
  raise RuntimeError('Replica set did not reach three healthy data-bearing nodes')
 except (FileNotFoundError,subprocess.CalledProcessError) as e:
  raise RuntimeError('Docker CLI/Engine unavailable or Compose failed. Start Docker Desktop, then run python3 bootstrap.py') from e
if __name__=='__main__':main()
