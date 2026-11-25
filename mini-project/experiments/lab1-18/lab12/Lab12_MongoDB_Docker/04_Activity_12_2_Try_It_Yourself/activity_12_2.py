import ssl,subprocess
from pathlib import Path
from common import save
from connection import CA,client

def main():
    certdir=CA.parent
    info={}
    for name in ['ca.crt','server.crt','client.crt']:
        f=certdir/name
        p=subprocess.run(['openssl','x509','-in',str(f),'-noout','-subject','-issuer','-dates'],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr)
        info[name]=p.stdout.strip().splitlines()
    c=client(use_cert=True);c.admin.command('ping')
    r={'activity':'Try it yourself 12.2','chain':info,'server_hostname_SANS':'DNS:mongo, DNS:localhost, IP:127.0.0.1','tls_ping_verified':True,'cert_auth_note':'Client certificate presented for TLS; user authentication uses SCRAM/password, not X.509 database authentication.'}
    print(r);save('activity_12_2',r)
if __name__=='__main__':main()
