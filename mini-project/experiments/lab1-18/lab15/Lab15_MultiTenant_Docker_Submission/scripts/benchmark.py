"""Illustrative local wall-clock benchmarking; not a universal speed claim."""
import os
import time
import statistics
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['tasktracker']
N = 30

def measure(fn):
    samples = []
    for _ in range(N):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter()-start)*1000)
    return round(statistics.median(samples), 3)


def shared_listing():
    list(db.tasks.find({'tenant_id': 'tenant1', 'seed_batch': 'lab15_2'}))


def separate_listing():
    list(db.tasks_tenant1.find({'seed_batch': 'lab15_2'}))


def shared_analytics():
    list(db.tasks.aggregate([{'$match': {'seed_batch': 'lab15_2'}}, {'$group': {'_id': '$tenant_id', 'count': {'$sum': 1}}}]))


def separate_analytics():
    [db[f'tasks_tenant{i}'].count_documents({'seed_batch': 'lab15_2'}) for i in range(1, 6)]


def shared_create():
    result = db.tasks.insert_one({'tenant_id': 'tenant1', 'title': 'benchmark', 'created_at': datetime.now(timezone.utc), 'seed_batch': 'benchmark'})
    db.tasks.delete_one({'_id': result.inserted_id})


def separate_create():
    result = db.tasks_tenant1.insert_one({'tenant_id': 'tenant1', 'title': 'benchmark', 'created_at': datetime.now(timezone.utc), 'seed_batch': 'benchmark'})
    db.tasks_tenant1.delete_one({'_id': result.inserted_id})


if __name__ == '__main__':
    assert db.tasks.count_documents({'seed_batch': 'lab15_2'}) == 500, 'Run migrate.py all first'
    assert db.tasks_tenant1.count_documents({'seed_batch': 'lab15_2'}) == 100, 'Run migrate.py all first'
    print('Median elapsed time over 30 local iterations (ms); results vary by hardware:')
    for name, shared, separate in [('List', shared_listing, separate_listing), ('Create+delete', shared_create, separate_create), ('Analytics', shared_analytics, separate_analytics)]:
        print(f'{name:<15} shared={measure(shared):>8.3f}  collection-per-tenant={measure(separate):>8.3f}')
