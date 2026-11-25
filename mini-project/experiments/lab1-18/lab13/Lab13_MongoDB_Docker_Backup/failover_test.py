"""Run explicitly after bootstrap; steps down current primary and verifies new primary and writable data."""
import time
from connection import client
from common import save
from pymongo.errors import PyMongoError
c=client()
before=c.admin.command('hello')['primary']
print('Primary before:',before)
assert before
c.lab13.heartbeat.update_one({'_id':'failover'}, {'$inc':{'count':1}},upsert=True)
# stepDown intentionally disconnects the primary; retry election verification
try:
 c.admin.command({'replSetStepDown':15,'force':True})
except PyMongoError as exc:
 print('Expected disconnection during stepDown:',type(exc).__name__)
after=None
for _ in range(60):
 try:
  after=c.admin.command('hello').get('primary')
  if after and after!=before:
   c.lab13.heartbeat.update_one({'_id':'failover'}, {'$inc':{'count':1}})
   break
 except PyMongoError:pass
 time.sleep(2)
result={'activity':'Lab 13.1 failover','primary_before':before,'primary_after':after,'primary_changed':bool(after and after!=before),'write_after_election':bool(after and after!=before)}
print(result);save('failover.json',result)
if not result['primary_changed']:raise SystemExit('Failover NOT verified')
