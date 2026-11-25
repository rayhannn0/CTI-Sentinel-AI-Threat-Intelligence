import json
from pathlib import Path
from datetime import datetime
from bson import ObjectId
from connection import client
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)

def save(name, data):
    path=OUT/name
    path.write_text(json.dumps(data,indent=2,default=str))
    print('Saved',path)

def ready():
    c=client()
    c.admin.command('ping')
    assert c.admin.command('hello').get('msg')=='isdbgrid', 'Connect through mongos, not mongod'
    return c

def shards_stats(db,coll):
    result=db.command('collStats',coll)
    return {k:{'count':v.get('count',0),'size':v.get('size',0)} for k,v in result.get('shards',{}).items()}

def shard_names(explain):
    names=set()
    def walk(obj):
        if isinstance(obj,dict):
            if isinstance(obj.get('shardName'),str): names.add(obj['shardName'])
            for k,v in obj.items():
                if k=='shards' and isinstance(v,list):
                    for e in v:
                        if isinstance(e,dict) and 'shardName' in e: names.add(e['shardName'])
                walk(v)
        elif isinstance(obj,list):
            for e in obj:walk(e)
    walk(explain)
    return sorted(names)
