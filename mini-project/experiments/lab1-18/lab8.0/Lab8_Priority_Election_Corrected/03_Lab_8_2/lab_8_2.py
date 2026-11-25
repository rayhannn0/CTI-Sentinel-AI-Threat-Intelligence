"""Lab 8.2: Observe election after stepping down the current PRIMARY."""
import sys, pathlib, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import member_client, wait_for_primary, status_summary

def main():
    old = wait_for_primary()
    print('Primary BEFORE stepDown:', old)
    c = member_client(old)
    try:
        try:
            # May disconnect the client as soon as the node steps down.
            print(c.admin.command({'replSetStepDown': 20, 'secondaryCatchUpPeriodSecs': 5}))
        except PyMongoError as exc:
            print('Expected possible client disconnect during stepDown:', type(exc).__name__)
    finally: c.close()
    deadline = time.monotonic()+75
    new = None
    while time.monotonic() < deadline:
        try: new = wait_for_primary(timeout=8)
        except RuntimeError: pass
        if new and new != old: break
        time.sleep(2)
    if not new or new == old: raise RuntimeError('New primary was not observed in time')
    print('Primary AFTER stepDown:', new)
    status_summary()

if __name__ == '__main__': main()
