from common import save
result={'activity':'Activity 13.2','comparison':{'Docker Compose':'Simpler local deployment; container restart policy and named volumes; manual service discovery/init and failover verification.','Kubernetes StatefulSet':'Stable pod names and per-pod PVC; orchestrator re-creates deleted pods; more RBAC, storage, networking and secret management complexity.'},'actual_kubernetes_pod_recovery_test':'NOT EXECUTED automatically; see README kubectl commands'}
print(result);save('activity_13_2.json',result)
