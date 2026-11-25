"""Lab 9.1: 1000 individual inserts with w=1, majority, and w=3."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import run_writes,log_result

def main():
 rows=[run_writes('w1',1),run_writes('majority','majority'),run_writes('w3_all',3)]
 print('\nWRITE CONCERN COMPARISON')
 for r in rows: print(f"{str(r['w']):>9} | {r['total_ms']:>10} ms total | {r['avg_ms_per_attempt']:>8} ms/write | ack {r['acknowledged']}/1000")
 log_result('lab_9_1',rows)
if __name__=='__main__':main()
