"""Lab 7.1: inspect the designed teaching schema and calculate BSON sizes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from connection import get_db

def run():
 db=get_db()
 print('RELATIONSHIPS:')
 print('EMBEDDED threats.tags, threats.mitigations, threats.observables, threats.source_assessment')
 print('REFERENCED threats.source_ids -> sources._id; reports.source_id -> sources._id')
 print('REFERENCED because one source can support many records and can change independently.')
 print('EMBEDDED alternative: threats.sources=[{_id,name,url,verification}, ...]')
 print('Downside: updating a source would require changing multiple threats.')
 for coll in ('threats','sources','reports'):
  pipeline=[{'$project':{'bytes':{'$bsonSize':'$$ROOT'}}},{'$group':{'_id':None,'n':{'$sum':1},'avg':{'$avg':'$bytes'},'max':{'$max':'$bytes'}}}]
  info=list(db[coll].aggregate(pipeline))
  if not info: print(coll,'empty; seed database first');continue
  x=info[0]; print(f"{coll}: documents={x['n']}, average={x['avg']:.1f} bytes, max={x['max']} bytes ({x['max']/(16*1024*1024)*100:.5f}% of 16MB)")
  print('Approaching 16MB?', 'YES' if x['max'] >= 0.8*16*1024*1024 else 'NO')
if __name__=='__main__':run()
