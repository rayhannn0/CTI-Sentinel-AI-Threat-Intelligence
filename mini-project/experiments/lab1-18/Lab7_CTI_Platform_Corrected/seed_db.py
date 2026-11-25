import json
from pathlib import Path
from connection import get_db

ROOT = Path(__file__).resolve().parent

def seed():
    db = get_db()
    for coll, filename in [('threats','threats.json'),('sources','sources.json'),('reports','reports.json')]:
        data = json.loads((ROOT / 'data' / filename).read_text())
        for doc in data:
            db[coll].replace_one({'_id':doc['_id']}, doc, upsert=True)
        print(f'{coll}: {len(data)} demonstration/reference records upserted')
    db.threats.create_index([('title','text'),('description','text'),('tags','text')], name='threat_text')
    db.threats.create_index([('platform',1),('status',1)])
    db.threats.create_index('source_ids')
    db.reports.create_index('url', unique=True, sparse=True)
    print('MongoDB Compass database: lab7')

if __name__ == '__main__': seed()
