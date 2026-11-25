"""Run all four Lab 4 exercises using the same connection.py."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "01_Lab_4_1/lab_4_1.py",
    "02_Activity_4_1_Try_It_Yourself/activity_4_1.py",
    "03_Lab_4_2/lab_4_2.py",
    "04_Activity_4_2_Try_It_Yourself/activity_4_2.py",
]
for script in SCRIPTS:
    print("\n" + "=" * 65, flush=True)
    print("RUNNING:", script, flush=True)
    subprocess.run([sys.executable, str(ROOT / script)], check=True)
print("\nDONE: Open MongoDB Compass -> localhost:27017 -> lab4 -> collections")
