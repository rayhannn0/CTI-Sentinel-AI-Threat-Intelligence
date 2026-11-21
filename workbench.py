"""Real, bounded, local MongoDB lab demonstrations. Operations are explicitly allowlisted.
Infrastructure demonstrations report prerequisites rather than simulating cluster behavior.
No arbitrary code, shell, or Cypher execution is accepted from the browser.
"""
import json
import os
import random
import re
import shutil
import subprocess
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from pymongo import MongoClient, ASCENDING, UpdateOne, WriteConcern
from pymongo.errors import PyMongoError, OperationFailure

HERE = Path(__file__).resolve().parent
URI = os.getenv('LAB18_MONGO_URI', 'mongodb://127.0.0.1:27021')
SCOPE = 'lab_atlas_workbench'
DB = 'lab_atlas_demos'

# Actions marked 'cluster' require a real topology, which cannot be created by the website.
ACTIONS = {
 1:[('connect','Connect & inspect MongoDB'),('insert','Insert a real document'),('query','Query saved documents')],
 2:[('versions','Compare local and Atlas MongoDB versions'),('seed','Seed book inventory'),('increase','Increase older-book prices by 10%')],
 3:[('courses','Embed course schedules & students'),('monday','Query Monday courses'),('blog','Migrate referenced comments to embedded')],
 4:[('products','Seed validated products'),('filter','Query operators + regex'),('bulk','Bulk update & SKU upsert')],
 5:[('orders','Seed realistic sales orders'),('revenue','Monthly revenue aggregation'),('join','Join orders with product catalog')],
 6:[('seed','Seed indexed workload (3,000 docs)'),('explain','Inspect query plan before/after index'),('indexstats','Read real index usage')],
 7:[('threats','Inspect live threat document sizes'),('cache','Inspect WiredTiger cache counters'),('working','Estimate sampled working set')],
 8:[('topology','Inspect replica-set topology'),('status','Read live replica-set health'),('failover','Check failover lab prerequisites')],
 9:[('write','Measure w=1 write latency'),('majority','Measure w=majority write latency'),('partition','Check partition experiment prerequisites')],
 10:[('accounts','Seed two bank accounts'),('transfer','Run real transaction (replica set required)'),('reserve','Try atomic inventory reservation')],
 11:[('matrix','Analyze candidate shard keys'),('cluster','Inspect shard topology'),('hotspot','Check shard-hotspot experiment prerequisites')],
 12:[('auth','Inspect authentication settings'),('roles','Check current user privileges'),('tls','Inspect live TLS connection configuration')],
 13:[('mongo','Inspect MongoDB deployment'),('replica','Verify replica-set state'),('k8s','Check Kubernetes StatefulSet readiness')],
 14:[('metrics','Read live server monitoring metrics'),('backup','Export demo collection to JSON backup'),('restore','Verify last backup file integrity')],
 15:[('seed','Seed tenants and tasks'),('list','List tasks for tenant 1'),('migrate','Create per-tenant task collections')],
 16:[('health','Check polyglot database services'),('mongo','Query MongoDB enrollment documents'),('architecture','Inspect three-database architecture')],
 17:[('seed','Build local document retrieval index'),('retrieve','Search relevant passages'),('memory','Save and inspect conversation history')],
 18:[('summary','Read live threat intelligence counts'),('query','Query high-confidence threats'),('bench','Read actual saved comparative benchmark results')],
}

LAB_NOTES={
 1:'Real MongoDB connection, documents, queries. These are foundational PyMongo demonstrations.',
 2:'Local server_info() is live. Atlas comparison needs ATLAS_MONGO_URI configured in the website environment.',
 3:'Live embedded schemas, array filtering and $lookup migrations.',
 4:'Live CRUD, comparison, logical and array operators, case-insensitive name search, upsert/bulk.',
 5:'Live MongoDB aggregation and real $lookup joins, scoped to demo collections.',
 6:'Real explain() and index statistics on 3,000 records. Full assignment asks for 50,000.',
 7:'Real WiredTiger metrics and BSON sizes from Lab 18; full cache study needs repeated 100,000-document reads.',
 8:'Read-only topology checks on your current server. Replica election needs a separate three-node replica set.',
 9:'Actual timed writes; majority comparison only valid on a running replica set. Network partition is not automatically performed.',
 10:'Real ACID transaction requires replica set; atomic stock reservation works on the present standalone database.',
 11:'Live shard configuration inspection; true hotspot measurement needs a sharded cluster.',
 12:'Live auth/role/TLS diagnostics. This tool never enables authentication, creates users or distributes certificates.',
 13:'Real deployment inspection. Three-node replica verification and Kubernetes require separate installed environments.',
 14:'Real server metrics and JSON backup of the sandboxed demo collection; not a full mongodump/PITR replacement.',
 15:'Live tenant data seeded and migrated for demonstration. Does not replace your Lab 15 JWT/RBAC API.',
 16:'Real service presence and MongoDB queries; Cassandra/Neo4j backend implementations remain in Lab 16 Docker project.',
 17:'Local TF-IDF-style retrieval demo without cloud embeddings/LLM. Atlas Vector Search is a separate requirement.',
 18:'Read-only queries of your 100,000 synthetic threats and measured CSV from Lab 18.',
}

class Prerequisite(Exception): pass

def mongo():
 c=MongoClient(URI,serverSelectionTimeoutMS=2200,connectTimeoutMS=2200, socketTimeoutMS=8000)
 c.admin.command('ping')
 return c

def jsonable(v):
 from bson import ObjectId
 if isinstance(v,dict): return {str(k):jsonable(val) for k,val in v.items() if k!='_id'}
 if isinstance(v,(list,tuple)): return [jsonable(x) for x in v]
 if isinstance(v,datetime):return v.isoformat()
 if isinstance(v,ObjectId):return str(v)
 return v

def show(title,summary,rows=None,**kw):
 return {'ok':True,'title':title,'summary':summary,'rows':jsonable(rows if rows is not None else []),**jsonable(kw)}

def today():return datetime.now(timezone.utc)

def seed_products(db):
 c=db.products
 if c.count_documents({})<10:
  c.delete_many({})
  vals=[('A','Wireless Mouse',29,21,['electronics','wireless']),('B','Bluetooth Speaker',46,9,['electronics','wireless','premium']),('C','Notebook',8,20,['stationery']),('D','USB Cable',14,0,['electronics']),('E','Gaming Monitor',220,7,['electronics','premium']),('F','Keyboard',49,0,['electronics','wireless']),('G','Travel Bag',65,12,['accessories']),('H','Desk Lamp',28,13,['home','premium']),('I','Headphones',110,6,['electronics','wireless']),('J','Water Bottle',21,29,['home'])]
  c.insert_many([{'sku':k,'name':n,'price':float(p),'stock':s,'tags':tag,'is_active':True} for k,n,p,s,tag in vals]);c.create_index('sku',unique=True)
 return c

def seed_orders(db):
 if db.orders.count_documents({}):return
 seed_products(db)
 prods=list(db.products.find({},{'_id':0,'sku':1,'name':1,'price':1}))
 docs=[]
 for i in range(30):
  p=prods[i%len(prods)]
  docs.append({'order_id':f'ORD-{i:03d}','customer':f'Customer {i%7+1}','product_id':p['sku'],'product':p['name'],'quantity':i%4+1,'unit_price':p['price'],'order_date':datetime(2026,1+(i%8),3+i%23,tzinfo=timezone.utc),'status':['paid','pending','refunded'][i%3]})
 db.orders.insert_many(docs)

def replica_state(c):
 try:
  stat=c.admin.command('replSetGetStatus')
  return {'available':True,'set':stat.get('set'),'members':[{'name':m.get('name'),'state':m.get('stateStr'),'health':m.get('health')} for m in stat.get('members',[])]}
 except (PyMongoError,Exception) as e:
  return {'available':False,'reason':str(e).split('\n')[0][:230]}

def run(lab,action):
 if lab not in ACTIONS or action not in [x[0] for x in ACTIONS[lab]]:raise ValueError('Unknown lab action')
 c=mongo();db=c[DB]
 try:
  return dispatch(c,db,lab,action)
 finally:c.close()

def dispatch(c,db,n,a):
 if n==1:
  d=db.fundamentals
  if a=='connect':return show('Live connection', 'MongoDB answered server_info() and ping.',[{'version':c.server_info().get('version'),'database':DB,'host':URI.split('@')[-1]}])
  if a=='insert':
   key='INTRO-'+uuid.uuid4().hex[:8];d.insert_one({'lab_id':key,'name':'MongoDB lab demo','status':'created','created':today()});return show('Document inserted',f'Inserted {key} into lab_atlas_demos.fundamentals',[{'lab_id':key}])
  return show('Recent real documents', 'Fetched from MongoDB (not hardcoded).',list(d.find({}).sort('created',-1).limit(10)))
 if n==2:
  if a=='versions':
   rows=[{'deployment':'Local Docker','version':c.server_info().get('version'),'connected':True}]
   atlas=os.getenv('ATLAS_MONGO_URI','')
   if atlas:
    try:
     aclient=MongoClient(atlas,serverSelectionTimeoutMS=2500);rows.append({'deployment':'Atlas','version':aclient.server_info()['version'],'connected':True});aclient.close()
    except Exception as e:rows.append({'deployment':'Atlas','connected':False,'error':str(e)[:140]})
   else:rows.append({'deployment':'Atlas','connected':False,'note':'Set ATLAS_MONGO_URI to connect to your own Atlas cluster'})
   return show('Server versions','Comparison queried with server_info(); Atlas is optional.',rows)
  d=db.books
  if a=='seed':
   d.delete_many({});d.insert_many([{'title':f'Book {i}','year':2001+i*2,'price':round(18+i*3.5,2)} for i in range(10)]);return show('Books seeded','10 books stored in MongoDB.',list(d.find({}).limit(10)))
  if d.count_documents({})==0:raise Prerequisite('First click “Seed book inventory”.')
  before=list(d.find({'year':{'$lt':2010}}));r=d.update_many({'year':{'$lt':2010}},[{'$set':{'price':{'$round':[{'$multiply':['$price',1.10]},2]}}}]);return show('10% price update applied',f'Updated {r.modified_count} books published before 2010. Repeating will increase again.',list(d.find({'year':{'$lt':2010}})),before=jsonable(before))
 if n==3:
  if a=='courses':
   courses=[{'code':'CS401','title':'Databases','instructor':'Dr Kumar','students':[{'id':'S01','name':'Alice','grade':'A'},{'id':'S02','name':'Bob','grade':'B'}],'schedule':{'days':['Monday','Wednesday'],'room':'A21'},'prerequisites':['CS201']},{'code':'CS402','title':'Networks','instructor':'Dr Rao','students':[{'id':'S03','name':'Charlie','grade':'A'}],'schedule':{'days':['Tuesday'],'room':'B12'},'prerequisites':['CS201']},{'code':'CS403','title':'AI','instructor':'Dr Kumar','students':[{'id':'S01','name':'Alice','grade':'A'}],'schedule':{'days':['Monday'],'room':'C11'},'prerequisites':['CS401']}]
   db.courses.delete_many({});db.courses.insert_many(courses);return show('Courses embedded','Inserted 3 real MongoDB course documents with schedules, rosters and prerequisite references.',list(db.courses.find({}, {'_id':0})))
  if a=='monday':return show('Monday course query','MongoDB array membership filter.',list(db.courses.find({'schedule.days':'Monday'},{'_id':0})))
  db.blog_posts.delete_many({});db.blog_comments.delete_many({});db.blog_embedded.delete_many({})
  db.blog_posts.insert_many([{'post_id':i,'title':f'Post {i}'} for i in range(1,6)])
  db.blog_comments.insert_many([{'post_id':(i%5)+1,'body':f'Comment {i}'} for i in range(10)])
  joined=list(db.blog_posts.aggregate([{'$lookup':{'from':'blog_comments','localField':'post_id','foreignField':'post_id','as':'comments'}},{'$project':{'_id':0}}]));db.blog_embedded.insert_many(joined)
  return show('Blog migration completed','Real $lookup joined 5 posts and 10 comments; embedded copies saved in blog_embedded.',joined[:3])
 if n==4:
  d=seed_products(db)
  if a=='products':return show('Products available','Ten products are stored with SKU, price, stock and tags.',list(d.find({},{'_id':0}).limit(10)))
  if a=='filter':
   groups={'price_20_to_50':list(d.find({'price':{'$gte':20,'$lte':50}},{'_id':0}).limit(10)),'out_of_stock_or_expensive':list(d.find({'$or':[{'stock':0},{'price':{'$gt':100}}]},{'_id':0}).limit(10)),'wireless_electronics':list(d.find({'tags':{'$all':['electronics','wireless']}},{'_id':0}).limit(10)),'name_contains_wire':list(d.find({'name':{'$regex':'wire','$options':'i'}},{'_id':0}).limit(10))}
   return show('Real query operator results','Comparison, logical, $all and case-insensitive $regex.',[{'query':k,'count':len(v),'results':v} for k,v in groups.items()])
  ops=[UpdateOne({'sku':k},{'$inc':{'stock':10}}) for k in 'ABC']+[UpdateOne({'sku':k},{'$set':{'is_active':False}}) for k in 'DE']
  result=d.bulk_write(ops);d.update_one({'sku':'NEW-001'},{'$set':{'price':33.0},'$setOnInsert':{'name':'New Demo Product','stock':0,'tags':['demo'],'is_active':True}},upsert=True)
  return show('Bulk writes and upsert',f'{result.modified_count} products modified; idempotent SKU NEW-001 upsert executed.',list(d.find({'sku':{'$in':['A','B','C','D','E','NEW-001']}},{'_id':0})))
 if n==5:
  seed_orders(db)
  if a=='orders':return show('30 sales orders available','Real MongoDB documents, seeded once.',list(db.orders.find({},{'_id':0}).limit(8)))
  if a=='revenue':
   rows=list(db.orders.aggregate([{'$group':{'_id':{'$dateToString':{'format':'%Y-%m','date':'$order_date'}},'revenue':{'$sum':{'$multiply':['$quantity','$unit_price']}},'orders':{'$sum':1}}},{'$sort':{'_id':1}}]))
   return show('Monthly sales revenue','Calculated using $group, $multiply and $sort on live documents.',rows)
  rows=list(db.orders.aggregate([{'$lookup':{'from':'products','localField':'product_id','foreignField':'sku','as':'item'}},{'$unwind':'$item'},{'$project':{'_id':0,'order_id':1,'product':'$item.name','quantity':1,'total':{'$multiply':['$quantity','$item.price']}}},{'$limit':12}]))
  return show('Live $lookup join','Orders joined against product catalog in MongoDB.',rows)
 if n==6:
  d=db.index_workload
  if a=='seed':
   if d.count_documents({})<3000:
    d.delete_many({});d.drop_indexes();rng=random.Random(621)
    d.insert_many([{'name':f'Item {i:05d}','category':rng.choice(['books','home','tech','fashion']),'price':rng.randrange(10,500),'rating':rng.randint(1,5),'stock':rng.randrange(0,80),'tags':[rng.choice(['premium','sale','wireless'])]} for i in range(3000)])
   return show('Index dataset ready',f'{d.estimated_document_count()} indexed-workload records stored.', [{'collection':'index_workload','count':d.estimated_document_count()}])
  if not d.count_documents({}):raise Prerequisite('First click “Seed indexed workload”.')
  if a=='explain':
   d.drop_indexes();query={'category':'tech'}
   pre=d.find(query).sort('price',1).limit(100).explain();d.create_index([('category',1),('price',1)],name='category_price');post=d.find(query).sort('price',1).limit(100).explain()
   return show('Measured query planner changes','Ran actual explain() before and after creating compound index.', [{'phase':'no compound index','docs_examined':pre.get('executionStats',{}).get('totalDocsExamined'),'execution_ms':pre.get('executionStats',{}).get('executionTimeMillis'),'winning_plan':str(pre.get('queryPlanner',{}).get('winningPlan',{}))[:450]},{'phase':'with compound index','docs_examined':post.get('executionStats',{}).get('totalDocsExamined'),'execution_ms':post.get('executionStats',{}).get('executionTimeMillis'),'winning_plan':str(post.get('queryPlanner',{}).get('winningPlan',{}))[:450]}])
  return show('Live index usage','MongoDB $indexStats results on this collection.',list(d.aggregate([{'$indexStats':{}}])))
 if n==7:
  src=c['threat_intel'].full_threats
  if a=='threats':
   rows=list(src.aggregate([{'$limit':100},{'$project':{'_id':0,'size_bytes':{'$bsonSize':'$$ROOT'}}},{'$group':{'_id':None,'sample_size':{'$sum':1},'mean_bytes':{'$avg':'$size_bytes'},'max_bytes':{'$max':'$size_bytes'}}}]))
   return show('Real BSON sizes','Inspected up to 100 threat documents from existing Lab 18 database.',rows)
  server=c.admin.command('serverStatus');cache=server.get('wiredTiger',{}).get('cache',{})
  if a=='cache':return show('WiredTiger live cache','Real database cache counters from serverStatus; no synthetic numbers.',[{k:cache.get(k) for k in ['maximum bytes configured','bytes currently in the cache','bytes read into cache','bytes written from cache','pages read into cache','pages requested from the cache']}])
  count=src.estimated_document_count();sample=list(src.aggregate([{'$sample':{'size':min(50,max(1,count))}},{'$project':{'size':{'$bsonSize':'$$ROOT'}}}])) if count else []
  mean=sum(x['size'] for x in sample)/len(sample) if sample else 0
  return show('Estimated working set','Estimated data bytes from a random sample; index and storage overhead excluded.',[{'documents':count,'avg_sample_bytes':round(mean,1),'estimated_data_MB':round(count*mean/1e6,2)}])
 if n==8:
  topology=replica_state(c)
  if a=='topology':return show('Live topology', 'This checks your real connected MongoDB deployment.',[{'hello':jsonable(c.admin.command('hello')),'replica_set':topology}])
  if a=='status':
   if not topology['available']:raise Prerequisite('This MongoDB instance is standalone. Start the separate 3-node replica set for Lab 8 to inspect PRIMARY/SECONDARY states.')
   return show('Replica state', 'Real replica member health.',topology['members'])
  if not topology['available']:raise Prerequisite('A 3-node replica set is required before observing failover. This website intentionally does not call rs.stepDown() on your existing database.')
  return show('Failover prerequisites','Replica set detected; use the isolated Lab 8 Compose project to trigger and monitor a manual failover.',topology['members'])
 if n==9:
  if a=='partition':raise Prerequisite('Network partition demonstration requires a dedicated replica-set network. No docker network disconnect is executed from the website.')
  if a=='majority' and not replica_state(c)['available']:raise Prerequisite('w=majority latency cannot be meaningfully tested on this standalone MongoDB instance. Connect LAB18_MONGO_URI to a replica-set URI.')
  d=c[DB].write_latency.with_options(write_concern=WriteConcern(w='majority' if a=='majority' else 1,wtimeout=2500));stamp=uuid.uuid4().hex[:8];start=time.perf_counter()
  for i in range(30):d.insert_one({'experiment':stamp,'i':i,'created':today()})
  ms=(time.perf_counter()-start)*1000;d.delete_many({'experiment':stamp})
  return show('Actual write-concern measurement','30 inserts completed and cleaned up. These are locally measured times.',[{'write_concern':'majority' if a=='majority' else '1','writes':30,'total_ms':round(ms,2),'avg_ms':round(ms/30,3)}])
 if n==10:
  aco=db.bank_accounts
  if a=='accounts':
   aco.delete_many({});aco.insert_many([{'account_id':'A','balance':500.0},{'account_id':'B','balance':100.0}]);return show('Bank accounts initialized','Two accounts stored in MongoDB.',list(aco.find({},{'_id':0})))
  if a=='transfer':
   if not replica_state(c)['available']:raise Prerequisite('Multi-document ACID transactions require a MongoDB replica set or mongos. Your Lab 18 MongoDB is standalone; a transfer is NOT simulated.')
   with c.start_session() as session:
    with session.start_transaction():
     r=aco.update_one({'account_id':'A','balance':{'$gte':25}},{'$inc':{'balance':-25}},session=session)
     if r.modified_count!=1:raise Prerequisite('Transfer aborted: insufficient funds.')
     aco.update_one({'account_id':'B'},{'$inc':{'balance':25}},session=session)
   return show('ACID transfer complete','Debited A and credited B in one MongoDB transaction.',list(aco.find({},{'_id':0})))
  inv=db.inventory;inv.update_one({'sku':'GPU'},{'$setOnInsert':{'stock':5}},upsert=True)
  r=inv.find_one_and_update({'sku':'GPU','stock':{'$gte':1}},{'$inc':{'stock':-1}},return_document=True)
  return show('Atomic reservation','Single-document atomic stock decrement (not a multi-document transaction).',[{'reserved':bool(r),'remaining':r['stock'] if r else 0}])
 if n==11:
  if a=='matrix':return show('Shard key decision matrix','Analytical evaluation; these are not live shard measurements.',[{'key':'order_id','distribution':'high cardinality','customer targeting':'poor'},{'key':'customer_id','distribution':'possible skew','customer targeting':'good'},{'key':'order_date','distribution':'hotspot risk','customer targeting':'poor'},{'key':'hashed customer_id','distribution':'typically balanced','customer targeting':'equality only'}])
  try:r=c.admin.command('listShards');rows=r.get('shards',[])
  except Exception as e:
   if a=='hotspot':raise Prerequisite('A real multi-shard MongoDB sharded cluster is required to measure key hotspots.')
   return show('Sharding not configured','Current server does not expose listShards; MongoDB standalone and replica sets are not sharded.',[{'connected_server':URI.split('@')[-1],'message':str(e).split('\n')[0][:160]}])
  if a=='hotspot':return show('Sharded deployment detected','Implement two sharded collections with range and hashed keys to compare actual chunk distribution.',rows)
  return show('Real shard topology','Read with listShards command.',rows)
 if n==12:
  if a=='auth':
   try:users=c[DB].command('usersInfo',1);return show('MongoDB authenticated user list','This command succeeded with current permissions.',[{'users':len(users.get('users',[]))}])
   except Exception as e:return show('Auth permissions check','User listing is unavailable or not authorized; this is the actual server response.',[{'detail':str(e).split('\n')[0][:190]}])
  if a=='roles':
   try:r=c.admin.command('connectionStatus',showPrivileges=True);user=r.get('authInfo',{});return show('Current connection privileges','Live authenticated roles and privilege count; secrets are not displayed.',[{'users':user.get('authenticatedUsers',[]),'roles':user.get('authenticatedUserRoles',[]),'privileges_count':len(user.get('authenticatedUserPrivileges',[]))}])
   except Exception as e:return show('Role inspection','Current connection cannot inspect role privileges.',[{'error':str(e)[:160]}])
  opts=c.options;return show('TLS configuration','Client transport settings; TLS server mode must be confirmed separately on the target deployment.',[{'tls_enabled_client':bool(opts.get('tls')),'note':'This is NOT proof that MongoDB rejects plaintext connections.'}])
 if n==13:
  if a=='mongo':return show('Live MongoDB deployment','Inspected connected server build and topology.',[{'version':c.server_info().get('version'),'hello':{'setName':c.admin.command('hello').get('setName'),'isWritablePrimary':c.admin.command('hello').get('isWritablePrimary')}}])
  if a=='replica':
   r=replica_state(c)
   if not r['available']:raise Prerequisite('The connected MongoDB server is not a 3-node replica set. A keyFile-backed deployment must be started separately.')
   return show('Real replica health','State checked via replSetGetStatus.',r['members'])
  kubectl=shutil.which('kubectl')
  if not kubectl:raise Prerequisite('kubectl is not installed in the website runtime; Kubernetes StatefulSet not deployed.')
  try:
   p=subprocess.run([kubectl,'get','statefulsets','-o','json'],text=True,capture_output=True,timeout=4)
   if p.returncode:raise Prerequisite('kubectl cannot access a Kubernetes cluster: '+p.stderr[:140])
   d=json.loads(p.stdout);return show('Kubernetes StatefulSets','Live kubectl read-only query.',[{'name':v['metadata']['name'],'replicas':v.get('status',{}).get('readyReplicas',0)} for v in d.get('items',[])])
  except subprocess.TimeoutExpired:raise Prerequisite('kubectl query timed out.')
 if n==14:
  if a=='metrics':
   status=c.admin.command('serverStatus');return show('MongoDB serverStatus metrics','These counters are live from your Docker MongoDB.',[{'connections':status.get('connections',{}),'opcounters':status.get('opcounters',{}),'uptime_seconds':status.get('uptime')}])
  path=HERE/'backups'/'lab14_demo_backup.json';path.parent.mkdir(exist_ok=True)
  if a=='backup':
   docs=list(db.fundamentals.find({}).limit(500));path.write_text(json.dumps(jsonable(docs),indent=2))
   return show('JSON export backup saved',f'Wrote {len(docs)} fundamental-demo documents to {path}. This is not a full mongodump.',[{'path':str(path),'documents':len(docs),'bytes':path.stat().st_size}])
  if not path.is_file():raise Prerequisite('First click “Export demo collection to JSON backup”.')
  docs=json.loads(path.read_text());return show('Backup integrity check','Parsed the saved backup JSON and verified document list type.',[{'path':str(path),'valid':isinstance(docs,list),'documents':len(docs)}])
 if n==15:
  coll=db.tenant_tasks
  if a=='seed':
   if not coll.count_documents({}):coll.insert_many([{'tenant_id':f'tenant-{t}','task_id':f'T{t}-{i:03d}','title':f'Task {i}','owner':f'user-{i%4}','status':'open' if i%3 else 'done'} for t in range(1,6) for i in range(100)])
   coll.create_index([('tenant_id',1),('task_id',1)],unique=True)
   return show('Five tenants seeded','500 document-level tenant tasks, isolated by tenant_id.',[{'count':coll.count_documents({}),'tenants':5}])
  if a=='list':return show('Tenant 1 task query','All query conditions explicitly filter tenant_id.',list(coll.find({'tenant_id':'tenant-1'},{'_id':0}).limit(12)))
  if not coll.count_documents({}):raise Prerequisite('First click “Seed tenants and tasks”.')
  rows=[]
  for t in range(1,6):
   tenant=f'tenant-{t}';name=f'tasks_tenant_{t}';docs=list(coll.find({'tenant_id':tenant}));dst=db[name];dst.delete_many({});dst.insert_many([{k:v for k,v in x.items() if k!='_id'} for x in docs]);rows.append({'tenant':tenant,'shared_count':len(docs),'separate_count':dst.count_documents({})})
  return show('Collection-per-tenant migration','Data copied and per-tenant counts checked.',rows)
 if n==16:
  if a=='health':
   import socket
   def online(port):
    try:
     s=socket.create_connection(('127.0.0.1',port),timeout=.4);s.close();return True
    except OSError:return False
   return show('Polyglot service probes','MongoDB ping plus TCP probes. A TCP port being open does not verify authentication or query health.',[{'service':'MongoDB','connected':True},{'service':'Neo4j Lab18 bolt','connected':online(7689)},{'service':'Neo4j Lab18 HTTP','connected':online(7476)},{'service':'Cassandra external CQL','connected':online(9042)}])
  if a=='mongo':
   course=c[DB].courses
   return show('MongoDB enrollment queries','Querying real lab-3 course data; Cassandra and Neo4j require their own lab-specific service.',list(course.find({}, {'_id':0,'code':1,'students':1}).limit(5)))
  return show('Three-database design','Actual connected MongoDB and existing Lab 16/18 architectures described, not claimed as a combined query execution.',[{'backend':'MongoDB','purpose':'Operational JSON documents'},{'backend':'Cassandra','purpose':'Query-driven time series and audit events'},{'backend':'Neo4j','purpose':'Relationships and connected graph paths'}])
 if n==17:
  docs=db.rag_chunks
  corpus=[('threats','Threat intelligence classifies suspicious events and distinguishes false positives from malicious activity.'),('mongodb','MongoDB stores flexible BSON documents and supports aggregation pipelines and compound indexes.'),('cassandra','Cassandra supports denormalized wide-column tables and partition-key access for time-series history.'),('neo4j','Neo4j represents sources and threats as nodes connected by relationships to detect suspicious communities.'),('security','Security analysts inspect confidence, malware, phishing, target hosts and event sources before mitigation.')]
  if a=='seed':
   docs.delete_many({});docs.insert_many([{'source':s,'text':t} for s,t in corpus]);return show('Retrieval corpus saved','5 short text chunks stored in MongoDB; local retrieval demo, not Atlas Vector Search.',list(docs.find({},{'_id':0})))
  if a=='retrieve':
   rows=list(docs.find({},{'_id':0}));query='how do graph relationships detect connected threats'
   qset=set(re.findall(r'[a-z]+',query));rank=[]
   for row in rows:
    words=set(re.findall(r'[a-z]+',row['text'].lower()));score=len(qset & words)/max(1,len(qset | words));rank.append({**row,'jaccard_score':round(score,4)})
   return show('Top relevant passages',f'Live local lexical retrieval for query: “{query}”. Not AI-generated or Atlas vector retrieval.',sorted(rank,key=lambda x:-x['jaccard_score'])[:3])
  history=db.rag_chat;history.insert_one({'question':'What is a false positive?','response':'A benign event incorrectly flagged as a threat.','time':today()});return show('Conversation memory saved','Latest five saved exchanges in MongoDB.',list(history.find({},{'_id':0}).sort('time',-1).limit(5)))
 if n==18:
  threat=c['threat_intel'].full_threats
  if a=='summary':return show('Live threat collection','Direct query of Lab 18 Docker MongoDB; labels come from synthetic data.',[{'total':threat.estimated_document_count(),'false_positives':threat.count_documents({'is_false_positive':True},maxTimeMS=7000),'database':'threat_intel'}])
  if a=='query':return show('High confidence threat inspection','Read-only query sorted by timestamp.',list(threat.find({'confidence':{'$gte':0.9}},{'_id':0}).sort('timestamp',-1).limit(12)))
  import csv
  path=Path.home()/'Downloads/lab18/Lab18_Threat_Intelligence_Docker_Submission/output/benchmark.csv'
  if not path.is_file():path=HERE/'data/benchmark_snapshot.csv'
  with path.open(newline='') as f: rows=list(csv.DictReader(f))
  return show('Saved Lab 18 comparison',f'Source: {path}. These are saved measurements, not a new benchmark run.',rows)
 raise ValueError('Unsupported action')


def catalog(labs):
 return [{'id':l['id'],'name':l['name'],'subtitle':l['subtitle'],'notes':LAB_NOTES[l['id']],'actions':[{'id':code,'label':label} for code,label in ACTIONS[l['id']]],'reference':l['reference'],'activities':l.get('activities',[])} for l in labs]
