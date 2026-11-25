"""Lab 15.2: seed -> migrate -> validate. Idempotent with replace for demo."""
import argparse
import random
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient, ASCENDING
import os

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['tasktracker']


def seed():
    random.seed(15)
    db.tasks.delete_many({'seed_batch': 'lab15_2'})
    docs = []
    for i in range(1, 6):
        tenant = f'tenant{i}'
        for j in range(100):
            docs.append({'tenant_id': tenant, 'owner_id': f'seed_user_{i}',
                         'title': f'{tenant} task {j + 1}', 'description': 'Lab 15.2 dataset',
                         'priority': random.choice(['low', 'medium', 'high']),
                         'status': random.choice(['open', 'done']),
                         'created_at': datetime.now(timezone.utc) - timedelta(minutes=j),
                         'seed_batch': 'lab15_2'})
    db.tasks.insert_many(docs)
    db.tasks.create_index([('tenant_id', ASCENDING), ('created_at', ASCENDING)])
    print('Seeded 5 tenants x 100 tasks = 500 benchmark records')


def migrate():
    for tenant in db.tasks.distinct('tenant_id', {'seed_batch': 'lab15_2'}):
        name = f'tasks_{tenant}'
        docs = list(db.tasks.find({'tenant_id': tenant, 'seed_batch': 'lab15_2'}))
        db[name].delete_many({'seed_batch': 'lab15_2'})
        if docs:
            db[name].insert_many(docs)
        db[name].create_index('created_at')
        print(f'{tenant}: copied {len(docs)} records to {name}')


def validate():
    passed = True
    for i in range(1, 6):
        tenant = f'tenant{i}'
        source = list(db.tasks.find({'tenant_id': tenant, 'seed_batch': 'lab15_2'}))
        dest = list(db[f'tasks_{tenant}'].find({'seed_batch': 'lab15_2'}))
        same_ids = {d['_id'] for d in source} == {d['_id'] for d in dest}
        no_leak = all(d['tenant_id'] == tenant for d in dest)
        good = len(source) == len(dest) == 100 and same_ids and no_leak
        passed &= good
        print(f'{tenant}: shared={len(source)}, isolated={len(dest)}, IDs match={same_ids}, leakage-free={no_leak}, PASS={good}')
    if not passed:
        raise SystemExit('VALIDATION FAILED')
    print('ALL FIVE TENANTS VALIDATED: PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['seed', 'migrate', 'validate', 'all'])
    args = parser.parse_args()
    if args.action in ('seed', 'all'): seed()
    if args.action in ('migrate', 'all'): migrate()
    if args.action in ('validate', 'all'): validate()
