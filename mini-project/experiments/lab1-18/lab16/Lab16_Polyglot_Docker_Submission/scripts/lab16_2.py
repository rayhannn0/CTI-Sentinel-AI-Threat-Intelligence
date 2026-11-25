import json
from datetime import datetime
from app.fraud_service import live_service

def serializer(value):
    if isinstance(value,datetime):return value.isoformat()
    return str(value)

def main():
    service,(mongo,cluster,neo)=live_service()
    try:
        report=service.analyze_user('u1','tx100',3)
        print(json.dumps(report,indent=2,default=serializer))
        assert report['transaction'] and report['transaction']['txn_id']=='tx100'
        assert report['recent_events']
        assert report['related_accounts']
        assert not report['errors'],report['errors']
        print('LAB 16.2 INTEGRATION PASS')
    finally:
        mongo.close();cluster.shutdown();neo.close()
if __name__=='__main__':main()
