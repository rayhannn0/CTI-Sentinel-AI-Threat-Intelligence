import subprocess,time,sys

def dc(*args,check=True):
    cmd=['docker','compose',*args]
    p=subprocess.run(cmd,text=True,capture_output=True)
    if check and p.returncode: raise RuntimeError(f'{cmd}: {p.stderr}\n{p.stdout}')
    return p

def mongo(service,js):
    return dc('exec','-T',service,'mongosh','--quiet','--port', '27019' if service=='config1' else '27017','--eval',js)

def until(fn,label,seconds=90):
    for _ in range(seconds):
        try:
            r=fn()
            if r.returncode==0:return r
        except Exception:pass
        time.sleep(1)
    raise RuntimeError('Timed out: '+label)

print('Starting config server and two shard replica sets...')
dc('up','-d','config1','shard1','shard2')
for name,port in [('config1',27019),('shard1',27017),('shard2',27017)]:
    until(lambda n=name: dc('exec','-T',n,'mongosh','--quiet','--port',str(27019 if n=='config1' else 27017),'--eval','db.adminCommand({ping:1})',check=False),name)
for name,rs,port in [('config1','cfg11',27019),('shard1','shard11a',27017),('shard2','shard11b',27017)]:
    configflag=',configsvr:true' if name=='config1' else ''
    js=f'if (!db.hello().setName) rs.initiate({{_id:"{rs}"{configflag},members:[{{_id:0,host:"{name}:{port}"}}]}})'
    r=mongo(name,js)
    if r.returncode:print('Initiate note:',r.stderr.strip())
    until(lambda n=name: dc('exec','-T',n,'mongosh','--quiet','--port',str(27019 if n=='config1' else 27017),'--eval','if (!db.hello().isWritablePrimary) quit(2)',check=False),rs)
print('Starting mongos...')
dc('up','-d','mongos')
until(lambda: dc('exec','-T','mongos','mongosh','--quiet','--eval','db.adminCommand({ping:1})',check=False),'mongos')
for shard in ['shard11a/shard1:27017','shard11b/shard2:27017']:
    r=dc('exec','-T','mongos','mongosh','--quiet','--eval',f'try {{ sh.addShard("{shard}") }} catch(e) {{ if (!String(e).includes("already")) throw e }}',check=False)
    if r.returncode:
        # Already registered shards are harmless; verify in final list
        print('addShard:',r.stderr.strip()[:300])
r=dc('exec','-T','mongos','mongosh','--quiet','--eval','printjson(db.adminCommand({listShards:1}).shards.map(x=>x._id))')
print('Registered shards:',r.stdout.strip())
if 'shard11a' not in r.stdout or 'shard11b' not in r.stdout:sys.exit('Both shards must be registered')
print('READY. Compass URI: mongodb://127.0.0.1:27517/?directConnection=true')
