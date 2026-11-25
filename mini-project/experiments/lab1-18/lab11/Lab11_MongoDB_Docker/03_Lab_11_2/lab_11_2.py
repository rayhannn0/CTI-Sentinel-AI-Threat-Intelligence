from datetime import datetime,timedelta,timezone
from bson import ObjectId
from common import ready,save,shards_stats,shard_names
c=ready(); db=c['lab11']
# Use a clean benchmark collection for each run; rerunning resets lab11 benchmark data.
for coll in ['hotspot_data','even_data']:
    db.drop_collection(coll)
    db.create_collection(coll)
# Shard range and hashed keys through mongos.
c.admin.command({'shardCollection':'lab11.hotspot_data','key':{'ts':1}})
c.admin.command({'shardCollection':'lab11.even_data','key':{'user_id':'hashed'},'numInitialChunks':8})
start=datetime(2025,1,1,tzinfo=timezone.utc)
for batch in range(0,10000,500):
    db.hotspot_data.insert_many([{'ts':start+timedelta(seconds=i),'order_id':i,'amount':i%100} for i in range(batch,batch+500)])
    db.even_data.insert_many([{'user_id':ObjectId(),'order_id':i,'amount':i%100} for i in range(batch,batch+500)])
range_filter={'ts':{'$gte':start+timedelta(days=0),'$lt':start+timedelta(days=1)}}
# For hashed keys, a range on the original user_id does not provide hashed targeting.
ids=list(db.even_data.find({}, {'user_id':1}).limit(2)); low=min(x['user_id'] for x in ids); high=max(x['user_id'] for x in ids)
hash_filter={'user_id':{'$gte':low,'$lte':high}}
exp1=db.hotspot_data.find(range_filter).explain();exp2=db.even_data.find(hash_filter).explain()
result={'activity':'Lab 11.2','documents_inserted_each':10000,'hotspot_per_shard':shards_stats(db,'hotspot_data'),'hashed_per_shard':shards_stats(db,'even_data'),'timestamp_range_targeted_shards':shard_names(exp1),'hashed_user_id_range_targeted_shards':shard_names(exp2),'timestamp_range_matches':db.hotspot_data.count_documents(range_filter),'hashed_range_matches':db.even_data.count_documents(hash_filter),'note':'Actual shard counts depend on chunk placement, balancing, and MongoDB version; do not assume a 9500/500 split. Hashed range predicates generally scatter.'}
print(result)
save('lab_11_2.json',result)
