"""Try it: journaled/un-journaled 1000 one-by-one inserts per concern."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import run_writes,log_result

def main():
 rows=[]
 for w,label in [(1,'w1'),('majority','majority'),(3,'w3')]:
  for j in [False,True]:rows.append(run_writes(f'{label}_j{str(j).lower()}',w,j))
 log_result('activity_9_1',rows)
 for w in (1,'majority',3):
  a,b=[r for r in rows if r['w']==w]
  pct=(b['total_ms']-a['total_ms'])/a['total_ms']*100 if a['total_ms'] else 0
  print(f'w={w}: j=true versus j=false: {pct:+.1f}% elapsed-time difference (environment-dependent)')
if __name__=='__main__':main()
