"""Execute all four Lab 10 activities in order inside the Docker runner."""
import subprocess,sys
ACTIVITIES=['01_Lab_10_1/lab_10_1.py','02_Activity_10_1_Try_It_Yourself/activity_10_1.py','03_Lab_10_2/lab_10_2.py','04_Activity_10_2_Try_It_Yourself/activity_10_2.py']
for activity in ACTIVITIES:
    print('\n'+'='*65+'\n'+activity+'\n'+'='*65,flush=True)
    r=subprocess.run([sys.executable,activity])
    if r.returncode:sys.exit(f'FAILED: {activity}, exit status {r.returncode}')
print('\nALL FOUR LAB 10 ACTIVITIES FINISHED. Output and exports saved in output/.')
