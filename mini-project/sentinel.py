"""Real transactional bank transfer, audit trail and balance telemetry for Sentinel UI."""
import os, uuid, time
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError
from pydantic import BaseModel, Field

URI=os.environ.get('LAB18_MONGO_URI','mongodb://127.0.0.1:27021')
NAME='lab_atlas_demos'

class TransferRequest(BaseModel):
    amount:float=Field(default=250,gt=0,le=100000)
    source:str=Field(default='ACC-1001',pattern=r'^ACC-100[12]$')
    target:str=Field(default='ACC-1002',pattern=r'^ACC-100[12]$')
    test_failure:bool=False


def client():
    c=MongoClient(URI,serverSelectionTimeoutMS=2500,connectTimeoutMS=2500)
    c.admin.command('ping')
    return c


def money(v):return round(float(v),2)


def clean(d):
    return {'id':str(d.get('_id','')),'time':d['time'].isoformat() if isinstance(d.get('time'),datetime) else str(d.get('time','')),'source':d.get('source'),'target':d.get('target'),'amount':money(d.get('amount',0)),'status':d.get('status'),'message':d.get('message',''),'attempts':d.get('attempts',1)}


def balances():
    with client() as c:
        db=c[NAME];hello=c.admin.command('hello');accounts=list(db.sentinel_accounts.find({},{'_id':0}).sort('account_id',1))
        history=[clean(d) for d in db.sentinel_history.find().sort('time',-1).limit(16)]
        return {'replica_set':hello.get('setName'),'transaction_ready':bool(hello.get('setName') or hello.get('msg')=='isdbgrid'), 'accounts':accounts,'history':history,'transactions':db.sentinel_history.count_documents({'status':'COMMITTED'}),'database':NAME,'connection':URI.split('@')[-1].split('?')[0]}


def reset():
    with client() as c:
        db=c[NAME]
        db.sentinel_accounts.update_one({'account_id':'ACC-1001'},{'$set':{'balance':1000.0,'version':1}},upsert=True)
        db.sentinel_accounts.update_one({'account_id':'ACC-1002'},{'$set':{'balance':500.0,'version':1}},upsert=True)
        db.sentinel_history.delete_many({})
        return {'ok':True,'message':'Demo accounts reset to $1,000 and $500; prior demo audit entries cleared.','state':balances()}


def transfer(req:TransferRequest):
    if req.source==req.target:return {'ok':False,'message':'Source and destination must differ.','state':balances()}
    with client() as c:
        db=c[NAME];hello=c.admin.command('hello')
        if not hello.get('setName') and hello.get('msg')!='isdbgrid':
            return {'ok':False,'message':'Real multi-document ACID transfer requires a replica set. Connect with LAB18_MONGO_URI=mongodb://localhost:27022/?replicaSet=rsLab10.','state':balances()}
        txid='TX-'+uuid.uuid4().hex[:10].upper();amount=money(req.amount)
        attempts=0
        def operation(session):
            nonlocal attempts
            attempts+=1
            debit=db.sentinel_accounts.update_one({'account_id':req.source,'balance':{'$gte':amount}},{'$inc':{'balance':-amount,'version':1}},session=session)
            if debit.modified_count!=1:raise ValueError('Insufficient funds or missing source account. Entire transfer rolled back.')
            credit=db.sentinel_accounts.update_one({'account_id':req.target},{'$inc':{'balance':amount,'version':1}},session=session)
            if credit.modified_count!=1:raise ValueError('Destination account missing. Entire transfer rolled back.')
            db.sentinel_history.insert_one({'tx_id':txid,'time':datetime.now(timezone.utc),'source':req.source,'target':req.target,'amount':amount,'status':'COMMITTED','message':'Atomic debit, credit and audit entry committed.'},session=session)
        try:
            if req.test_failure:
                # Reject inside a transaction after attempted debit to verify rollback.
                with c.start_session() as s:
                    with s.start_transaction():
                        db.sentinel_accounts.update_one({'account_id':req.source,'balance':{'$gte':0}},{'$inc':{'balance':-1,'version':1}},session=s)
                        raise ValueError('Simulated failure after debit. Transaction aborted; no balance changed.')
            else:
                with c.start_session() as session:
                    session.with_transaction(operation,max_commit_time_ms=8000)
        except (ValueError,PyMongoError) as e:
            message=str(e).split('\n')[0][:220]
            db.sentinel_history.insert_one({'tx_id':txid,'time':datetime.now(timezone.utc),'source':req.source,'target':req.target,'amount':amount,'status':'ROLLED BACK','message':message,'attempts':attempts})
            return {'ok':False,'message':message,'tx_id':txid,'state':balances()}
        return {'ok':True,'message':f'${amount:,.2f} transferred. Debit, credit and audit log committed together.','tx_id':txid,'attempts':attempts,'state':balances()}
