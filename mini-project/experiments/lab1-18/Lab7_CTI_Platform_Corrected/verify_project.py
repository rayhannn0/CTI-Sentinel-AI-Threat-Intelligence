"""Offline package validation: no MongoDB server required."""
from pathlib import Path
import ast,json
base=Path(__file__).resolve().parent
scripts=list(base.rglob('*.py'))
json_files=list(base.rglob('*.json'))
for file in scripts:
    ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
for file in json_files:
    json.loads(file.read_text(encoding='utf-8'))
assert all((base/name).exists() for name in (
    'connection.py','seed_db.py','run_all.py','backend/app.py','frontend/index.html',
    'lab_7_1/lab_7_1.py','activity_7_1/activity_7_1.py',
    'lab_7_2/lab_7_2.py','activity_7_2/activity_7_2.py'))
print(f'PASS: {len(scripts)} Python files parsed; {len(json_files)} JSON files validated')
print('NOTE: Real MongoDB connection and running website require your local server.')
