import subprocess,sys
ACTS=['setup_users.py','01_Lab_12_1/lab_12_1.py','02_Activity_12_1_Try_It_Yourself/activity_12_1.py','03_Lab_12_2/lab_12_2.py','04_Activity_12_2_Try_It_Yourself/activity_12_2.py']
for f in ACTS:
    print('\n'+'='*68+'\n'+f+'\n'+'='*68,flush=True)
    p=subprocess.run([sys.executable,f])
    if p.returncode:raise SystemExit(f'FAILED at {f}; fix before submitting')
print('\nALL FOUR LAB 12 ACTIVITIES FINISHED.',flush=True)
