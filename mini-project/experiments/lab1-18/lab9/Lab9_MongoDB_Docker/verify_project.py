import ast,json
from pathlib import Path
r=Path(__file__).parent
py=list(r.rglob('*.py'));js=list(r.rglob('*.json'))
for f in py:ast.parse(f.read_text())
for f in js:json.loads(f.read_text())
print(f'PASS: {len(py)} Python files parsed; {len(js)} JSON files validated')
print('NOTE: Docker engine and MongoDB runtime testing require your Mac.')
