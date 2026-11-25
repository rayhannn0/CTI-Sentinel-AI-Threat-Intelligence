"""Read-only network/replica-state observer, run in a second terminal inside runner service."""
import sys,time,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connection import get_client
from pymongo.errors import PyMongoError

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=60);args=ap.parse_args()
 end=time.monotonic()+args.seconds
 while time.monotonic()<end:
  try:
   with get_client(timeout=1500) as c:
    members=c.admin.command('replSetGetStatus')['members']
    print(time.strftime('%H:%M:%S'),' '.join(f"{m['name'].split(':')[0]}={m['stateStr']}/health{m['health']}" for m in members),flush=True)
  except PyMongoError as e:print(time.strftime('%H:%M:%S'),'no primary / error:',str(e)[:140],flush=True)
  time.sleep(1)
if __name__=='__main__':main()
