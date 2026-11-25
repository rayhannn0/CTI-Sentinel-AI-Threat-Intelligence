from connection import client
from common import save
c=client()
hello=c.admin.command('hello')
status=c.admin.command('replSetGetStatus')
members=[{'name':m['name'],'state':m['stateStr'],'health':m['health']} for m in status['members']]
assert len(members)==3 and sum(x['state']=='PRIMARY' for x in members)==1 and sum(x['state']=='SECONDARY' for x in members)==2,members
col=c.lab13.heartbeat
col.update_one({'_id':'demo'}, {'$set':{'message':'Replica set is healthy','lab':'13.1'}}, upsert=True)
assert col.find_one({'_id':'demo'})['lab']=='13.1'
result={'activity':'Lab 13.1','primary':hello.get('primary'),'members':members,'read_write_verified':True}
print(result);save('lab_13_1.json',result)
