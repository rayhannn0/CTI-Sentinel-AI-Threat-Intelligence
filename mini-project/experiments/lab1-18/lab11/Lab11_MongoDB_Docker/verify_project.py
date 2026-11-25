"""Offline project structure and source syntax checks (does not test Docker cluster)."""
from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parent
need=['Dockerfile','docker-compose.yml','bootstrap.py','run_all.py','connection.py','common.py','generate_report.py','make_submission_pdf.py','01_Lab_11_1/lab_11_1.py','02_Activity_11_1_Try_It_Yourself/activity_11_1.py','03_Lab_11_2/lab_11_2.py','04_Activity_11_2_Try_It_Yourself/activity_11_2.py']
for name in need:
    p=R/name
    assert p.exists(),name
    if p.suffix=='.py':ast.parse(p.read_text(),filename=name)
print('OFFLINE project structure + Python syntax PASS (live Docker not tested)')
