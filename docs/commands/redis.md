# Redis Emergency

## Cluster Health

```powershell
kubectl get pods -n task-api -l app=redis-cluster
kubectl exec -n task-api redis-cluster-0 -- `
  redis-cli -c -a ${REDIS_PASSWORD} cluster info
kubectl exec -n task-api redis-cluster-0 -- `
  redis-cli -c -a ${REDIS_PASSWORD} cluster nodes
```

Healthy signal:

```text
cluster_state:ok
3 masters
3 replicas
```

## Check A Cache Key

```powershell
kubectl exec -n task-api redis-cluster-0 -- `
  redis-cli -c -a ${REDIS_PASSWORD} keys '*'
```

For a specific key:

```powershell
kubectl exec -n task-api redis-cluster-0 -- `
  redis-cli -c -a ${REDIS_PASSWORD} get '<key>'
```

## Common Failure

```text
pods Running but Redis Cluster broken
```

Check:

```text
nodes.conf may contain old pod IPs
cluster_state may be fail
```

Fix path for local lab:

```text
recreate cluster carefully
do not delete production Redis data without a backup
```
