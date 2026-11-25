"""Lab 7.2 activity: sample cache counters every 10 sec; discover report links.
Use --once for a single iteration, or --cycles 3 for finite monitoring.
"""
import argparse, hashlib, re, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import requests
from connection import get_db
from lab_7_2.lab_7_2 import cache_snapshot, hit_proxy

README_URL='https://raw.githubusercontent.com/jacobdjwilson/awesome-annual-security-reports/main/README.md'

def discover(db):
    try:
        response=requests.get(README_URL,timeout=15,headers={'User-Agent':'Lab7-CTI-Educational-Monitor/1.0'})
        response.raise_for_status()
        links=re.findall(r'\[([^\]]{5,180})\]\((https?://[^) ]+)\)',response.text)
        new_count=0
        for title,url in links[:1000]:
            if not ('report' in title.lower() or '.pdf' in url.lower()):
                continue
            key='GITHUB-'+hashlib.sha256(url.encode()).hexdigest()[:20]
            record={'_id':key,'title':title,'url':url,'source_id':'SRC-002',
                    'data_origin':'public_github_link_metadata','verified_threat':False}
            res=db.reports.update_one({'_id':key},{'$setOnInsert':record},upsert=True)
            if res.upserted_id is not None:
                new_count+=1
        return f'{new_count} new report metadata records'
    except requests.RequestException as exc:
        return f'Could not fetch report links: {exc}'

def run(cycles=None,discover_reports=True):
    db=get_db()
    previous=None
    tick=0
    print('Monitoring WiredTiger cache. Ctrl+C to stop.')
    try:
        while cycles is None or tick<cycles:
            current=cache_snapshot(db)
            if not current.get('available'):
                print('Cache metrics not available:',current.get('reason'))
            else:
                print('Cache occupancy:',current.get('cache_occupancy_pct'),
                      '% | approximate hit proxy:',hit_proxy(previous,current) if previous else 'baseline')
            previous=current
            if discover_reports and tick%6==0:
                print('Report discovery:',discover(db))
            tick+=1
            if cycles is None or tick<cycles:
                time.sleep(10)
    except KeyboardInterrupt:
        print('Monitor stopped')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true',help='One sample without waiting')
    parser.add_argument('--cycles',type=int,default=None,help='Number of 10-second samples')
    parser.add_argument('--no-discovery',action='store_true',help='Skip internet report discovery')
    options=parser.parse_args()
    if options.cycles is not None and options.cycles<1:
        parser.error('--cycles must be >= 1')
    run(cycles=1 if options.once else options.cycles,discover_reports=not options.no_discovery)
