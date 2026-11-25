"""Output handling and transient-transaction retry used across exercises."""
import json, os, time
from pathlib import Path
from datetime import datetime, timezone
from bson import json_util
from pymongo.errors import PyMongoError

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'output'
OUTPUT.mkdir(exist_ok=True)

def dump(name, value):
    target=OUTPUT/name
    target.write_text(json_util.dumps(value, indent=2), encoding='utf-8')
    print('Saved', target)

def exported(name, collections):
    payload={'generated_at_utc':datetime.now(timezone.utc).isoformat(), 'collections':{col.name:list(col.find({}, {'_id':0})) for col in collections}}
    dump(name, payload)

def retry_transient(operation, max_attempts=6, base_delay=.1):
    for attempt in range(max_attempts):
        try:
            return operation()
        except PyMongoError as exc:
            if not exc.has_error_label('TransientTransactionError') or attempt == max_attempts-1:
                raise
            delay=base_delay*(2**attempt)
            print(f'TransientTransactionError: retry {attempt+1}/{max_attempts-1} in {delay:.3f}s')
            time.sleep(delay)
