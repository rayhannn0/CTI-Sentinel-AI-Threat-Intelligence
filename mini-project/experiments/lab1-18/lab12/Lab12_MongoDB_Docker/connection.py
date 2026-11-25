import os
from pathlib import Path
from pymongo import MongoClient

CA=Path('/app/certs/ca.crt') if Path('/app/certs/ca.crt').exists() else Path(__file__).parent/'certs'/'ca.crt'
HOST=os.getenv('MONGO_HOST', 'mongo' if Path('/app/certs').exists() else '127.0.0.1')
PORT=int(os.getenv('MONGO_PORT','27017' if HOST=='mongo' else '27617'))

def client(username=None,password=None, use_cert=False):
    username=username or os.environ['ROOT_USER']
    password=password or os.environ['ROOT_PASSWORD']
    opts=dict(host=HOST,port=PORT,username=username,password=password,authSource='admin',tls=True,tlsCAFile=str(CA),serverSelectionTimeoutMS=5000)
    if use_cert:
        opts['tlsCertificateKeyFile']=str(CA.parent/'client.pem')
    return MongoClient(**opts)
