"""Create local-only, unbundled secrets and certificates; start MongoDB TLS + RBAC."""
import os,secrets,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
C=R/'certs'
C.mkdir(exist_ok=True)
def cmd(*args,check=True,env=None):
    return subprocess.run(args,cwd=R,check=check,text=True,capture_output=True,env=env)
def openssl(*args):
    r=cmd('openssl',*args,check=False)
    if r.returncode: raise RuntimeError('openssl failed: '+r.stderr)
def generate():
    if (C/'ca.crt').exists() and (C/'server.pem').exists() and (C/'client.pem').exists(): return
    openssl('genrsa','-out',str(C/'ca.key'),'2048')
    openssl('req','-new','-x509','-sha256','-days','365','-key',str(C/'ca.key'),'-out',str(C/'ca.crt'),'-subj','/CN=Lab12-Local-CA')
    openssl('genrsa','-out',str(C/'server.key'),'2048')
    openssl('req','-new','-key',str(C/'server.key'),'-out',str(C/'server.csr'),'-subj','/CN=mongo')
    (C/'server.ext').write_text('subjectAltName=DNS:mongo,DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
    openssl('x509','-req','-sha256','-days','365','-in',str(C/'server.csr'),'-CA',str(C/'ca.crt'),'-CAkey',str(C/'ca.key'),'-CAcreateserial','-out',str(C/'server.crt'),'-extfile',str(C/'server.ext'))
    openssl('genrsa','-out',str(C/'client.key'),'2048')
    openssl('req','-new','-key',str(C/'client.key'),'-out',str(C/'client.csr'),'-subj','/CN=Lab12-PyMongo-Client')
    (C/'client.ext').write_text('extendedKeyUsage=clientAuth\n')
    openssl('x509','-req','-sha256','-days','365','-in',str(C/'client.csr'),'-CA',str(C/'ca.crt'),'-CAkey',str(C/'ca.key'),'-CAcreateserial','-out',str(C/'client.crt'),'-extfile',str(C/'client.ext'))
    (C/'server.pem').write_bytes((C/'server.key').read_bytes()+(C/'server.crt').read_bytes())
    (C/'client.pem').write_bytes((C/'client.key').read_bytes()+(C/'client.crt').read_bytes())
    for n in ('ca.key','server.key','client.key','server.pem','client.pem'): os.chmod(C/n,0o600)
    print('Generated local CA, server and client certificates (NOT included in Docker image).')
def credentials():
    f=R/'.env'
    if f.exists(): return dict(line.strip().split('=',1) for line in f.read_text().splitlines() if '=' in line)
    d={'ROOT_USER':'lab12_admin','ROOT_PASSWORD':secrets.token_urlsafe(22),'READ_USER':'app_user_read','READ_PASSWORD':secrets.token_urlsafe(22),'WRITE_USER':'app_user_write','WRITE_PASSWORD':secrets.token_urlsafe(22),'HR_USER':'hr_user','HR_PASSWORD':secrets.token_urlsafe(22)}
    f.write_text(''.join(f'{k}={v}\n' for k,v in d.items()));os.chmod(f,0o600)
    print('Created local .env containing randomized passwords; do not upload it.')
    return d
def main():
    generate(); d=credentials()
    r=cmd('docker','compose','up','-d','mongo',check=False)
    print(r.stdout,r.stderr)
    if r.returncode: raise RuntimeError('Could not start MongoDB container')
    base=['docker','compose','exec','-T','mongo','mongosh','--quiet','--host','localhost','--tls','--tlsCAFile','/certs/ca.crt']
    for i in range(45):
        r=cmd(*(base+['--eval','db.adminCommand({ping:1})']),check=False)
        if r.returncode==0: break
        time.sleep(2)
    else: raise RuntimeError('MongoDB did not start: '+r.stderr)
    env=os.environ.copy();env['LAB12_ROOT_PASSWORD']=d['ROOT_PASSWORD']
    init='const a=db.getSiblingDB("admin"); a.createUser({user:"lab12_admin",pwd:process.env.LAB12_ROOT_PASSWORD,roles:[{role:"root",db:"admin"}]}); print("ROOT CREATED")'
    r=cmd(*(['docker','compose','exec','-T','-e','LAB12_ROOT_PASSWORD='+d['ROOT_PASSWORD'],'mongo','mongosh','--quiet','--host','localhost','--tls','--tlsCAFile','/certs/ca.crt','--eval',init]),check=False)
    if r.returncode==0: print('Created root user')
    elif 'already exists' in r.stderr or 'not authorized' in r.stderr or 'Unauthorized' in r.stderr: print('Root user already exists (preserved)')
    else: print('Root init message:',r.stderr[-400:]);print('If already initialized, this may be expected.')
    print('READY: tls-required server on 127.0.0.1:27617; credentials in local .env')
if __name__=='__main__':main()
