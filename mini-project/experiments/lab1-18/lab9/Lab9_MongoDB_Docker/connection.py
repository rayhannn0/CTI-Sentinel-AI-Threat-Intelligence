"""Shared replica-set client for processes INSIDE the Docker Compose network."""
import os
from pymongo import MongoClient
MONGO_URI=os.getenv('MONGO_URI','mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs9')
DB='lab9'
def get_client(timeout=8000):
    c=MongoClient(MONGO_URI,serverSelectionTimeoutMS=timeout,connectTimeoutMS=3000)
    c.admin.command('ping')
    return c
def print_status():
    with get_client() as c:
        s=c.admin.command('replSetGetStatus')
        for m in s['members']:
            print(f"{m['name']:19} {m['stateStr']:12} health={m['health']}")
if __name__=='__main__':
    print('Database:',DB);print_status()
