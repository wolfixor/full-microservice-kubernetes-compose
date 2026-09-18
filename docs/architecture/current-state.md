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
  -> conservative autosync
  -> selfHeal enabled
  -> prune disabled for now

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
  -> renders k8s/argocd/kustomization.yaml
  -> owns the AppProject and child Applications only

k8s/argocd/applications/platform-rbac.yaml
  -> syncs k8s/platform/rbac/base

k8s/argocd/applications/platform-networking.yaml
  -> syncs k8s/platform/networking/base

k8s/argocd/applications/platform-observability.yaml
  -> syncs k8s/platform/observability/base

k8s/argocd/applications/platform-messaging.yaml
  -> syncs k8s/platform/messaging/base

k8s/argocd/applications/platform-secrets.yaml
  -> renders and syncs k8s/platform/secrets/base

k8s/argocd/applications/platform-cache.yaml
  -> syncs k8s/platform/cache/base

k8s/argocd/applications/platform-data.yaml
  -> syncs k8s/platform/data/task-db/base

k8s/argocd/applications/platform-workloads.yaml
  -> syncs k8s/environments/local/apps
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

Current Kibana secret flow:

```text
Vault secret/kibana/encryption-keys
  -> ExternalSecret
  -> Kubernetes Secret kibana-encryption-keys
  -> Kibana encryption env vars

Kubernetes Secret kibana-service-token
  -> Kibana authenticates to Elasticsearch
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

Repository ownership:

```text
k8s/operators                 Helmfile and offline operator bundles
k8s/platform/*/base           shared long-running resources
k8s/apps/*/base               long-running business workloads
k8s/apps/*/operations         migrations, backups, and drills (manual)
k8s/environments/local        local composition and local-only tools
k8s/security-drills           explicit manual tests, never autosynced
```
