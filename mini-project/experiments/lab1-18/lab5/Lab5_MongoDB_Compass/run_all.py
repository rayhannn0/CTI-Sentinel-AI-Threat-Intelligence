"""Run all four exercises from the project root."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "01_Lab_5_1/lab_5_1.py",
    "02_Activity_5_1_Try_It_Yourself/activity_5_1.py",
    "03_Lab_5_2/lab_5_2.py",
    "04_Activity_5_2_Try_It_Yourself/activity_5_2.py",
]
for script in SCRIPTS:
    print(f"\n{'='*66}\nRUNNING {script}\n{'='*66}", flush=True)
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT)
    if result.returncode:
        raise SystemExit(f"Stopped: {script} failed (code {result.returncode})")
print("\nSUCCESS: Four activities completed. Refresh the lab5 database in Compass.")
