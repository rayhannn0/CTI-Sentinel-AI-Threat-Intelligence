from pathlib import Path
from common import save
p=Path('/app/k8s') if Path('/app/k8s').exists() else Path(__file__).resolve().parents[1]/'k8s'
svc=(p/'mongo-headless-svc.yaml').read_text();sts=(p/'mongo-statefulset.yaml').read_text()
checks={'headless_service':'clusterIP: None' in svc, 'three_replicas':'replicas: 3' in sts,'persistent_claims':'volumeClaimTemplates:' in sts,'stable_headless_dns':'mongo-headless-svc' in sts,'shared_keyfile_secret':'mongo-keyfile' in sts,'init_container':'initContainers:' in sts}
assert all(checks.values()),checks
result={'activity':'Lab 13.2','manifest_static_checks':checks,'k8s_deployed':False,'note':'Static inspection only. Requires Kubernetes cluster and kubectl to validate deployment and pod recovery.'}
print(result);save('lab_13_2.json',result)
