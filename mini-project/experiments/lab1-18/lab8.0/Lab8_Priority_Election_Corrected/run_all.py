"""Run all finite labs in safe order. Restore voter baseline before experiments."""
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TASKS=[
 ('01_Lab_8_1/lab_8_1.py','lab_8_1'),
 ('03_Lab_8_2/lab_8_2.py','lab_8_2'),
 ('04_Activity_8_2_Try_It_Yourself/activity_8_2.py','activity_8_2'),
 ('02_Activity_8_1_Try_It_Yourself/activity_8_1.py','activity_8_1'),
]
def execute(path,tag):
    print('\n=== '+tag+' ===', flush=True)
    p=subprocess.run([sys.executable,str(ROOT/path)],cwd=ROOT,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    print(p.stdout,flush=True)
    (ROOT/'output').mkdir(exist_ok=True)
    (ROOT/'output'/f'{tag}.txt').write_text(p.stdout,encoding='utf-8')
    if p.returncode: raise SystemExit(f'STOPPED: {tag}, exit={p.returncode}. Fix the error before continuing.')
def main():
    execute('bootstrap.py','bootstrap')
    execute('restore_baseline.py','restore_baseline')
    for path,name in TASKS: execute(path,name)
    print('ALL FOUR ACTIVITIES FINISHED. Generate report with python3 generate_report.py')
if __name__=='__main__': main()
