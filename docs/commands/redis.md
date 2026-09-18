# Redis Commands

## Install Or Upgrade Operator

```powershell
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local template --selector name=redis-operator
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local diff --selector name=redis-operator
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local apply --selector name=redis-operator
kubectl rollout status deployment/redis-operator -n redis-operator --timeout=180s
```

## Reconcile Redis

Preferred flow:

```text
commit and push -> Argo CD platform-cache -> RedisCluster -> Redis Operator
```

Direct local check:

```powershell
kubectl apply --dry-run=server -k k8s/platform/cache/base
kubectl apply -k k8s/platform/cache/base
kubectl wait rediscluster/platform-redis -n task-api --for=jsonpath='{.status.state}'=Ready --timeout=300s
```

## Health

```powershell
kubectl get rediscluster platform-redis -n task-api -o wide
kubectl get pods -n task-api -l redis_setup_type=cluster -o wide
kubectl get sts,svc,pvc,pdb -n task-api | Select-String platform-redis

kubectl exec -n task-api platform-redis-leader-0 -- sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli cluster info'
kubectl exec -n task-api platform-redis-leader-0 -- sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli cluster nodes'
```

Healthy signals:

```text
STATE=Ready
3 ready leaders
3 ready followers
cluster_state:ok
cluster_slots_fail:0
cluster_known_nodes:6
```

## Application And Metrics Checks

```powershell
kubectl get --raw '/api/v1/namespaces/task-api/services/http:task-service:80/proxy/ready'
kubectl get --raw '/api/v1/namespaces/task-api/services/http:user-service:80/proxy/ready'

kubectl get --raw '/api/v1/namespaces/monitoring/services/http:redis-exporter:9121/proxy/metrics' |
  Select-String 'redis_up|redis_cluster_state'
```

Expected metrics are `redis_up 1` and `redis_cluster_state 1`.

## Debug

```powershell
kubectl get pods -n redis-operator -o wide
kubectl logs deployment/redis-operator -n redis-operator --since=10m --tail=200
kubectl get endpointslice -n redis-operator -l kubernetes.io/service-name=webhook-service
kubectl describe rediscluster platform-redis -n task-api
kubectl get events -n task-api --sort-by=.lastTimestamp | Select-Object -Last 50
kubectl get secretstore,externalsecret -n task-api
kubectl describe externalsecret redis-cluster-auth -n task-api
```

Do not edit operator-generated StatefulSets, expose passwords on the command
line, or delete production PVCs without a tested recovery procedure.
