"""Lab 8.1: Insert to primary, verify reads from BOTH secondaries, print status."""
import sys, pathlib, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from pymongo.write_concern import WriteConcern
from connection import DB_NAME, PORTS, member_client, wait_for_primary, status_summary

COLLECTION = 'replication_demo'

def main():
    primary = wait_for_primary()
    c = member_client(primary)
    try:
        coll = c[DB_NAME].get_collection(COLLECTION, write_concern=WriteConcern(w='majority', wtimeout=15000))
        key = 'lab8-replication-document'
        coll.update_one({'_id': key}, {'$set': {'message': 'Replicated hello from Lab 8.1', 'source': primary}}, upsert=True)
        print('Inserted/upserted on primary:', primary)
    finally:
        c.close()
    for name in PORTS:
        if name == primary: continue
        end = time.monotonic()+35
        while time.monotonic() < end:
            secondary = member_client(name)
            try:
                doc = secondary[DB_NAME][COLLECTION].find_one({'_id': key})
            finally:
                secondary.close()
            if doc:
                print(f'REPLICATION PASS {name}: {doc}')
                break
            time.sleep(2)
        else:
            raise RuntimeError(f'Document not visible on {name} within timeout')
    print('rs.status() summary:')
    status_summary()

if __name__ == '__main__': main()
