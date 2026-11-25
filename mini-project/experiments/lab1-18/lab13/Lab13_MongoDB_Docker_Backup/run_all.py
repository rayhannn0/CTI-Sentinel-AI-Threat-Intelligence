import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
scripts=['01_Lab_13_1/lab_13_1.py','02_Activity_13_1_Try_It_Yourself/activity_13_1.py','03_Lab_13_2/lab_13_2.py','04_Activity_13_2_Try_It_Yourself/activity_13_2.py']
for s in scripts:
 print('\n'+'='*65+'\n'+s+'\n'+'='*65,flush=True)
 env=os.environ.copy();env['PYTHONPATH']=str(ROOT)
 p=subprocess.run([sys.executable,str(ROOT/s)],cwd=ROOT,env=env)
 if p.returncode:raise SystemExit(f'FAILED: {s}')
print('\nALL FOUR LAB 13 SCRIPTS FINISHED (Kubernetes execution is optional and not implied).')
