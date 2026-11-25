import json
from pathlib import Path
from datetime import datetime
from bson import ObjectId
OUT=Path('/app/output') if Path('/app').is_dir() else Path(__file__).parent/'output'
OUT.mkdir(parents=True,exist_ok=True)
def save(name,data):
    path=OUT/f'{name}.json'
    path.write_text(json.dumps(data,indent=2,default=str))
    print('Saved',path)
