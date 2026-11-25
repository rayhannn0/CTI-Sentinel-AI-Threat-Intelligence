# Lab 18.1: four patterns x three databases x 10 repeats
import argparse, json, csv, statistics, time
from datetime import timezone
from pathlib import Path
from pymongo import InsertOne
from cassandra.concurrent import execute_concurrent_with_args
from app.model import make_threat
from app.db import mongo_client,cassandra_cluster,graph_driver

OUT=Path('output'); OUT.mkdir(exist_ok=True)
RUNS=10

def ms(f):
    start=time.perf_counter(); result=f(); return (time.perf_counter()-start)*1000, result

def benchmark():
    mc=mongo_client(); db=mc.threat_intel;cc=cassandra_cluster();cs=cc.connect('threat_intel');gd=graph_driver()
    if db.full_threats.count_documents({})==0: raise RuntimeError('Seed first: python -m scripts.seed --count 1000')
    source='sensor-01';target='host-001';day='2026-11-20'
    q_source=cs.prepare('SELECT * FROM threats_by_source WHERE from_source=? LIMIT 50')
    q_target=cs.prepare('SELECT * FROM threats_by_target WHERE target=? LIMIT 50')
    q_daily=cs.prepare('SELECT * FROM daily_volume WHERE day=?')
    def mongo_history(): return list(db.full_threats.find({'from_source':source}).sort('timestamp',-1).limit(50))
    def cass_history(): return list(cs.execute(q_source,(source,)))
    def neo_history():
        with gd.session() as s:return s.run('MATCH (s:Source {id:$src})-[:REPORTED]->(t:Threat) RETURN t.id AS id ORDER BY t.timestamp DESC LIMIT 50',src=source).data()
    def mongo_spread():return list(db.full_threats.find({'target':target}).sort('timestamp',-1).limit(50))
    def cass_spread():return list(cs.execute(q_target,(target,)))
    def neo_spread():
        with gd.session() as s:return s.run('MATCH (s:Source)-[:REPORTED]->(t:Threat {target:$target}) RETURN s.id AS source,t.id AS threat LIMIT 50',target=target).data()
    def mongo_volume():return list(db.full_threats.aggregate([{'$match':{'day':day}},{'$group':{'_id':'$from_source','n':{'$sum':1}}}]))
    def cass_volume():return list(cs.execute(q_daily,(day,)))
    def neo_volume():
        with gd.session() as s:return s.run('MATCH (s:Source)-[:REPORTED]->(t:Threat {day:$day}) RETURN s.id AS source,count(t) AS n',day=day).data()
    methods={
      'threat_history':{'mongodb':mongo_history,'cassandra':cass_history,'neo4j':neo_history},
      'target_spread':{'mongodb':mongo_spread,'cassandra':cass_spread,'neo4j':neo_spread},
      'daily_volume':{'mongodb':mongo_volume,'cassandra':cass_volume,'neo4j':neo_volume},
    }
    results=[]
    for pattern,engines in methods.items():
        for backend,fn in engines.items():
            samples=[]
            for k in range(RUNS):
                duration,result=ms(fn);samples.append(duration)
                if k==0:print(f'{pattern} {backend}: returned {len(result)} rows')
            results.append({'pattern':pattern,'backend':backend,'runs':RUNS,'median_ms':round(statistics.median(samples),3),'samples_ms':[round(x,3) for x in samples]})
            print(f'{pattern:<20} {backend:<10} median {statistics.median(samples):.3f} ms')
    # Throughput: batch of 10 fresh records per run; includes application & network latency.
    q1=cs.prepare('INSERT INTO threats_by_source (from_source,timestamp,threat_id,target,threat_type,fingerprint,confidence,is_false_positive) VALUES (?,?,?,?,?,?,?,?)')
    q2=cs.prepare('INSERT INTO threats_by_type (threat_type,timestamp,threat_id,from_source,target,confidence) VALUES (?,?,?,?,?,?)')
    q3=cs.prepare('INSERT INTO threats_by_target (target,timestamp,threat_id,from_source,threat_type) VALUES (?,?,?,?,?)')
    for backend in ('mongodb','cassandra','neo4j'):
        samples=[]; size=10
        for run in range(RUNS):
            # different IDs for each backend; benchmark records deliberately retained
            offset={'mongodb':10000000,'cassandra':11000000,'neo4j':12000000}[backend]
            batch=[make_threat(offset+run*size+i) for i in range(size)]
            def insert_batch():
                if backend=='mongodb':
                    db.full_threats.insert_many(batch,ordered=False)
                elif backend=='cassandra':
                    for stmt,rows in ((q1,[(x['from_source'],x['timestamp'],x['threat_id'],x['target'],x['threat_type'],x['fingerprint'],x['confidence'],x['is_false_positive']) for x in batch]),
                                      (q2,[(x['threat_type'],x['timestamp'],x['threat_id'],x['from_source'],x['target'],x['confidence']) for x in batch]),
                                      (q3,[(x['target'],x['timestamp'],x['threat_id'],x['from_source'],x['threat_type']) for x in batch])):
                        outcomes=execute_concurrent_with_args(cs,stmt,rows,concurrency=20,raise_on_first_error=False)
                        if not all(ok for ok,_ in outcomes):raise RuntimeError('Cassandra insertion error')
                else:
                    with gd.session() as s:
                        s.run('''UNWIND $rows AS r
                            MERGE (src:Source {id:r.from_source})
                            CREATE (t:Threat {id:r.threat_id, timestamp:datetime(r.timestamp), day:r.day,
                                target:r.target, threat_type:r.threat_type})
                            CREATE (src)-[:REPORTED]->(t)''',rows=[dict(x,timestamp=x['timestamp'].isoformat()) for x in batch]).consume()
            d,_=ms(insert_batch);samples.append(d)
        med=statistics.median(samples)
        results.append({'pattern':'insert_10_events','backend':backend,'runs':RUNS,'median_ms':round(med,3),'events_per_sec':round(10000/med,1),'samples_ms':[round(x,3) for x in samples]})
        print(f'insert_10_events     {backend:<10} median {med:.3f} ms; ~{10000/med:.1f} events/s')
    payload={'data':'synthetic, not live threats','note':'Single-node Docker laptop; Cassandra daily_volume preaggregated, unlike Mongo/Neo4j live aggregation. Insert benchmark writes 3 Cassandra tables. Side effects: benchmark inserts remain in stores. Results are non-production.',
        'seeded_mongo_events_before_benchmark': (db.seed_metadata.find_one({'_id':'seed'}) or {}).get('seed_count', 'unknown'),'runs_per_pattern':10,'results':results}
    (OUT/'benchmark.json').write_text(json.dumps(payload,indent=2))
    with (OUT/'benchmark.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['pattern','backend','runs','median_ms','events_per_sec'])
        for r in results:writer.writerow([r['pattern'],r['backend'],r['runs'],r['median_ms'],r.get('events_per_sec','')])
    print('BENCHMARK COMPLETE: output/benchmark.json + output/benchmark.csv')
    mc.close();cc.shutdown();gd.close()

if __name__=='__main__':benchmark()
