"""Host-side direct connections to Docker-exposed MongoDB ports.

Replica-set member hostnames (mongo1, mongo2, mongo3) resolve INSIDE Docker,
not ordinarily from macOS. directConnection=True avoids client-side DNS errors.
"""
import os
import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DB_NAME = 'lab8'
PORTS = { 'mongo1': int(os.getenv('MONGO1_PORT', '27217')),
          'mongo2': int(os.getenv('MONGO2_PORT', '27218')),
          'mongo3': int(os.getenv('MONGO3_PORT', '27219')) }

def member_client(name, timeout_ms=2500):
    port = PORTS[name]
    return MongoClient(f'mongodb://127.0.0.1:{port}/?directConnection=true',
                       serverSelectionTimeoutMS=timeout_ms, connectTimeoutMS=timeout_ms)

def hello(name):
    c = member_client(name)
    try:
        return c.admin.command('hello')
    finally:
        c.close()

def primary_name():
    for name in PORTS:
        try:
            if hello(name).get('isWritablePrimary', False):
                return name
        except PyMongoError:
            continue
    return None

def wait_for_primary(timeout=75):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        name = primary_name()
        if name:
            return name
        time.sleep(2)
    raise RuntimeError('No primary elected. Check: docker compose ps; docker compose logs')

def primary_client(timeout=75):
    return member_client(wait_for_primary(timeout))

def status_summary():
    client = primary_client()
    try:
        s = client.admin.command('replSetGetStatus')
        for item in s['members']:
            print(f"{item['name']:16s} {item['stateStr']:12s} healthy={item.get('health', '?')}")
        return s
    finally:
        client.close()

if __name__ == '__main__':
    print('Database:', DB_NAME)
    status_summary()
