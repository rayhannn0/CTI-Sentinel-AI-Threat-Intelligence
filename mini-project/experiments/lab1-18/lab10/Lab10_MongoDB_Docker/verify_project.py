from pathlib import Path
import json
R=Path(__file__).resolve().parent
files=['lab_10_1.json','activity_10_1.json','lab_10_2.json','activity_10_2.json']
for file in files:
    p=R/'output'/file
    if not p.exists(): print('MISSING:',p);continue
    data=json.loads(p.read_text())
    print('OK',file,data.get('activity'))
