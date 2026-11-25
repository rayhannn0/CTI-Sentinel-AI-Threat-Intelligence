"""Local, read-only dashboard for NoSQL Labs 1–18.
Run: pip install -r requirements.txt && python server.py
Live data is read from your existing MongoDB and local Lab 18 benchmark files.
"""
import csv
import io
import json
import os
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parent
MONGO_URI = os.environ.get('LAB18_THREAT_URI', 'mongodb://127.0.0.1:27021')
DEFAULT_OUTPUT = Path.home() / 'Downloads/lab18/Lab18_Threat_Intelligence_Docker_Submission/output'
OUTPUT = Path(os.environ.get('LAB18_OUTPUT_DIR', str(DEFAULT_OUTPUT))).expanduser()
app = FastAPI(title='NoSQL Lab Atlas', version='1.0')
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

LABS = json.loads((ROOT / 'data' / 'lab_catalog.json').read_text())


def mongo_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1200, connectTimeoutMS=1200)
    client.admin.command('ping')
    return client, client['threat_intel']


def clean(doc):
    if isinstance(doc, dict): return {k: clean(v) for k, v in doc.items() if k != '_id'}
    if isinstance(doc, list): return [clean(v) for v in doc]
    if isinstance(doc, datetime): return doc.isoformat()
    return doc


def is_up(port, host='127.0.0.1'):
    try:
        with socket.create_connection((host, port), timeout=0.6): return True
    except OSError: return False


def docker_containers():
    try:
        output = subprocess.run(['docker', 'ps', '--format', '{{.Names}}|{{.Status}}'], capture_output=True, text=True, timeout=3, check=True).stdout
        return [{'name': fields[0], 'status': fields[1]} for line in output.splitlines() if len(fields := line.split('|', 1)) == 2 and ('lab1' in fields[0].lower())]
    except (OSError, subprocess.SubprocessError): return []


def benchmark_data():
    path = OUTPUT / 'benchmark.csv'
    if path.is_file():
        try:
            with path.open(newline='') as f: records = list(csv.DictReader(f))
            return {'source': 'local Lab 18 benchmark.csv', 'path': str(path), 'rows': records, 'live_file': True}
        except (OSError, csv.Error): pass
    with (ROOT / 'data' / 'benchmark_snapshot.csv').open(newline='') as f: records = list(csv.DictReader(f))
    return {'source': 'saved results from your Terminal (not a new measurement)', 'path': '', 'rows': records, 'live_file': False}


@app.get('/')
def index(): return FileResponse(ROOT / 'static/dashboard.html', headers={'Cache-Control':'no-store, max-age=0'})


@app.get('/api/labs')
def labs(): return {'labs': LABS, 'note': 'All 18 lab topics and activity instructions are documented. Labs 1–14 still need your own scripts and runtime results.'}


@app.get('/api/status')
def status():
    containers = docker_containers()
    services = [
        {'label': 'Lab 18 · MongoDB', 'online': is_up(27021), 'detail': 'localhost:27021'},
        {'label': 'Lab 18 · Neo4j', 'online': is_up(7476), 'detail': 'localhost:7476'},
        {'label': 'Lab 15 · TaskTracker API', 'online': is_up(8000), 'detail': 'localhost:8000'},
    ]
    c = next((x for x in containers if 'lab18' in x['name'] and 'cassandra' in x['name']), None)
    services.append({'label': 'Lab 18 · Cassandra', 'online': bool(c and ('Up' in c['status'])), 'detail': c['status'] if c else 'Not detected by Docker CLI'})
    return {'services': services, 'containers': containers, 'checked_at': datetime.now(timezone.utc).isoformat(), 'mongo_url': 'localhost:27021', 'benchmark': benchmark_data()['source']}


@app.get('/api/overview')
def overview():
    result = {'connected': False, 'total': None, 'false_positive': None, 'sources': None, 'targets': None, 'types': [], 'recent': [], 'seed_count': None}
    try:
        client, db = mongo_db()
        try:
            result['connected'] = True
            result['total'] = db.full_threats.estimated_document_count()
            metadata = db.seed_metadata.find_one({'_id':'seed'}, {'seed_count':1}) or {}
            result['seed_count'] = metadata.get('seed_count')
            result['false_positive'] = db.full_threats.count_documents({'is_false_positive': True}, maxTimeMS=5000)
            result['sources'] = len(db.full_threats.distinct('from_source'))
            result['targets'] = len(db.full_threats.distinct('target'))
            result['types'] = clean(list(db.full_threats.aggregate([
                {'$group': {'_id': '$threat_type', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}], maxTimeMS=5000)))
            result['recent'] = clean(list(db.full_threats.find({}, {'_id':0}).sort('timestamp', -1).limit(8)))
        finally: client.close()
    except (PyMongoError, OSError) as e: result['error'] = str(e).split('\n')[0][:220]
    return result


@app.get('/api/threats')
def threats(q: str = Query('', max_length=80), kind: str = Query('all'), limit: int = Query(40, ge=1, le=100)):
    filt = {}
    if q.strip():
        pattern = re.escape(q.strip())
        fields = ['threat_id', 'from_source', 'target', 'fingerprint', 'threat_type']
        filt = {'$or': [{field: {'$regex': pattern, '$options': 'i'}} for field in fields]}
    if kind == 'flagged': filt['is_false_positive'] = True
    elif kind == 'other': filt['is_false_positive'] = False
    try:
        client, db = mongo_db()
        try:
            results = clean(list(db.full_threats.find(filt, {'_id':0}).sort('timestamp',-1).limit(limit)))
            return {'connected': True, 'items': results, 'count': len(results), 'note': 'Synthetic lab events, not a live security feed.'}
        finally: client.close()
    except (PyMongoError, OSError) as e:
        return {'connected': False, 'items': [], 'count': 0, 'error': str(e).split('\n')[0][:180]}


@app.get('/api/benchmark')
def benchmark(): return benchmark_data()


@app.get('/api/communities')
def communities():
    path = OUTPUT / 'communities.json'
    if path.is_file():
        try: return {'available': True, 'data': json.loads(path.read_text()), 'source': str(path)}
        except (ValueError, OSError): pass
    return {'available': False, 'message': 'Run docker compose exec app python -m scripts.communities in Lab 18.'}


@app.get('/api/chat')
def chat(message: str = Query(..., min_length=2, max_length=250)):
    question = message.strip().lower()
    if any(x in question for x in ('benchmark', 'fastest', 'latency', 'throughput')):
        rows = benchmark_data()['rows']
        return {'answer': 'These are your saved local measurements, not real-time query timings. Select Benchmarks for the full chart.', 'kind': 'benchmark', 'rows': rows[:12]}
    if any(x in question for x in ('status', 'online', 'database', 'connected')):
        current = status()['services']
        return {'answer': '; '.join(f"{s['label']}: {'online' if s['online'] else 'offline'}" for s in current), 'kind': 'status'}
    if any(x in question for x in ('false positive', 'flagged')):
        data = overview()
        if not data['connected']: return {'answer':'MongoDB is offline. Start your Lab 18 Docker Compose stack to ask questions about its synthetic threat events.', 'kind':'offline'}
        return {'answer':f"The database currently contains {data['false_positive']:,} synthetic events marked as false positives out of approximately {data['total']:,} total records. This is a teaching heuristic based on generated confidence, not verified security evidence.", 'kind':'count'}
    match = re.search(r'(sensor-\d\d|host-\d\d\d|th-\d+|ioc-\d+)', question)
    if match:
        term = match.group(1)
        data = threats(q=term, limit=5)
        if not data['connected']: return {'answer': 'MongoDB is currently unavailable. Start Lab 18 to inspect threat records.', 'kind':'offline'}
        return {'answer':f"Found {data['count']} matching recent events for {term} (showing at most five). These records are synthetic.", 'kind':'events', 'events':data['items']}
    return {'answer':'I can query your Lab 18 synthetic data. Try “false positives”, “sensor-01”, “host-001”, “benchmark”, or “database status”. This is a rule-based local assistant, not an LLM, and it cannot scan or mitigate real threats.', 'kind':'help'}



# Each action is an explicitly allowlisted lab operation, never arbitrary code execution.
from pydantic import BaseModel, Field
from fastapi import HTTPException
from workbench import catalog as workbench_catalog, run as workbench_run, Prerequisite

class WorkbenchRequest(BaseModel):
    lab: int = Field(ge=1, le=18)
    action: str = Field(min_length=1, max_length=32, pattern=r'^[a-z_]+$')

@app.get('/api/workbench/labs')
def workbench_labs():
    return {'labs': workbench_catalog(LABS), 'data_source': 'MongoDB Docker at 127.0.0.1:27021; separate demo database lab_atlas_demos'}

@app.post('/api/workbench/run')
def workbench_action(req: WorkbenchRequest):
    from pymongo.errors import PyMongoError
    try:
        return workbench_run(req.lab, req.action)
    except Prerequisite as e:
        return {'ok': False, 'prerequisite': True, 'message': str(e)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PyMongoError as e:
        return {'ok': False, 'message': 'Database operation failed: ' + str(e).split('\n')[0][:300]}
    except Exception as e:
        return {'ok': False, 'message': type(e).__name__ + ': ' + str(e).split('\n')[0][:260]}

@app.get('/workbench')
def workbench_home():
    return FileResponse(ROOT / 'static/workbench.html')


# New: visual, user-driven live models (validated and allowlisted).
from studio import list_data as studio_list, command as studio_command
from typing import Any
class StudioCommand(BaseModel):
    lab: int = Field(ge=1,le=18)
    operation: str = Field(min_length=1,max_length=30,pattern=r'^[a-z_]+$')
    data: dict[str,Any] = Field(default_factory=dict)

@app.get('/models')
def models_home():
    return FileResponse(ROOT / 'static/models.html')

@app.get('/api/models/{lab}')
def models_data(lab: int, q: str='', tenant: str='tenant-1', type: str='all', flagged: str='',limit:int=35):
    if not 1<=lab<=18:raise HTTPException(status_code=404,detail='Unknown lab')
    try:return {'ok':True,**studio_list(lab,{'q':q,'tenant':tenant,'type':type,'flagged':flagged,'limit':limit})}
    except (ValueError,PyMongoError) as e:return {'ok':False,'message':str(e).split('\n')[0][:280]}

@app.post('/api/models/command')
def models_command(req: StudioCommand):
    try:return {'ok':True,**studio_command(req.lab,req.operation,req.data)}
    except (ValueError,PyMongoError) as e:return {'ok':False,'message':str(e).split('\n')[0][:280]}

# Sentinel dashboard (preserves all existing interactive lab routes)
from sentinel import TransferRequest, balances as sentinel_balances, reset as sentinel_reset, transfer as sentinel_transfer

@app.get('/sentinel')
def sentinel_page():
    return FileResponse(ROOT / 'static/sentinel.html', headers={'Cache-Control':'no-store, max-age=0'})

# Lab 11: read-only statistics from the user's existing mongos router.
# This endpoint does not insert, migrate, drop, or rebalance any documents.
@app.get('/api/sentinel/lab11/live')
def live_lab11_stats(collection: str = Query('even_data')):
    if collection not in ('even_data', 'hotspot_data'):
        raise HTTPException(status_code=400, detail='Unsupported Lab 11 collection')
    uri = os.environ.get('LAB11_MONGOS_URI', 'mongodb://127.0.0.1:27517/?directConnection=true')
    client = MongoClient(uri, serverSelectionTimeoutMS=3000, socketTimeoutMS=5000)
    try:
        hello = client.admin.command('hello')
        if hello.get('msg') != 'isdbgrid':
            return {'ok':False,'message':'Port is not a mongos router; connect to Lab 11 mongos on port 27517.'}
        shards = client.admin.command({'listShards': 1}).get('shards', [])
        ns = 'lab11.' + collection
        coll = client['lab11'][collection]
        collection_meta = client['config']['collections'].find_one({'_id': ns})
        if not collection_meta:
            return {'ok':False,'message':ns+' is not a sharded collection'}
        uuid = collection_meta.get('uuid')
        chunks = {}
        if uuid is not None:
            for row in client['config']['chunks'].aggregate([
                {'$match': {'uuid': uuid}},
                {'$group': {'_id': '$shard', 'count': {'$sum': 1}}}
            ]):
                chunks[row['_id']] = row['count']
        # The server-side sharded data distribution diagnostic reports *owned*
        # documents, excluding orphans. This is preferred to per-shard collStats.
        owned = {}
        try:
            result = client.admin.command({'aggregate': 1, 'pipeline': [{'$shardedDataDistribution': {}}], 'cursor': {}})
            batches = result.get('cursor',{}).get('firstBatch',[])
            for item in batches:
                if item.get('ns') == ns:
                    owned = {x['shardName']:int(x['numOwnedDocuments']) for x in item.get('shards',[])}
                    break
        except Exception:
            pass
        if not owned:
            stats = client['lab11'].command({'collStats':collection})
            for name, row in stats.get('shards',{}).items():
                owned[name] = int(row.get('count',0))
        result_shards = [{'name':s['_id'], 'host':s['host'], 'documents':owned.get(s['_id'],0), 'chunks':chunks.get(s['_id'],0)} for s in shards]
        total = sum(x['documents'] for x in result_shards)
        return {'ok':True, 'source':'live mongos', 'collection':ns, 'shard_key':str(collection_meta.get('key',{})), 'shards':result_shards, 'total':total, 'chunk_count':sum(chunks.values()), 'note':'Actual sharded collection metadata and document counts. Query timings are not measured.'}
    except Exception as e:
        return {'ok':False,'message':str(e).split('\n')[0][:280]}
    finally:
        client.close()

@app.get('/api/sentinel/bank')
def sentinel_bank():
    try: return {'ok':True,**sentinel_balances()}
    except Exception as e: return {'ok':False,'message':str(e).split('\n')[0][:260]}

@app.post('/api/sentinel/bank/reset')
def sentinel_reset_api():
    try: return sentinel_reset()
    except Exception as e: return {'ok':False,'message':str(e).split('\n')[0][:260]}

@app.post('/api/sentinel/bank/transfer')
def sentinel_transfer_api(req:TransferRequest):
    try: return sentinel_transfer(req)
    except Exception as e: return {'ok':False,'message':str(e).split('\n')[0][:260]}


# Lab 12 standalone, isolated MongoDB collection with enforced $jsonSchema.
# This exercise is separate from the Lab 12 RBAC/TLS installation exercises.
from pymongo.errors import OperationFailure, WriteError
from pydantic import BaseModel, Field
from bson import json_util

LAB12_DB = 'lab12_ui_validation'
LAB12_COLL = 'security_events'
LAB12_SCHEMA = {
    'bsonType':'object',
    'required':['email','age','severity'],
    'properties':{
       'email':{'bsonType':'string','pattern':r'^[^\s@]+@[^\s@]+\.[^\s@]+$'},
       'age':{'bsonType':'int','minimum':18,'maximum':120},
       'severity':{'enum':['LOW','MEDIUM','HIGH','CRITICAL']}
    }
}

class Lab12Submission(BaseModel):
    email: str = Field(min_length=1,max_length=180)
    age: int = Field(ge=-200,le=500)
    severity: str = Field(min_length=1,max_length=35)

def lab12_client():
    uri = os.environ.get('LAB12_MONGO_URI', 'mongodb://127.0.0.1:27022/?replicaSet=rsLab10')
    client = MongoClient(uri,serverSelectionTimeoutMS=3000,connectTimeoutMS=3000)
    client.admin.command('ping')
    return client

def lab12_ensure_schema(db):
    if LAB12_COLL not in db.list_collection_names():
        try:
            db.create_collection(LAB12_COLL,validator={'$jsonSchema':LAB12_SCHEMA},validationLevel='strict',validationAction='error')
            return
        except OperationFailure as ex:
            if ex.code!=48: raise  # NamespaceExists race
    db.command({'collMod':LAB12_COLL,'validator':{'$jsonSchema':LAB12_SCHEMA},'validationLevel':'strict','validationAction':'error'})

@app.get('/api/sentinel/lab12/records')
def lab12_records():
    client=None
    try:
        client=lab12_client()
        db=client[LAB12_DB]
        rows=list(db[LAB12_COLL].find({}, {'_id':0,'email':1,'age':1,'severity':1,'created_at':1}).sort('created_at',-1).limit(8))
        return {'ok':True,'records':clean(rows),'count':db[LAB12_COLL].count_documents({}),'database':LAB12_DB+'.'+LAB12_COLL}
    except Exception as e:
        return {'ok':False,'message':str(e).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()

@app.post('/api/sentinel/lab12/validate')
def lab12_validate(req:Lab12Submission):
    email=req.email.strip(); severity=req.severity.strip().upper(); age=req.age
    email_ok=bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email))
    age_ok=18<=age<=120; severity_ok=severity in ('LOW','MEDIUM','HIGH','CRITICAL')
    checks={'email':email_ok,'age':age_ok,'severity':severity_ok}
    # An invalid document is deliberately submitted to exercise MongoDB's own validator.
    client=None
    try:
        client=lab12_client(); db=client[LAB12_DB];lab12_ensure_schema(db)
        document={'email':email,'age':age,'severity':severity,'created_at':datetime.now(timezone.utc)}
        try:
            db[LAB12_COLL].insert_one(document)
            return {'ok':True,'committed':True,'checks':checks,'message':'MongoDB accepted document under enforced $jsonSchema.','database':LAB12_DB+'.'+LAB12_COLL}
        except WriteError as e:
            if e.code==121:
                return {'ok':True,'committed':False,'checks':checks,'message':'MongoDB rejected document (error 121): $jsonSchema validation failed. No document was saved.','database':LAB12_DB+'.'+LAB12_COLL}
            raise
    except Exception as e:
        return {'ok':False,'committed':False,'checks':checks,'message':str(e).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()


# Lab 13: real MongoDB projection view and read-only view enforcement.
# The role selector is a training preview, NOT authenticated MongoDB RBAC or CSFLE.
from hashlib import sha256
from fastapi import HTTPException

LAB13_DB = 'lab13_security_demo'
LAB13_COLLECTION = 'analysts'
LAB13_VIEW = 'analysts_public'

def lab13_open():
    # Reuse the working rsLab10 local MongoDB; all writes limited to LAB13_DB.
    return lab12_client()

def lab13_prepare(db):
    source=db[LAB13_COLLECTION]
    seeded=[
        {'analyst_id':'ANALYST-122','name':'Demo Analyst A','clearance':'TOP_SECRET_CTI','department':'Threat Research'},
        {'analyst_id':'ANALYST-108','name':'Demo Analyst B','clearance':'SECRET_SOC','department':'SOC Operations'}
    ]
    for doc in seeded:
        id_=doc['analyst_id']
        # Fictional hashes are only sample ciphertext-like placeholders, not CSFLE.
        seed={**doc,'gov_id_ciphertext':'DEMO_ONLY_'+sha256((id_+'-fake-gov-id').encode()).hexdigest(),
              'api_token_hash':sha256((id_+'-fake-token').encode()).hexdigest(),
              'created_at':datetime.now(timezone.utc)}
        source.update_one({'analyst_id':id_},{'$setOnInsert':seed},upsert=True)
    if LAB13_VIEW not in db.list_collection_names():
        try:
            db.command({'create':LAB13_VIEW,'viewOn':LAB13_COLLECTION,'pipeline':[{'$project':{
                '_id':0,'analyst_id':1,'name':1,'clearance':1,'department':1
            }}]})
        except OperationFailure as ex:
            if ex.code!=48: raise

@app.get('/api/sentinel/lab13/projection')
def lab13_projection(role:str=Query('analyst',pattern='^(analyst|auditor|admin)$')):
    client=None
    try:
        client=lab13_open();db=client[LAB13_DB];lab13_prepare(db)
        # The view is queried by MongoDB; it never exposes the sensitive fields.
        public=list(db[LAB13_VIEW].find({}, {'_id':0}).sort('analyst_id',1).limit(25))
        if role=='admin':
            # Compare to direct collection access but do not leak credential materials.
            by_id={r['analyst_id']:r for r in db[LAB13_COLLECTION].find({}, {'_id':0,'analyst_id':1,'gov_id_ciphertext':1,'api_token_hash':1})}
        else:by_id={}
        records=[]
        for r in public:
            fields=by_id.get(r['analyst_id'],{})
            records.append({**r,'gov_id_display':('[OPAQUE SAMPLE: '+str(fields.get('gov_id_ciphertext',''))[:18]+'…]' if role=='admin' else '[REDACTED BY MONGODB VIEW]'),
                'api_token_display':('[HASH PRESENT; HIDDEN]' if role=='admin' else '[NOT IN VIEW]')})
        return {'ok':True,'database':LAB13_DB,'source':LAB13_VIEW,'view_exists':True,'role_preview':role,
                'records':records,'message':'Queried real MongoDB view; sensitive fields are excluded by $project. The selected role is a UI preview, not DB-enforced authentication.'}
    except Exception as ex:
        return {'ok':False,'message':str(ex).split('\n')[0][:350]}
    finally:
        if client is not None:client.close()

@app.post('/api/sentinel/lab13/view-write-test')
def lab13_view_write_test():
    client=None
    try:
        client=lab13_open();db=client[LAB13_DB];lab13_prepare(db)
        try:
            db[LAB13_VIEW].insert_one({'analyst_id':'VIEW-TEST-UNWRITABLE','name':'Must Reject','clearance':'NONE'})
            return {'ok':False,'message':'Unexpectedly succeeded; investigate database view configuration.'}
        except OperationFailure as ex:
            return {'ok':True,'code':ex.code,'message':'MongoDB rejected the insert into the read-only projection view. No analyst document was added. This proves view read-only behavior, not authenticated RBAC.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:350]}
    finally:
        if client is not None:client.close()



# Lab 14 — read-only serverStatus telemetry and reversible, isolated JSON backups.
LAB14_DB = 'lab14_monitoring_demo'
LAB14_COLLECTION = 'backup_test_records'
LAB14_BACKUPS = ROOT / 'output' / 'lab14_backups'

def lab14_open():
    return lab12_client()

@app.get('/api/sentinel/lab14/telemetry')
def lab14_telemetry(threshold:float=Query(80, ge=1, le=100)):
    client=None
    try:
        client=lab14_open()
        status=client.admin.command('serverStatus')
        conn=status.get('connections',{})
        cache=status.get('wiredTiger',{}).get('cache',{})
        # These are cumulative counters; this is a proxy, not an authoritative cache hit SLA.
        requested=cache.get('pages requested from the cache')
        read_in=cache.get('pages read into cache')
        proxy=None
        if isinstance(requested,(int,float)) and isinstance(read_in,(int,float)) and requested>0:
            proxy=round(max(0,min(100,100*(1-read_in/requested))),2)
        return {'ok':True,'source':'MongoDB serverStatus','measured_at':datetime.now(timezone.utc).isoformat(),
            'connections':{'current':conn.get('current'), 'available':conn.get('available'), 'total_created':conn.get('totalCreated')},
            'wired_tiger':{'pages_requested':requested,'pages_read_into_cache':read_in,'cache_bytes_in_use':cache.get('bytes currently in the cache'),
                'maximum_cache_bytes':cache.get('maximum bytes configured')},
            'cache_hit_proxy_pct':proxy,'threshold_pct':threshold,
            'sla_status':('PROXY ABOVE THRESHOLD' if proxy>=threshold else 'PROXY BELOW THRESHOLD') if proxy is not None else 'NOT MEASURABLE',
            'is_proxy':True,'message':'Cache percentage is estimated from cumulative WiredTiger page counters; it is not a measured request cache-hit SLA. Connection counts are live serverStatus values.'}
    except Exception as exc:
        return {'ok':False,'message':str(exc).split('\n')[0][:350]}
    finally:
        if client is not None:client.close()

def lab14_seed_if_empty(db):
    coll=db[LAB14_COLLECTION]
    if coll.estimated_document_count()==0:
        coll.insert_many([{'record_id':f'DEMO-{i:03d}','source':'Lab14 sample','event':'Threat triage checkpoint','severity':x}
            for i,x in enumerate(['LOW','MEDIUM','HIGH','LOW','CRITICAL'],1)])
    return coll

@app.post('/api/sentinel/lab14/backup')
def lab14_backup():
    import hashlib
    client=None
    try:
        client=lab14_open();db=client[LAB14_DB]
        coll=lab14_seed_if_empty(db)
        docs=list(coll.find({},{'_id':0}).sort('record_id',1).limit(500))
        LAB14_BACKUPS.mkdir(parents=True,exist_ok=True)
        data=json.dumps(docs,sort_keys=True,indent=2,default=str).encode('utf-8')
        digest=hashlib.sha256(data).hexdigest()
        name='lab14_snapshot_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'
        target=LAB14_BACKUPS/name
        target.write_bytes(data)
        return {'ok':True,'filename':name,'sha256':digest,'count':len(docs),'bytes':len(data),
                'message':'Created an isolated, read-only JSON snapshot of lab14_monitoring_demo records. This is not a mongodump, point-in-time backup, or production restore test.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:350]}
    finally:
        if client is not None:client.close()

@app.get('/api/sentinel/lab14/verify')
def lab14_verify():
    import hashlib
    try:
        files=sorted(LAB14_BACKUPS.glob('lab14_snapshot_*.json')) if LAB14_BACKUPS.exists() else []
        if not files:return {'ok':False,'message':'No Lab 14 JSON snapshot yet. Click Create demo snapshot first.'}
        path=files[-1]; content=path.read_bytes();rows=json.loads(content)
        if not isinstance(rows,list) or not all(isinstance(x,dict) and 'record_id' in x for x in rows):
            return {'ok':False,'message':'Snapshot format invalid.'}
        return {'ok':True,'filename':path.name,'count':len(rows),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
                'message':'Latest JSON snapshot can be parsed and records have expected identifiers. This verifies local snapshot readability, not a full mongorestore or point-in-time recovery.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:350]}



# Lab 15 — true MongoDB document-level / collection-per-tenant demo.
# Tenant selection is a teaching feature, not JWT authentication or production RBAC.
from pymongo import ASCENDING, ReturnDocument, UpdateOne
from time import perf_counter
LAB15_DB='lab15_saas_live_demo'
LAB15_TENANTS=('tenantAlpha','tenantBeta','tenantGamma','tenantDelta','tenantEpsilon')
LAB15_RATE_LIMIT=5

def lab15_open():
    return lab12_client()  # independent demo database on the existing rsLab10 replica set

def lab15_tenant(t):
    if t not in LAB15_TENANTS: raise HTTPException(400,'Unknown demo tenant')
    return t

def lab15_prepare(db):
    db.pool_tasks.create_index([('tenant_id',ASCENDING),('created_at',-1)],name='tenant_created_idx')
    db.pool_tasks.create_index('task_id',unique=True)
    db.rate_limits.create_index('expires_at',expireAfterSeconds=0,name='expires_ttl')
    db.rate_limits.create_index('tenant_id')

def lab15_collection(db, tenant, strategy):
    if strategy not in ('shared','isolated'): raise HTTPException(400,'Invalid isolation strategy')
    return db.pool_tasks if strategy=='shared' else db['tasks_'+tenant]

def lab15_task_rows(db,tenant,strategy):
    c=lab15_collection(db,tenant,strategy)
    f={'tenant_id':tenant} if strategy=='shared' else {}
    return clean(list(c.find(f,{'_id':0,'task_id':1,'tenant_id':1,'title':1,'status':1,'priority':1,'created_at':1}).sort('created_at',-1).limit(50)))

def lab15_snapshot(db,tenant,strategy):
    count=db.pool_tasks.count_documents({'tenant_id':tenant}) if strategy=='shared' else db['tasks_'+tenant].count_documents({})
    return {'namespace':LAB15_DB+'.'+('pool_tasks' if strategy=='shared' else 'tasks_'+tenant),
        'count':count,'tasks':lab15_task_rows(db,tenant,strategy)}

class Lab15Create(BaseModel):
    tenant: str=Field(min_length=1,max_length=40)
    title: str=Field(min_length=1,max_length=140)
    priority: str='medium'

@app.get('/api/sentinel/lab15/state')
def lab15_state(tenant:str='tenantAlpha',strategy:str='shared'):
    tenant=lab15_tenant(tenant);client=None
    try:
        client=lab15_open();db=client[LAB15_DB];lab15_prepare(db)
        snap=lab15_snapshot(db,tenant,strategy)
        return {'ok':True,'tenant':tenant,'strategy':strategy,'tenants':list(LAB15_TENANTS),
            'shared_count':db.pool_tasks.count_documents({'tenant_id':tenant}),
            'isolated_count':db['tasks_'+tenant].count_documents({}),**snap,
            'note':'Live MongoDB documents in isolated demo database. Tenant dropdown is NOT an authentication boundary.'}
    except HTTPException:raise
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()

@app.post('/api/sentinel/lab15/seed')
def lab15_seed():
    client=None
    try:
        client=lab15_open();db=client[LAB15_DB];lab15_prepare(db)
        # Fixed IDs + upsert make this safe to repeat; no unrelated collection cleared.
        operations=[]
        for ti,t in enumerate(LAB15_TENANTS):
            for i in range(100):
                task_id=f'{t}-seed-{i:03d}'
                doc={'task_id':task_id,'tenant_id':t,'title':f'CTI investigation {i+1}',
                    'priority':('low','medium','high')[i%3],'status':('open' if i%4 else 'review'),
                    'created_at':datetime(2026,1,1,tzinfo=timezone.utc)}
                operations.append(UpdateOne({'task_id':task_id},{'$setOnInsert':doc},upsert=True))
        result=db.pool_tasks.bulk_write(operations,ordered=False)
        return {'ok':True,'total':db.pool_tasks.count_documents({}),
            'inserted':result.upserted_count,'message':'Idempotently seeded five tenants × 100 tasks into shared pool. No existing tasks deleted.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()

@app.post('/api/sentinel/lab15/create')
def lab15_create(req:Lab15Create):
    tenant=lab15_tenant(req.tenant)
    if req.priority not in ('low','medium','high'): raise HTTPException(400,'Invalid priority')
    title=req.title.strip()
    if not title:raise HTTPException(400,'Task title cannot be blank')
    import uuid
    client=None
    try:
        client=lab15_open();db=client[LAB15_DB];lab15_prepare(db)
        window=datetime.now(timezone.utc).replace(second=0,microsecond=0)
        counter=db.rate_limits.find_one_and_update(
            {'_id':f'{tenant}:{window.isoformat()}'},
            {'$inc':{'count':1},'$setOnInsert':{'tenant_id':tenant,'expires_at':window.replace(minute=window.minute)+__import__('datetime').timedelta(minutes=2)}},
            upsert=True,return_document=ReturnDocument.AFTER)
        # Only one atomic counter increment per request. Limit is a demo per-tenant, per-minute counter.
        if counter['count']>LAB15_RATE_LIMIT:
            return {'ok':False,'rate_limited':True,'count':counter['count'],'limit':LAB15_RATE_LIMIT,
                    'message':'TTL demo rate limit exceeded for this tenant (5 creates/min). No task inserted.'}
        doc={'task_id':'task-'+uuid.uuid4().hex[:12],'tenant_id':tenant,'title':title,'priority':req.priority,'status':'open',
             'created_at':datetime.now(timezone.utc)}
        db.pool_tasks.insert_one(doc)
        return {'ok':True,'task_id':doc['task_id'],'tenant':tenant,'limit':LAB15_RATE_LIMIT,'used':counter['count'],
            'message':'Created task in real shared MongoDB pool. Tenant-scoped queries prevent data mixing in this demo.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()

@app.post('/api/sentinel/lab15/migrate')
def lab15_migrate():
    client=None
    try:
        client=lab15_open();db=client[LAB15_DB];lab15_prepare(db)
        results=[]
        for t in LAB15_TENANTS:
            docs=list(db.pool_tasks.find({'tenant_id':t},{'_id':0}))
            dest=db['tasks_'+t]
            dest.create_index('task_id',unique=True)
            if docs:
                dest.bulk_write([UpdateOne({'task_id':d['task_id']},{'$set':d},upsert=True) for d in docs],ordered=False)
            # Compare task IDs rather than merely counts; do not delete extra destination data.
            src_ids={d['task_id'] for d in docs}
            dst_ids=set(dest.distinct('task_id'))
            results.append({'tenant':t,'shared':len(src_ids),'isolated':len(dst_ids),'matched':src_ids==dst_ids})
        ok=all(r['matched'] for r in results)
        return {'ok':ok,'results':results,'message':'Upsert migration complete; source pool retained, destination counts + IDs checked. Existing destination-only records cause verification to fail.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:350]}
    finally:
        if client is not None:client.close()

@app.get('/api/sentinel/lab15/benchmark')
def lab15_benchmark(tenant:str='tenantAlpha',iterations:int=Query(20,ge=5,le=100)):
    tenant=lab15_tenant(tenant);client=None
    try:
        import statistics
        client=lab15_open();db=client[LAB15_DB];lab15_prepare(db)
        measurements={}
        for name,collection,query in [('shared',db.pool_tasks,{'tenant_id':tenant}),('isolated',db['tasks_'+tenant],{})]:
            # A small, synchronous, read-only local benchmark: observed values, not generalized throughput.
            timings=[]
            for _ in range(iterations):
                start=perf_counter()
                list(collection.find(query,{'_id':0,'task_id':1}).limit(100))
                timings.append((perf_counter()-start)*1000)
            measurements[name]=round(statistics.median(timings),4)
        return {'ok':True,'tenant':tenant,'iterations':iterations,'median_ms':measurements,
            'note':'Actual local query timings (warm cache possible), 100-record limit. Small datasets; not a production performance claim.'}
    except Exception as ex:return {'ok':False,'message':str(ex).split('\n')[0][:300]}
    finally:
        if client is not None:client.close()


# Lab 16-only: run real three-database FraudQueryService in its existing Docker application.
# No service credentials exposed to the browser and no database writes.
from pydantic import BaseModel as Lab16Model
LAB16_APP_CONTAINER = 'lab16_polyglot-app-1'
def lab16_docker_run(code: str, timeout: int=20):
    try:
        result = subprocess.run(['docker','exec',LAB16_APP_CONTAINER,'python','-c',code],capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as ex:
        return {'ok':False,'message':'Lab 16 Docker execution unavailable: '+str(ex)[:260]}
    if result.returncode != 0:
        return {'ok':False,'message':('Lab 16 app is not ready: '+(result.stderr or result.stdout).strip())[-550:]}
    try:
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError,ValueError):
        return {'ok':False,'message':'Lab 16 service produced no parseable JSON: '+result.stdout[-350:]}

@app.get('/api/sentinel/lab16/transactions')
def lab16_transactions():
    return lab16_docker_run("import json\nfrom app.connections import mongo_client\nc=mongo_client()\ntry:\n rows=list(c.lab16.transactions.find({}, {'_id':0,'txn_id':1,'user_id':1,'merchant':1,'amount':1,'risk_score':1}).sort('txn_id',1).limit(50))\n print(json.dumps({'ok':True,'transactions':rows},default=str))\nfinally:c.close()")

class Lab16Analyze(Lab16Model):
    txn_id: str

@app.post('/api/sentinel/lab16/analyze')
def lab16_analyze(payload:Lab16Analyze):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,36}', payload.txn_id):
        return {'ok':False,'message':'Invalid transaction identifier'}
    code = "import json\nfrom app.fraud_service import live_service\nservice,handles=live_service()\ntry:\n txn=service.get_transaction(TXN)\n if txn is None:\n  print(json.dumps({'ok':False,'message':'Transaction not found in Lab 16 MongoDB'}))\n else:\n  data=service.analyze_user(txn['user_id'],TXN,max_hops=2)\n  print(json.dumps({'ok':True,'source':'Live Lab 16 MongoDB / Cassandra / Neo4j','result':data},default=str))\nfinally:\n for handle in handles:\n  try:handle.shutdown() if hasattr(handle,'shutdown') else handle.close()\n  except Exception:pass".replace('TXN',repr(payload.txn_id))
    return lab16_docker_run(code,timeout=30)

@app.post('/api/sentinel/lab16/circuit-test')
def lab16_circuit_test():
    # Demonstrates the real class with injected failures, not actual Neo4j downtime.
    code="import json\nfrom app.fraud_service import CircuitBreaker,CircuitOpen\nb=CircuitBreaker(threshold=3,cooldown=30)\nsteps=[]\ndef inject():raise ConnectionError('injected test fault')\nfor i in range(1,5):\n try:b.call(inject)\n except CircuitOpen:steps.append('Attempt '+str(i)+': OPEN — request rejected without backend call')\n except ConnectionError:steps.append('Attempt '+str(i)+': injected failure '+str(b.failures)+'/3')\nprint(json.dumps({'ok':True,'steps':steps,'note':'Isolated CircuitBreaker test only; real Neo4j was not disconnected or modified.'}))"
    return lab16_docker_run(code)


# Lab 17 only: use the Lab 17 project's actual MongoDB documents and vector code.
# No static scores or invented latency measurements.
from pydantic import BaseModel as Lab17RequestBase
LAB17_APP_CONTAINER='lab17_rag-app-1'
def lab17_docker_run(code:str, args=None, timeout:int=25):
    command=['docker','exec',LAB17_APP_CONTAINER,'python','-c',code]+(args or [])
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as ex:
        return {'ok':False,'message':'Lab 17 Docker service unavailable or timed out: '+str(ex)[:240]}
    if result.returncode:
        return {'ok':False,'message':('Lab 17 operation error: '+(result.stderr or result.stdout).strip())[-700:]}
    try:return json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):return {'ok':False,'message':'Lab 17 returned unexpected output: '+result.stdout[-300:]}

@app.get('/api/sentinel/lab17/status')
def lab17_status():
    code="import json;from app.rag import connect;db=connect();n=db.documents.count_documents({});print(json.dumps({'ok':True,'documents':n,'embedding_model':db.documents.find_one({}, {'embedding_model':1}).get('embedding_model') if n else None}))"
    return lab17_docker_run(code,timeout=14)

class Lab17Question(Lab17RequestBase):
    query:str
    user_id:str='sentinel-student'

@app.post('/api/sentinel/lab17/seed')
def lab17_seed():
    code="import json;from app.rag import connect,seed;count,model,dims=seed(connect());print(json.dumps({'ok':True,'seeded':count,'embedding_model':model,'dimensions':dims,'message':'Lab 17 MongoDB document corpus seeded successfully'}))"
    return lab17_docker_run(code,timeout=50)

@app.post('/api/sentinel/lab17/search')
def lab17_search(req:Lab17Question):
    if not req.query.strip() or len(req.query)>750:return {'ok':False,'message':'Question must contain between 1 and 750 characters'}
    code="import json,sys,time;from app.rag import connect,retrieve;start=time.perf_counter();db=connect();results=retrieve(db,sys.argv[1],limit=3);print(json.dumps({'ok':True,'results':results,'source':'Actual Lab 17 MongoDB document embeddings, local cosine similarity','embedding_model':db.documents.find_one({}).get('embedding_model'),'elapsed_ms':round((time.perf_counter()-start)*1000,2)}))"
    return lab17_docker_run(code,[req.query],timeout=25)

@app.post('/api/sentinel/lab17/answer')
def lab17_answer(req:Lab17Question):
    if not req.query.strip() or len(req.query)>750:return {'ok':False,'message':'Question must contain between 1 and 750 characters'}
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',req.user_id):return {'ok':False,'message':'Invalid user ID'}
    code="import json,sys;from app.rag import connect,answer;print(json.dumps({'ok':True,**answer(connect(),sys.argv[1],sys.argv[2])},default=str))"
    return lab17_docker_run(code,[req.user_id,req.query],timeout=75)

@app.post('/api/sentinel/lab17/benchmark')
def lab17_benchmark():
    # Run actual FAISS HNSW/IVF search benchmarks against seeded synthetic 384-D vectors.
    # Bound count and queries to keep this safe on a memory-constrained Mac.
    cmd=['docker','exec',LAB17_APP_CONTAINER,'python','-m','scripts.lab17_2','--count','1000','--dimensions','384','--queries','25','--topk','20']
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=110)
    except (OSError,subprocess.TimeoutExpired) as ex:
        return {'ok':False,'message':'Lab 17 vector benchmark unavailable: '+str(ex)[:260]}
    if p.returncode:return {'ok':False,'message':('FAISS benchmark failed: '+(p.stderr or p.stdout))[-650:]}
    rows=[]
    for line in p.stdout.splitlines():
        line=line.strip()
        if line.startswith('{') and 'avg_latency_ms' in line:
            try:rows.append(json.loads(line))
            except ValueError:pass
    return {'ok':bool(rows),'benchmarks':rows,'benchmark_description':'1,000 synthetic vectors, 384-D, 25 search queries; locally measured FAISS, not MongoDB Atlas indexes','message':'Measured local HNSW and IVF configurations','notes':'These measurements reflect the Lab 17 Docker container and synthetic vectors, not Atlas-native vector index performance.'}



# Lab 18-only: read-only false-positive analytics from the existing Lab 18 Docker MongoDB.
# This endpoint never synthesizes threat counts or benchmark latencies.
@app.get('/api/sentinel/lab18/analytics')
def lab18_analytics(source: str = Query('all', max_length=64), community: str = Query('all'), scale: int = Query(100, ge=1, le=100)):
    import time
    if community not in ('all', 'flagged', 'other'):
        return {'ok': False, 'message': 'Unknown false-positive filter.'}
    bench = benchmark_data()
    result = {'ok': False, 'source': source, 'community': community,
              'scale_millions': scale, 'benchmark': bench,
              'scale_estimate': {
                  'kind': 'ILLUSTRATIVE CAPACITY PLANNING, NOT MEASURED HARDWARE',
                  'records': scale * 1000000,
                  'mongodb': {1:'Replica set + optional sharding',10:'2–4 shards + config-server replica set',100:'6–8 shards + config-server replica set'}[scale],
                  'cassandra': {1:'3 nodes (RF=3)',10:'3–6 nodes (RF=3)',100:'6–12 nodes (RF=3)'}[scale],
                  'neo4j': {1:'Single instance / HA as needed',10:'Causal cluster / graph partitioning evaluation',100:'Causal cluster + Fabric / graph-partitioning design'}[scale],
                  'raw_data_estimate_gb': round(scale * 1.2, 1),
                  'assumption': 'Approximately 1.2 KB of logical record data before indexes, replicas and graph overhead; capacity depends on data model.'}}
    try:
        client, db = mongo_db()
        try:
            col = db.full_threats
            sources = sorted(str(v) for v in col.distinct('from_source') if isinstance(v, str))
            if source != 'all' and source not in sources:
                return {**result, 'message': 'Source not present in this database.', 'sources': sources}
            flt = {}
            if source != 'all': flt['from_source'] = source
            if community == 'flagged': flt['is_false_positive'] = True
            elif community == 'other': flt['is_false_positive'] = False
            total = col.count_documents({}, maxTimeMS=10000)
            fp_total = col.count_documents({'is_false_positive': True}, maxTimeMS=10000)
            started = time.perf_counter()
            matched = col.count_documents(flt, maxTimeMS=10000)
            latency = (time.perf_counter()-started)*1000
            recent = clean(list(col.find(flt, {'_id':0, 'threat_id':1, 'from_source':1, 'threat_type':1,
                                                  'target':1, 'confidence':1, 'is_false_positive':1})
                                     .sort('_id',-1).limit(8)))
            return {**result, 'ok': True, 'sources': sources, 'total': total,
                    'false_positive_candidates': fp_total, 'matched': matched,
                    'filter_latency_ms': round(latency, 3), 'latest': recent,
                    'label': 'Lab 18 synthetic, heuristic-labeled false positives; not independently verified alerts.',
                    'community_note': 'Flagged filter is MongoDB is_false_positive. Graph community membership is not inferred from this flag.'}
        finally: client.close()
    except Exception as e:
        return {**result, 'message': 'Lab 18 MongoDB unavailable: ' + str(e).split('\\n')[0][:200],
                'sources': [], 'total': None, 'false_positive_candidates': None, 'matched': None}



# Add-on: Appendix A AI Threat Advisor
from advisor import router as advisor_router
app.include_router(advisor_router)


# Unified navigation landing page (keeps every existing lab and advisor route).
@app.get('/dashboard')
def main_dashboard_page():
    return FileResponse(ROOT / 'static/dashboard.html', headers={'Cache-Control':'no-store, max-age=0'})

if __name__ == '__main__':
    import uvicorn
    print('Open http://127.0.0.1:8765 in your browser')
    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8765')))

