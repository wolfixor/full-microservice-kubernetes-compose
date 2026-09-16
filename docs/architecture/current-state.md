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
platform manifests
  -> Argo CD Applications
  -> manual sync for now

task-service
  -> Argo Rollout
  -> canary steps
  -> AnalysisRun checks Prometheus

most other services
  -> Deployment
```

Current Argo CD layout:

```text
k8s/argocd/projects/task-api-platform.yaml
  -> AppProject
  -> allowed repo, cluster, namespaces, resource kinds

k8s/argocd/applications/platform-root.yaml
  -> syncs k8s root manifests

k8s/argocd/applications/platform-rbac.yaml
  -> syncs k8s/rbac

k8s/argocd/applications/platform-networking.yaml
  -> syncs k8s/network-policies

k8s/argocd/applications/platform-observability.yaml
  -> syncs k8s/monitoring

k8s/argocd/applications/platform-messaging.yaml
  -> syncs k8s/kafka
```

GitOps flow:

```text
Git repo
  -> Argo CD Application
  -> Kubernetes API
  -> normal controllers/operators reconcile
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
  -> GitOps with Argo CD
  -> Helm/Kustomize
  -> operators for stateful systems
  -> tested backup/restore
  -> no downtime by default
```
