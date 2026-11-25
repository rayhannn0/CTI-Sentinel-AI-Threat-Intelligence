from pathlib import Path
import json
OUT=Path('/app/output') if Path('/app/output').exists() else Path(__file__).resolve().parent/'output'
OUT.mkdir(parents=True,exist_ok=True)
def save(name,payload):
  file=OUT/name
  file.write_text(json.dumps(payload,indent=2,default=str)+'\n')
  print('Saved',file)
