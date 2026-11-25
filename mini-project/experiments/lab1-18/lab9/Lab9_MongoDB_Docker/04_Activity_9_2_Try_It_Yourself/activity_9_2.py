"""Record post-recovery state and summarize observations saved by partition controller."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connection import get_client,DB
from common import log_result

def main():
 with get_client() as c:
  status=c.admin.command('replSetGetStatus')
  result={'members':[{'host':m['name'],'state':m['stateStr'],'health':m['health']} for m in status['members']],
          'partition_test_count':c[DB]['partition_writes'].count_documents({})}
  print(json.dumps(result,indent=2));log_result('activity_9_2',result)
if __name__=='__main__':main()
