"""Continuously read a document from whatever member is elected PRIMARY."""
import sys, pathlib, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import DB_NAME, primary_name, member_client

def main():
    print('Monitoring every 2 seconds. In another Terminal run lab_8_2.py. Ctrl+C stops.')
    try:
        while True:
            name = primary_name()
            if not name:
                print('No primary (election in progress)')
            else:
                c = member_client(name)
                try:
                    item = c[DB_NAME]['replication_demo'].find_one({'_id': 'lab8-replication-document'})
                    print(f'Read via {name} | found={bool(item)}')
                except PyMongoError as e:
                    print('Read interrupted during election:', type(e).__name__)
                finally: c.close()
            time.sleep(2)
    except KeyboardInterrupt: print('Monitoring stopped.')

if __name__ == '__main__': main()
