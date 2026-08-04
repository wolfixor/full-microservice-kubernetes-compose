# Argo Rollouts Flow

## Mental Model

Argo Rollouts is a smarter replacement for a Kubernetes `Deployment`.

```text
Deployment
  -> replace pods with rolling update

Rollout
  -> release new pods slowly
  -> check Prometheus
  -> continue or rollback
```

## What We Added

```text
Argo Rollouts Controller
  -> watches Rollout CRs
  -> creates ReplicaSets and Pods
  -> creates AnalysisRuns
  -> uses Prometheus result to promote or stop
```

For now, only `task-service` uses Argo Rollouts.

## Rollout CR

File:

```text
task-service/k8s/rollout.yaml
```

This is the desired release plan for `task-service`.

```text
Rollout/task-service
  -> 10 replicas
  -> canary steps: 10%, 25%, 50%, 100%
  -> pause between steps
  -> run analysis between steps
```

The pod template is copied from the old `Deployment`, so the app config stays the same:

```text
PostgreSQL env
Redis env
Kafka env
liveness probe
readiness probe
```

The `Service` name stays `task-service`, so Kong does not need to change.

## AnalysisTemplate CR

File:

```text
task-service/k8s/analysis-template.yaml
```

This is the health check plan for the rollout.

```text
AnalysisTemplate
  -> Prometheus query for 5xx error rate
  -> Prometheus query for p95 latency
```

The Rollout references it by name:

```text
templateName: task-service-success-rate
```

When Argo reaches an analysis step, it creates an `AnalysisRun`.

```text
Rollout step
  -> AnalysisTemplate
  -> AnalysisRun
  -> Prometheus
  -> pass or fail
```

## Release Flow

```text
new task-service image
  -> Argo creates new ReplicaSet
  -> canary pods start
  -> 10%
  -> pause
  -> Prometheus analysis
  -> 25%
  -> pause
  -> Prometheus analysis
  -> 50%
  -> pause
  -> Prometheus analysis
  -> 100%
```

If error rate or latency is bad, the rollout stops.

## Exact Installation Flow

### Step 1: Install the Controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/v1.9.0/download/install.yaml
kubectl wait deployment/argo-rollouts -n argo-rollouts --for=condition=Available --timeout=300s
```

What this does:

```text
install.yaml contains:
  -> CRDs (Rollout, AnalysisTemplate, AnalysisRun, Experiment)
  -> Argo Rollouts Controller Deployment in argo-rollouts namespace
  -> RBAC (ClusterRole, ClusterRoleBinding, ServiceAccount)
```

After this step the cluster knows new kinds:

```text
Rollout
AnalysisTemplate
AnalysisRun
Experiment
```

And one new pod is running:

```text
argo-rollouts namespace
  -> argo-rollouts-xxx pod (Deployment)
```

### Step 2: Replace the Deployment with a Rollout

```bash
kubectl apply -f task-service/k8s/analysis-template.yaml
kubectl delete deployment task-service -n task-api
kubectl apply -f task-service/k8s/rollout.yaml
```

What this does:

```text
analysis-template.yaml contains kind: AnalysisTemplate
  -> defines Prometheus queries for error rate and latency
  -> not active yet, just a template

delete deployment task-service
  -> removes the old Deployment
  -> Argo Rollouts will manage pods from now on

rollout.yaml contains kind: Rollout
  -> Argo controller sees this CR
  -> creates ReplicaSets and Pods
  -> follows canary steps: 10%, 25%, 50%, 100%
  -> creates AnalysisRun at each step using the AnalysisTemplate
```

So you never manage task-service pods through a Deployment anymore.
The Rollout CR is the new source of truth.

```text
you apply:   kind: Rollout
controller creates: ReplicaSets
                    Pods
                    AnalysisRuns (at each canary step)
```

## Check

```bash
kubectl get rollout task-service -n task-api
kubectl describe rollout task-service -n task-api
kubectl get analysisrun -n task-api
```

With the Argo Rollouts plugin:

```bash
kubectl argo rollouts get rollout task-service -n task-api --watch
```

## Basic Canary Note

This version uses basic canary.

```text
10% canary
  -> roughly 1 canary pod out of 10 pods
```

Traffic still goes through the normal Kubernetes `Service`.

So this is pod-ratio canary, not exact request-level traffic splitting.

Exact traffic splitting comes later with Istio, Gateway API, or NGINX.
