import runpy,traceback,sys
from pathlib import Path
root=Path(__file__).resolve().parent
scripts=['01_Lab_11_1/lab_11_1.py','02_Activity_11_1_Try_It_Yourself/activity_11_1.py','03_Lab_11_2/lab_11_2.py','04_Activity_11_2_Try_It_Yourself/activity_11_2.py']
for script in scripts:
    print('\n'+'='*55+'\n'+script+'\n'+'='*55,flush=True)
    try:runpy.run_path(str(root/script),run_name='__main__')
    except Exception:
        traceback.print_exc();sys.exit(1)
print('ALL FOUR LAB 11 ACTIVITIES FINISHED.')
