from pathlib import Path
import json
R=Path(__file__).parent
for f in ('lab_12_1','activity_12_1','lab_12_2','activity_12_2'):
 p=R/'output'/f'{f}.json'
 if not p.exists():raise SystemExit('Missing actual result: '+str(p))
 d=json.loads(p.read_text());print(f, 'PASS' if d.get('verified',d.get('tls_ping_verified',False)) else 'CHECK')
