import urllib.request,json,os
from common import save
url=os.environ.get('EXPORTER_URL','http://mongodb-exporter:9216/metrics')
try:
 raw=urllib.request.urlopen(url,timeout=6).read().decode()
 result={'activity':'Activity 13.1','exporter_reachable':True,'metrics_lines':len(raw.splitlines()),'sample_metric_lines':[x for x in raw.splitlines() if x.startswith('mongodb_')][:8]}
except Exception as e:
 result={'activity':'Activity 13.1','exporter_reachable':False,'reason':str(e),'instructions':'Start monitoring profile: docker compose --profile monitoring up -d mongodb-exporter; rerun activity using docker compose --profile runner --profile monitoring run --rm labrunner python 02_Activity_13_1_Try_It_Yourself/activity_13_1.py'}
print(result);save('activity_13_1.json',result)
