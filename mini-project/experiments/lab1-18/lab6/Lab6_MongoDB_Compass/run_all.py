"""Runs all four Chapter 6 activities in required order."""
from pathlib import Path
import subprocess, sys
ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    "01_Lab_6_1/lab_6_1.py",
    "02_Activity_6_1_Try_It_Yourself/activity_6_1.py",
    "03_Lab_6_2/lab_6_2.py",
    "04_Activity_6_2_Try_It_Yourself/activity_6_2.py",
]
for script in SCRIPTS:
    print("\n" + "=" * 60, "\nRUNNING", script, flush=True)
    p = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT)
    if p.returncode:
        raise SystemExit(f"FAILED: {script} (exit code {p.returncode})")
print("\nAll four Lab 6 activities completed successfully.")
