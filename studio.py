"""Bounded interactive actions backed by a separate MongoDB demo database.
No user-provided arbitrary query JSON, shell commands or DB connection strings are evaluated.
"""
import re, time, uuid, json
from datetime import datetime, timezone
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError
from workbench import URI, DB, jsonable, seed_products, seed_orders
import os
THREAT_URI=os.getenv('LAB18_THREAT_URI','mongodb://127.0.0.1:27021')

LAB_COLLECTIONS={1:'fundamentals',2:'books',3:'courses',4:'products',5:'orders',6:'index_workload',7:'full_threats',10:'bank_accounts',14:'fundamentals',15:'tenant_tasks',17:'rag_chunks',18:'full_threats'}
def _text(v,limit=100):
 v=str(v or '').strip()
 if not v or len(v)>limit:raise ValueError(f'Enter 1–{limit} characters')
 return v

def _num(v,minimum=0,maximum=1000000):
 try: x=float(v)
 except (TypeError,ValueError):raise ValueError('Enter a valid number')
 if not minimum<=x<=maximum:raise ValueError(f'Number must be between {minimum} and {maximum}')
 return x

def _db():
 c=MongoClient(URI,serverSelectionTimeoutMS=2500,connectTimeoutMS=2500,socketTimeoutMS=8500)
 c.admin.command('ping')
 return c

def list_data(lab,params=None):
 c=MongoClient(THREAT_URI if lab in (7,18) else URI,serverSelectionTimeoutMS=2500,connectTimeoutMS=2500,socketTimeoutMS=8500);params=params or {}
 try:
  db=c[DB]
  if lab==4: seed_products(db)
  if lab==5: seed_orders(db)
  if lab==15:
   col=db.tenant_tasks;filter={'tenant_id':str(params.get('tenant') or 'tenant-1')[:30]}
  elif lab==18:
   col=c.threat_intel.full_threats;filter={}
   if params.get('type') and params['type']!='all':filter['threat_type']=str(params['type'])[:50]
   if params.get('flagged')=='true':filter['is_false_positive']=True
  else:
   coll=LAB_COLLECTIONS.get(lab)
   if not coll: return {'rows':[],'total':0,'database':DB}
   col=c.threat_intel[coll] if lab==7 else db[coll];filter={}
  q=str(params.get('q') or '').strip()[:70]
  if q:
   rx=re.compile(re.escape(q),re.I)
   fields={1:['name','lab_id'],2:['title'],3:['code','title','instructor'],4:['name','sku'],5:['customer','product','order_id'],6:['name','category'],7:['from_source','threat_type','target','threat_id'],10:['account_id'],14:['name','lab_id'],15:['title','task_id'],17:['source','text'],18:['from_source','threat_type','target','threat_id']}.get(lab,[])
   if fields:filter['$or']=[{f:rx} for f in fields]
  limit=min(100,max(1,int(params.get('limit') or 35)))
  total=col.count_documents(filter,maxTimeMS=8000)
  rows=list(col.find(filter,{'_id':0}).limit(limit))
  return {'rows':jsonable(rows),'total':total,'database':'threat_intel' if lab in (7,18) else DB,'collection':col.name}
 finally:c.close()

def command(lab,operation,data):
 data=data or {};c=_db()
 try:
  db=c[DB]
  if lab==1:
   if operation=='create':
    obj={'lab_id':'DOC-'+uuid.uuid4().hex[:8].upper(),'name':_text(data.get('name')),'status':str(data.get('status') or 'active')[:24],'created':datetime.now(timezone.utc)}
    db.fundamentals.insert_one(obj);return {'message':'Document saved in MongoDB','item':jsonable(obj)}
   if operation=='delete':
    r=db.fundamentals.delete_one({'lab_id':_text(data.get('id'),40)});return {'message':f'{r.deleted_count} document deleted'}
  if lab==2:
   if operation=='create':
    d={'title':_text(data.get('title')),'year':int(_num(data.get('year'),1900,2100)),'price':_num(data.get('price'))}
    db.books.insert_one(d);return {'message':'Book added','item':jsonable(d)}
   if operation=='increase':
    r=db.books.update_many({'year':{'$lt':2010}},[{'$set':{'price':{'$round':[{'$multiply':['$price',1.1]},2]}}}]);return {'message':f'Updated {r.modified_count} books by 10%'}
  if lab==3:
   if operation=='create':
    code=_text(data.get('code'),15).upper();days=[x.strip() for x in str(data.get('days') or 'Monday').split(',') if x.strip()][:7]
    db.courses.update_one({'code':code},{'$set':{'code':code,'title':_text(data.get('title')),'instructor':_text(data.get('instructor')),'schedule':{'days':days,'room':str(data.get('room') or 'A-101')[:30]}},'$setOnInsert':{'students':[]}},upsert=True)
    return {'message':'Course saved to MongoDB'}
   if operation=='enroll':
    code=_text(data.get('code'),15).upper();student=_text(data.get('student'))
    d=db.courses.find_one_and_update({'code':code,'students.name':{'$ne':student}},{'$push':{'students':{'id':uuid.uuid4().hex[:6],'name':student,'grade':'N/A'}}},return_document=ReturnDocument.AFTER)
    return {'message':'Student enrolled' if d else 'Course not found or student already enrolled'}
  if lab==4:
   coll=seed_products(db)
   if operation=='create':
    sku=_text(data.get('sku'),30).upper();doc={'sku':sku,'name':_text(data.get('name')),'price':_num(data.get('price'),.01),'stock':int(_num(data.get('stock'),0,100000)),'tags':[t.strip() for t in str(data.get('tags') or '').split(',') if t.strip()][:12],'is_active':True}
    coll.update_one({'sku':sku},{'$set':doc},upsert=True);return {'message':f'Product {sku} saved'}
   if operation=='stock':
    r=coll.update_one({'sku':_text(data.get('sku'),30).upper()},{'$inc':{'stock':int(_num(data.get('amount'),0,10000))}});return {'message':f'{r.modified_count} product updated'}
   if operation=='delete':
    r=coll.delete_one({'sku':_text(data.get('sku'),30).upper()});return {'message':f'{r.deleted_count} product deleted'}
  if lab==5:
   seed_orders(db); seed_products(db)
   if operation=='create':
    sku=_text(data.get('sku'),30).upper();item=db.products.find_one({'sku':sku})
    if not item:raise ValueError('SKU not found. Use a valid SKU from Lab 4 (such as A).')
    order={'order_id':'ORD-'+uuid.uuid4().hex[:8].upper(),'customer':_text(data.get('customer')),'product_id':sku,'product':item['name'],'quantity':int(_num(data.get('quantity'),1,1000)),'unit_price':item['price'],'order_date':datetime.now(timezone.utc),'status':'paid'}
    db.orders.insert_one(order);return {'message':'Order created','item':jsonable(order)}
  if lab==10:
   if operation=='init':
    db.bank_accounts.update_one({'account_id':'A'},{'$set':{'balance':500}},upsert=True);db.bank_accounts.update_one({'account_id':'B'},{'$set':{'balance':100}},upsert=True)
    db.inventory.update_one({'sku':'GPU'},{'$set':{'stock':5}},upsert=True)
    return {'message':'Sample accounts and inventory created'}
   if operation=='transfer':
    hello=c.admin.command('hello')
    if not hello.get('setName') and not hello.get('msg')=='isdbgrid':raise ValueError('ACID transfer requires a MongoDB replica set. Your Lab 18 MongoDB is standalone; no transfer was performed.')
    source=_text(data.get('source'),10);target=_text(data.get('target'),10);amount=_num(data.get('amount'),.01,10000)
    if source==target:raise ValueError('Choose two different accounts')
    with c.start_session() as s:
     with s.start_transaction():
      r=db.bank_accounts.update_one({'account_id':source,'balance':{'$gte':amount}},{'$inc':{'balance':-amount}},session=s)
      if not r.modified_count:raise ValueError('Insufficient funds or source account missing')
      r=db.bank_accounts.update_one({'account_id':target},{'$inc':{'balance':amount}},session=s)
      if not r.modified_count:raise ValueError('Target account missing')
    return {'message':f'Transferred {amount} safely in an ACID transaction'}
   if operation=='reserve':
    qty=int(_num(data.get('quantity'),1,100));doc=db.inventory.find_one_and_update({'sku':'GPU','stock':{'$gte':qty}},{'$inc':{'stock':-qty}},return_document=ReturnDocument.AFTER)
    if not doc:raise ValueError('Insufficient GPU stock; initialize or reduce quantity')
    return {'message':'Atomic stock reservation completed','item':jsonable(doc)}
  if lab==15:
   if operation=='create':
    tenant=_text(data.get('tenant') or 'tenant-1',30);title=_text(data.get('title'));task={'task_id':'TASK-'+uuid.uuid4().hex[:8].upper(),'tenant_id':tenant,'title':title,'owner':'demo-user','status':'open'}
    db.tenant_tasks.insert_one(task);return {'message':'Tenant-scoped task created','item':jsonable(task)}
   if operation=='toggle':
    tenant=_text(data.get('tenant') or 'tenant-1',30);tid=_text(data.get('id'),50)
    r=db.tenant_tasks.update_one({'tenant_id':tenant,'task_id':tid},{'$set':{'status':'done'}})
    return {'message':f'{r.modified_count} matching tenant task completed'}
  if lab==17:
   if operation=='create':
    doc={'source':_text(data.get('source')),'text':_text(data.get('text'),2000)};db.rag_chunks.insert_one(doc)
    return {'message':'Document saved to retrieval collection'}
   if operation=='search':
    query=_text(data.get('query'),200);words=set(re.findall(r'[a-z0-9]+',query.lower()));rows=list(db.rag_chunks.find({}, {'_id':0}).limit(300))
    scored=[]
    for row in rows:
     tokens=set(re.findall(r'[a-z0-9]+',row['text'].lower()));score=len(words & tokens)/max(1,len(words|tokens));scored.append({**row,'lexical_score':round(score,4)})
    results=sorted(scored,key=lambda x:-x['lexical_score'])[:5]
    db.rag_chat.insert_one({'question':query,'response':'Retrieved '+str(len(results))+' passages','time':datetime.now(timezone.utc)})
    return {'message':'Local lexical search completed (not an LLM or Atlas vector search)','rows':results}
  raise ValueError('Unsupported operation for this laboratory')
 finally:c.close()
