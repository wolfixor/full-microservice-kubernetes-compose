# Current State

This is the current learning architecture in this repo.

## Entry Path

```text
client
  -> Kong Gateway
  -> service
  -> dependency
```

Main services:

```text
user-service
task-service
comment-service
search-service
activity-service
notification-service
```

## Deploy Style

```text
task-service
  -> Argo Rollout
  -> canary steps
  -> AnalysisRun checks Prometheus

most other services
  -> Deployment
```

## Security

```text
RBAC
  -> controls who can use Kubernetes API

ServiceAccount
  -> identity used by pods

Kyverno
  -> audits/blocks bad manifests

NetworkPolicy
  -> controls pod-to-pod traffic

Vault + ESO
  -> Vault stores secrets
  -> ESO syncs Vault secrets into Kubernetes Secrets
```

Current task-service secret flow:

```text
Vault secret/task-service/db
Vault secret/task-service/redis
  -> ExternalSecret
  -> Kubernetes Secrets:
       task-service-db-from-vault
       task-service-redis-from-vault
  -> task-service env vars
```

## Data And Messaging

```text
PostgreSQL
  -> CloudNativePG for task-service
  -> PgBouncer Pooler: task-db-pooler-rw
  -> Backup/WAL to object storage lab

Kafka
  -> Strimzi Operator
  -> KafkaTopic CRs
  -> producers: task/comment/user services
  -> consumers: search/activity services

Redis
  -> local Redis Cluster lab
  -> future production direction: Redis operator

Elasticsearch/Kibana
  -> ECK Operator
  -> search/log exploration
```

## Observability

```text
Prometheus Operator
  -> Prometheus CR
  -> ServiceMonitor CRs
  -> scrape configs
  -> Prometheus StatefulSet

Grafana
  -> dashboards

Alertmanager
  -> alert routing

Fluent Bit
  -> collects container logs
  -> sends logs to Elasticsearch
```

## Backup

```text
Velero
  -> Kubernetes object backup
  -> not enough alone for databases

CloudNativePG backup
  -> base backup
  -> WAL archive
  -> restore/PITR drill
```

## Production Direction

```text
raw YAML
  -> good for learning/debugging

production direction
  -> Helm/Kustomize
  -> GitOps with Argo CD
  -> operators for stateful systems
  -> tested backup/restore
  -> no downtime by default
```

