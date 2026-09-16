# Production Infrastructure As Code

Prompt 34 is the move from lab manifests to production repository style.

The goal is not "put everything in Helm".
The goal is:

```text
reviewed Git changes
  -> reproducible render
  -> Argo CD sync
  -> operators reconcile
  -> safe rollout and rollback
```

## Current State

This repo still has many raw YAML manifests.

That was useful for learning because every object is visible:

```text
Deployment
Service
NetworkPolicy
Role
ExternalSecret
KafkaTopic
PrometheusRule
```

But production needs stronger structure:

```text
clear ownership
environment overlays
repeatable install order
diff before apply
rollback path
no manual drift
```

## Target Repository Shape

```text
k8s/
  operators/
    -> operator installs, CRDs, controllers

  platform/
    -> shared platform services and cluster policies

  apps/
    -> business services and gateway

  environments/
    local/
    dev/
    staging/
    prod/
```

Meaning:

```text
operators
  -> Strimzi, CloudNativePG, ECK, Prometheus Operator, ESO, Kyverno, Argo Rollouts

platform
  -> Kafka cluster, monitoring, logging, Vault, network policies, RBAC, Redis, storage

apps
  -> user/task/comment/search/activity/notification services and Kong

environments
  -> what changes between local/dev/staging/prod
```

## Helm

Helm packages Kubernetes manifests as charts.

Use Helm when:

```text
third-party tool already has a good chart
many repeated objects need values
release lifecycle matters
```

Examples:

```text
external-secrets operator
kyverno
trivy-operator
grafana
prometheus stack
```

Do not force Helm everywhere.
For CRs and policies, raw YAML or Kustomize can be clearer.

## Values Files

Values files hold environment-specific inputs.

Example shape:

```text
values-local.yaml
values-dev.yaml
values-staging.yaml
values-prod.yaml
```

Typical differences:

```text
replicas
image tag
resource requests/limits
storage size
domain names
ingress class
feature flags
retention days
```

Secrets should not live in values files.
Secrets should come from Vault via External Secrets.

## Kustomize

Kustomize patches YAML without templating everything.

Use Kustomize when:

```text
we already have good raw YAML
we need small environment patches
we want readable Kubernetes objects
```

Typical shape:

```text
base/
  deployment.yaml
  service.yaml
  kustomization.yaml

overlays/local/
  kustomization.yaml
  patch-replicas.yaml

overlays/prod/
  kustomization.yaml
  patch-resources.yaml
```

Kustomize is the safest first step for this repo because we already have raw manifests.

## Helmfile Vs Helmsman

Both manage many Helm releases.

Helmfile:

```text
YAML file lists releases
supports environments
supports helm diff
common in platform repos
```

Helmsman:

```text
desired-state file for Helm releases
focuses on installed release state
less common than Helmfile in many teams
```

Recommended direction for this repo:

```text
Kustomize first for existing YAML
Helmfile later for operator/platform Helm charts
Argo CD for continuous reconciliation
```

## Release Ordering

Some things must exist before others.

Example:

```text
1. Namespace
2. CRD/operator
3. SecretStore/Vault auth
4. Custom resources
5. Workloads that depend on them
```

Real examples:

```text
Strimzi operator
  -> Kafka CR
  -> KafkaTopic CRs
  -> services use Kafka

CloudNativePG operator
  -> Cluster CR
  -> Pooler CR
  -> task-service uses PgBouncer

External Secrets Operator
  -> SecretStore
  -> ExternalSecret
  -> app Deployment reads generated Secret
```

In Argo CD, ordering can be handled with:

```text
separate Applications
sync waves
app-of-apps
ApplicationSet
manual promotion gates for sensitive systems
```

## Environment Drift

Drift means live cluster state differs from Git.

Examples:

```text
someone manually changed replicas
someone edited a ConfigMap with kubectl
someone patched an image tag
someone created a Secret by hand
```

Production rule:

```text
Git is desired state.
Manual changes are temporary incident actions.
After incident, commit the correct desired state or revert live drift.
```

Argo CD helps detect and repair drift.

## GitOps Reconciliation

```text
Git commit
  -> Argo CD detects revision
  -> renders manifests
  -> compares desired vs live
  -> applies changes
  -> Kubernetes controllers/operators reconcile
```

For this repo:

```text
Argo CD syncs Applications
Operators reconcile CRDs
Argo Rollouts controls progressive app rollout
External Secrets syncs Vault secrets
Prometheus Operator builds scrape config
Strimzi manages Kafka
CloudNativePG manages PostgreSQL
```

## Migration Rule

Do not move everything at once.

Use this order:

```text
1. Create target structure and docs
2. Convert one low-risk component
3. Render/diff before apply
4. Let Argo sync
5. Verify health
6. Repeat component by component
```

Good first candidates:

```text
external-secrets
rbac
network-policies
pgadmin
```

Current first conversion:

```text
rbac
  old raw path: k8s/rbac
  production path: k8s/platform/rbac/base
  Argo CD app: platform-rbac
```

Risky candidates:

```text
CloudNativePG database
Kafka cluster
Elasticsearch
Kong gateway
```

Those need stronger backup, rollback, and maintenance windows.

## Interview Answer

```text
Raw YAML is good for learning and debugging.
In production I prefer GitOps with Helm/Kustomize because environments need repeatable renders, reviewed diffs, and drift detection.
I use Helm for third-party charts and repeated templates, Kustomize for readable overlays on existing YAML, External Secrets for secret material, and Argo CD as the reconciliation engine.
For stateful systems I keep CRD/operator ordering explicit and migrate one component at a time with health checks and rollback.
```
