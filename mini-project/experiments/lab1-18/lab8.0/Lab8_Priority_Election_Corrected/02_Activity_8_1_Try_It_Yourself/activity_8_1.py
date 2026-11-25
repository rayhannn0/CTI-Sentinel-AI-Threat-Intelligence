"""Arbiter demo: 3 data members, but only 2 vote; arbiter is third vote.

Run LAST. An arbiter does not hold data. A data-bearing member with votes=0
remains a secondary. This is a classroom experiment, not production guidance.
"""
import sys, pathlib, subprocess, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from pymongo.errors import PyMongoError
from connection import member_client, wait_for_primary, status_summary
from docker_utils import compose

def main():
    compose('--profile', 'arbiter', 'up', '-d', 'arbiter')
    time.sleep(4)
    name=wait_for_primary()
    c=member_client(name)
    try:
        # Pin explicit majority write concern before switching the voting topology.
        c.admin.command({'setDefaultRWConcern': 1, 'defaultWriteConcern': {'w': 'majority'}})
        cfg=c.admin.command('replSetGetConfig')['config']
        hosts=[m['host'] for m in cfg['members']]
        if 'arbiter:27017' in hosts:
            print('Arbiter already configured; verifying status')
        else:
            # Keep one SECONDARY non-voting; ensures 2 data votes + 1 arbiter vote.
            m=next((m for m in cfg['members'] if m['host']=='mongo3:27017' and name!='mongo3'),None)
            if m is None:
                m=next((m for m in cfg['members'] if m['host']=='mongo2:27017' and name!='mongo2'),None)
            if m is None: raise RuntimeError('Expected a healthy data-bearing secondary for non-voting role')
            m['priority']=0
            m['votes']=0
            cfg['version']+=1
            c.admin.command({'replSetReconfig':cfg})
            print(m['host'], 'is now a non-voting secondary.')
    finally:c.close()
    time.sleep(5)
    c=member_client(wait_for_primary())
    try:
        cfg=c.admin.command('replSetGetConfig')['config']
        if not any(m['host']=='arbiter:27017' for m in cfg['members']):
            # Explicit add command demonstrates rs.addArb equivalent.
            next_id=max(m['_id'] for m in cfg['members'])+1
            cfg['members'].append({'_id':next_id,'host':'arbiter:27017','arbiterOnly':True})
            cfg['version']+=1
            c.admin.command({'replSetReconfig':cfg})
            print('Arbiter added as third voting member.')
        else: print('Arbiter already present.')
    finally:c.close()
    time.sleep(10)
    c=member_client(wait_for_primary())
    try:
        cfg=c.admin.command('replSetGetConfig')['config']
        votes=sum(m.get('votes',1) for m in cfg['members'])
        print('Members:',len(cfg['members']),'Election votes:',votes)
        assert votes==3, f'Expected odd number of votes (3), received {votes}'
    finally:c.close()
    status_summary()
    print('Why use an arbiter? Votes in elections without storing data; no reads/writes.')
    print('Note: 3 data-bearing voters is generally preferred for production.')

if __name__=='__main__':main()
