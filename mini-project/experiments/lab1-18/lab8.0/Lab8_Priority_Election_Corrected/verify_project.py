from pathlib import Path
import ast,json
root=Path(__file__).resolve().parent
py=list(root.rglob('*.py'))
js=list(root.rglob('*.json'))
for f in py:ast.parse(f.read_text(encoding='utf8'))
for f in js: json.loads(f.read_text(encoding='utf8'))
print(f'PASS: {len(py)} Python scripts parsed and {len(js)} JSON files checked.')
print('Docker, replica elections and actual output require running on your Mac.')
