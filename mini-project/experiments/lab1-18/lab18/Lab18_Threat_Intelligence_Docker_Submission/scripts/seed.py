# Seed the same deterministic synthetic event stream into three engines.

# Usage: python -m scripts.seed --count 1000   [smoke]
#        python -m scripts.seed --count 100000 [assignment]
# Cassandra inserts are asynchronous and may take substantial time.
import argparse
from collections import Counter, defaultdict
from pymongo import ReplaceOne
from cassandra.concurrent import execute_concurrent_with_args
from app.model import generate
from app.db import mongo_client, cassandra_cluster, graph_driver
from app.setup import setup_mongo, setup_cassandra, setup_neo4j

BATCH = 500

def seed(count):
    mc=mongo_client(); db=mc['threat_intel']; setup_mongo(db)
    cc=cassandra_cluster(); cs=cc.connect(); setup_cassandra(cs)
    gd=graph_driver(); setup_neo4j(gd)
    q_source=cs.prepare('INSERT INTO threats_by_source (from_source,timestamp,threat_id,target,threat_type,fingerprint,confidence,is_false_positive) VALUES (?,?,?,?,?,?,?,?)')
    q_type=cs.prepare('INSERT INTO threats_by_type (threat_type,timestamp,threat_id,from_source,target,confidence) VALUES (?,?,?,?,?,?)')
    q_target=cs.prepare('INSERT INTO threats_by_target (target,timestamp,threat_id,from_source,threat_type) VALUES (?,?,?,?,?)')
    daily=Counter(); recent=defaultdict(list); totals=Counter()
    for start in range(0,count,BATCH):
        batch=list(generate_range(start, min(start+BATCH,count)))
        ops=[ReplaceOne({'threat_id':x['threat_id']},x,upsert=True) for x in batch]
        db.full_threats.bulk_write(ops, ordered=False)
        rows1=[(x['from_source'],x['timestamp'],x['threat_id'],x['target'],x['threat_type'],x['fingerprint'],x['confidence'],x['is_false_positive']) for x in batch]
        rows2=[(x['threat_type'],x['timestamp'],x['threat_id'],x['from_source'],x['target'],x['confidence']) for x in batch]
        rows3=[(x['target'],x['timestamp'],x['threat_id'],x['from_source'],x['threat_type']) for x in batch]
        for statement, rows in ((q_source,rows1),(q_type,rows2),(q_target,rows3)):
            results=execute_concurrent_with_args(cs,statement,rows, concurrency=64,raise_on_first_error=False)
            failures=[repr(exc) for ok, exc in results if not ok]
            if failures: raise RuntimeError(f'Cassandra writes failed: {failures[:2]}')
        with gd.session() as gs:
            gs.run('''UNWIND $rows AS r
                MERGE (s:Source {id:r.from_source})
                MERGE (t:Threat {id:r.threat_id})
                SET t.timestamp=datetime(r.timestamp), t.day=r.day,
                    t.target=r.target, t.threat_type=r.threat_type,
                    t.fingerprint=r.fingerprint,t.confidence=r.confidence,
                    t.is_false_positive=r.is_false_positive
                MERGE (s)-[:REPORTED]->(t)''', rows=[dict(x, timestamp=x['timestamp'].isoformat()) for x in batch]).consume()
        for x in batch:
            daily[(x['day'],x['from_source'])]+=1; totals[x['from_source']]+=1
            recent[x['from_source']].append(x)
            recent[x['from_source']]=recent[x['from_source']][-50:]
        print(f'Inserted {min(start+BATCH,count):,}/{count:,} across all 3 stores', flush=True)
    q_daily=cs.prepare('INSERT INTO daily_volume (day,from_source,volume) VALUES (?,?,?)')
    execute_concurrent_with_args(cs,q_daily,[(d,s,n) for (d,s),n in daily.items()],concurrency=32)
    # MongoDB source summaries with last 50 readings
    for src, items in recent.items():
        db.threats.replace_one({'from_source':src}, {'from_source':src, 'total_count':totals[src], 'recent_threats': sorted(items,key=lambda x:x['timestamp'], reverse=True)[:50]},upsert=True)
    # Build shared-fingerprint source connections, then expose explicit SUSPICIOUS edges.
    with gd.session() as gs:
        gs.run('''MATCH (s:Source)-[:REPORTED]->(t:Threat)
            WITH s, t.fingerprint AS fp, count(*) AS n
            WHERE n >= 3
            WITH fp, collect(s.id) AS ids
            UNWIND ids AS a UNWIND ids AS b
            WITH a,b,count(DISTINCT fp) AS shared WHERE a < b
            MATCH (s1:Source {id:a}),(s2:Source {id:b})
            MERGE (s1)-[r:SUSPICIOUS]-(s2)
            SET r.shared_fingerprints=shared''').consume()
    db.seed_metadata.replace_one({'_id':'seed'}, {'_id':'seed','seed_count':count}, upsert=True)
    print('SEED COMPLETE; database MongoDB=threat_intel, keyspace Cassandra=threat_intel, Neo4j=neo4j')
    print('Synthetic records:',count,'; NOT real-world threat events')
    mc.close();cc.shutdown();gd.close()

def generate_range(a,b):
    from app.model import make_threat
    for i in range(a,b):yield make_threat(i)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--count',type=int,default=1000)
    n=a.parse_args().count
    if n<1: raise SystemExit('count must be >= 1')
    seed(n)
