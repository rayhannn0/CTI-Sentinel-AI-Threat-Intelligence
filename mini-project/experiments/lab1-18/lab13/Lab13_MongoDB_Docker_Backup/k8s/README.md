# Kubernetes Lab 13.2 (requires a cluster and provisioned StorageClass)

This is NOT executed by `run_all.py`. Each pod copies the SAME keyfile from a Kubernetes Secret to an `emptyDir` using an initContainer. Generating a new key on each pod would break replica-set authentication.

```bash
# From Lab13_MongoDB_Docker project root; do not commit the keyfile
kubectl create secret generic mongo-keyfile --from-file=keyfile=./keyfile --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/mongo-headless-svc.yaml -f k8s/mongo-statefulset.yaml
kubectl rollout status statefulset/mongo --timeout=300s
kubectl get pods -l app=mongo
kubectl exec mongo-0 -- mongosh --quiet --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"mongo-0.mongo-headless-svc:27017"},{_id:1,host:"mongo-1.mongo-headless-svc:27017"},{_id:2,host:"mongo-2.mongo-headless-svc:27017"}]})'
# On a fresh cluster, create an admin user through the localhost exception from mongo-0
kubectl exec -it mongo-0 -- mongosh
# Inside mongosh: use admin; db.createUser({user:"lab13_k8s_admin",pwd:passwordPrompt(),roles:[{role:"root",db:"admin"}]})
# Then run authenticated rs.status(); you will be prompted for password:
kubectl exec -it mongo-0 -- mongosh -u lab13_k8s_admin --authenticationDatabase admin --password --eval 'rs.status().members.map(x=>({name:x.name,state:x.stateStr,health:x.health}))'
kubectl delete pod mongo-2
kubectl wait --for=condition=Ready pod/mongo-2 --timeout=300s
kubectl exec -it mongo-0 -- mongosh -u lab13_k8s_admin --authenticationDatabase admin --password --eval 'rs.status().members.map(x=>({name:x.name,state:x.stateStr,health:x.health}))'
```

Note: `kubectl delete pod` makes Kubernetes recreate the pod; watch until it is healthy and SECONDARY again. This sample uses one mongod per StatefulSet pod for learning, not an independently audited production deployment. Requires appropriate Kubernetes networking, storage and security policy.
