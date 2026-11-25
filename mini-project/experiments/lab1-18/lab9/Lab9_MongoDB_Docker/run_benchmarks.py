"""Inside runner image: run write concern and journaling experiments."""
import runpy
from pathlib import Path
R=Path(__file__).parent
for f in ['01_Lab_9_1/lab_9_1.py','02_Activity_9_1_Try_It_Yourself/activity_9_1.py']:
 print('\n===',f,'===',flush=True);runpy.run_path(str(R/f),run_name='__main__')
