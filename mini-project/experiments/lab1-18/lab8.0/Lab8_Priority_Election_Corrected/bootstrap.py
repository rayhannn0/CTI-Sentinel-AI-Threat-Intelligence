"""Starts the three data-bearing nodes and initializes replica set (idempotent)."""
import time
from docker_utils import compose
from connection import wait_for_primary, status_summary

def main():
    compose('up','-d','mongo1','mongo2','mongo3')
    time.sleep(4)
    compose('exec','-T','mongo1','mongosh','--quiet','--eval',
        'try { rs.status(); print("Already initialized") } catch(e) { '
        'rs.initiate({_id:"rs0",members:[{_id:0,host:"mongo1:27017",priority:2},'
        '{_id:1,host:"mongo2:27017",priority:1},'
        '{_id:2,host:"mongo3:27017",priority:1}]}) }')
    print('Primary:', wait_for_primary())
    status_summary()

if __name__ == '__main__': main()
