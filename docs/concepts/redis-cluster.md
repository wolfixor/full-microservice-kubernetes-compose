# Redis Cluster

## Current Design

```text
Helmfile
  -> installs Redis Operator and RedisCluster CRD

Vault platform/shared.REDIS_PASSWORD
  -> External Secrets Operator
  -> Kubernetes Secret redis-cluster-auth

Git -> Argo CD platform-cache
  -> RedisCluster/platform-redis
  -> Redis Operator
  -> 3 leader pods + 3 follower pods
  -> Services + PVCs + PodDisruptionBudgets
```

The operator owns the generated StatefulSets. We edit the `RedisCluster` CR, not
the generated StatefulSets.

## Data Flow

Redis Cluster divides 16,384 hash slots among three leaders. Each leader has one
follower containing a copy of that shard.

```text
application
  -> platform-redis-leader:6379
  -> cluster-aware client discovers all Redis nodes
  -> key hash selects a slot
  -> request reaches the leader that owns the slot
```

All services use Redis database `0`; key prefixes such as `task:` and `user:`
provide logical separation.

## Failure Flow

```text
leader fails
  -> Redis members detect lost heartbeats
  -> its follower is promoted
  -> Redis Operator reconciles the Kubernetes resources
  -> cluster-aware clients refresh topology
```

The current PodDisruptionBudgets keep at least two leaders and two followers
available during voluntary disruption. They do not protect against simultaneous
node, storage, or zone loss.

## Local Versus Production

This lab is production-shaped but not production-sized:

| Area | Local lab | Production |
|---|---|---|
| Storage | `local-path`, tied to one node | replicated CSI storage across failure domains |
| Operator | 2 replicas | 2+ replicas with tested upgrades and alerts |
| Redis | 3 leaders, 3 followers | size from load tests and memory growth |
| Secrets | Vault dev mode | HA Vault with persistent storage and recovery keys |
| Recovery | pod/failover drills | tested Redis backup and disaster recovery |

Capacity cannot be estimated from user count alone. Measure operations per
second, value size, memory, hit rate, latency, connection count, and failover
behavior.

## Ownership Rule

```text
operator lifecycle  -> k8s/operators/helmfile.yaml.gotmpl
operator values     -> k8s/operators/values/redis-operator.yaml
Redis desired state -> k8s/platform/cache/base/platform-redis.yaml
credentials         -> k8s/platform/secrets/base/platform-secrets.yaml
traffic rules       -> k8s/platform/networking/base
metrics             -> k8s/platform/observability/base
```

Argo CD self-heal restores Git's version if somebody changes an owned resource
directly. Make durable changes in Git, then let Argo CD reconcile them.
