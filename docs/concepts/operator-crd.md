# Operator, CRD, and Controller

## Mental Model

Kubernetes has built-in kinds:

```text
Pod
Deployment
StatefulSet
Service
Secret
ConfigMap
Job
```

A `CRD` teaches Kubernetes a new kind.

```text
CRD = Custom Resource Definition
```

After installing a CRD, Kubernetes can store and understand a new resource type.

## Controller

A controller is a pod running inside Kubernetes.

It watches resources and makes the real objects.

Built-in example:

```text
Deployment
  -> Kubernetes deployment controller
  -> ReplicaSet
  -> Pods
```

Custom example:

```text
Rollout CR
  -> Argo Rollouts controller
  -> ReplicaSet
  -> Pods
```

## Operator

An operator is a controller for a specific product.

It usually installs:

```text
CRDs
controller pod
RBAC permissions
```

## Argo Rollouts Example

Install:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/v1.9.0/download/install.yaml
```

This adds new kinds:

```text
Rollout
AnalysisTemplate
AnalysisRun
```

Then this works:

```text
task-service/k8s/rollout.yaml
  -> Rollout/task-service
  -> Argo controller creates ReplicaSets and Pods
```

## CloudNativePG Example

Install:

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.0.yaml
```

This adds new kinds:

```text
Cluster
Pooler
Backup
ScheduledBackup
```

Then this works:

```text
task-service/k8s/postgres-cnpg.yaml
  -> Cluster/task-db
  -> CloudNativePG controller creates PostgreSQL pods, PVCs, and services
```

And:

```text
task-service/k8s/pooler.yaml
  -> Pooler/task-db-pooler-rw
  -> CloudNativePG controller creates PgBouncer pods and service
```

## Source of Truth

Manual way:

```text
you create the low-level Kubernetes objects
```

Operator way:

```text
you create the custom resource
operator creates the low-level Kubernetes objects
```

Short version:

```text
CRD = new Kubernetes kind
Custom Resource = your YAML using that kind
Controller/Operator = pod that makes it real
```
