"""Lab 7.2: 100,000 roughly 2 KiB BSON records and WiredTiger cache study.
Run explicitly: this replaces only lab7.working_set and uses over 200 MB on disk.
"""
import sys, json, random, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from connection import get_db
from bson import BSON

COUNT=100_000

def cache_snapshot(db):
    try:
        cache=db.command('serverStatus').get('wiredTiger',{}).get('cache',{})
        if not cache:
            return {'available':False,'reason':'WiredTiger cache stats unavailable'}
        used=cache.get('bytes currently in the cache')
        capacity=cache.get('maximum bytes configured')
        requested=cache.get('pages requested from the cache')
        loaded=cache.get('pages read into cache')
        return {'available':True,'cache_bytes':used,'configured_cache_bytes':capacity,
                'cache_occupancy_pct':round(100*used/capacity,2) if used is not None and capacity else None,
                'pages_requested':requested,'pages_read_into_cache':loaded}
    except Exception as exc:
        return {'available':False,'reason':str(exc)}

def hit_proxy(before,after):
    if not before.get('available') or not after.get('available'):
        return None
    a,b=before.get('pages_requested'),after.get('pages_requested')
    c,d=before.get('pages_read_into_cache'),after.get('pages_read_into_cache')
    if any(x is None for x in (a,b,c,d)) or b<=a:
        return None
    # Proxy only; page requests and physical loads are not strict 1:1 hits/misses.
    return round(max(0,min(100,100*(1-(d-c)/(b-a)))),2)

def run():
    db=get_db()
    coll=db['working_set']
    coll.drop()
    payload='x'*1850
    for start in range(0,COUNT,1000):
        batch=[{'_id':i,'platform':('Linux','Windows','macOS')[i%3],
                'threat_type':'synthetic_benchmark','ordinal':i,'payload':payload}
               for i in range(start,min(COUNT,start+1000))]
        coll.insert_many(batch)
        if (start+1000)%20000==0:
            print('Inserted:',min(COUNT,start+1000),flush=True)
    print('Document BSON bytes:',len(BSON.encode(coll.find_one({'_id':0}))))
    rng=random.Random(2026)
    before=cache_snapshot(db)
    print('Cache baseline:',json.dumps(before))
    for phase in range(1,4):
        start_time=time.perf_counter()
        for _ in range(3000):
            coll.find_one({'_id':rng.randrange(COUNT)}, {'payload':1})
        after=cache_snapshot(db)
        print(f'Phase {phase}: 3000 reads in {time.perf_counter()-start_time:.2f}s; '
              f'occupancy={after.get("cache_occupancy_pct")}; '
              f'approximate hit proxy={hit_proxy(before,after)}')
        before=after
    print('Cache occupancy is not percent of the dataset cached; hit proxy is not exact.')

if __name__=='__main__':
    run()
