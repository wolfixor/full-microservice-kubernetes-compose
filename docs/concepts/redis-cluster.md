# Redis Cluster Flow

## Mental Model

The old Redis setup was one pod:

```text
redis Deployment
  -> one Redis pod
  -> emptyDir storage
```

The new Kubernetes setup is Redis Cluster:

```text
redis-cluster StatefulSet
  -> 6 Redis pods
  -> 3 masters
  -> 3 replicas
  -> persistent PVC per pod
```

## Why Redis Cluster

Redis Cluster gives:

```text
sharding
automatic failover
persistent storage
```

Keys are split across hash slots.

If a master fails, its replica can be promoted.

## Cluster Shape

Our current cluster has 6 pods:

```text
3 masters
3 replicas
```

Redis Cluster has 16384 hash slots.

With 3 masters, slots are split like this:

```text
master 1 -> slots 0-5460
master 2 -> slots 5461-10922
master 3 -> slots 10923-16383
```

When the app writes a key:

```text
task:123
```

Redis calculates the hash slot and sends the key to the correct master.

## Failover Flow

Each master has one replica.

```text
master fails
  -> cluster detects missing heartbeats
  -> replica is promoted
  -> replica becomes the new master
  -> cluster-aware clients refresh topology
  -> traffic continues
```

With 3 masters, this setup can usually tolerate 1 master failure if that master has a healthy replica.

## Kubernetes IP Change Problem

StatefulSet pod names are stable:

```text
redis-cluster-0
redis-cluster-1
```

But pod IPs can change after restart:

```text
old IP -> 10.244.1.46
new IP -> 10.244.1.30
```

Redis stores cluster node addresses in `nodes.conf`.

If `nodes.conf` keeps old pod IPs, Kubernetes pods can be `Running` but Redis Cluster can still fail:

```text
cluster_state:fail
cluster_slots_pfail:...
```

Our manifest fixes this on startup:

```text
read current POD_IP
update this pod's own line in /data/nodes.conf
start Redis with --cluster-announce-ip POD_IP
also announce stable pod hostname
```

This is one reason a Redis operator is better in production: it handles this kind of cluster repair logic for us.

## Capacity

There is no fixed number like "10k users" or "1M users".

Capacity depends on:

```text
Redis ops/sec
cache hit rate
key size
value size
TTL
CPU
memory
network
connection count
read/write ratio
```

Our current pod resources are small:

```text
request: 256Mi memory, 100m CPU
limit:   512Mi memory, 500m CPU
```

So this is production-shaped, not production-sized.

Production sizing should come from load testing.

## Important App Change

Redis Cluster only supports database `0`.

So service isolation is not done with DB numbers anymore.

Old:

```text
user -> db0
task -> db1
comment -> db2
search -> db3
```

New:

```text
all services -> db0
isolation -> key prefixes
```

Example:

```text
user:...
task:...
comment:...
search:...
```

## Apply Flow

```bash
kubectl apply -f k8s/redis-cluster.yaml
kubectl rollout status statefulset/redis-cluster -n task-api --timeout=300s
kubectl wait --for=condition=complete job/redis-cluster-init -n task-api --timeout=300s
```

Then update services to use Redis Cluster:

```bash
kubectl apply -f user-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/rollout.yaml
kubectl apply -f comment-service/k8s/deployment.yaml
kubectl apply -f search-service/k8s/deployment.yaml
```

## Check

```bash
kubectl exec -n task-api redis-cluster-0 -- \
  redis-cli -a supersecure cluster info

kubectl exec -n task-api redis-cluster-0 -- \
  redis-cli -a supersecure cluster nodes
```

## Current Note

Keep the old `redis-service` until all apps are confirmed healthy.

After cutover, it can be removed later.
