# Argo CD

Argo CD is GitOps for Kubernetes.

It watches Git and compares it with the live cluster.

```text
Git repo
  -> Argo CD Application
  -> Kubernetes manifests
  -> cluster state
```

## What It Answers

```text
What should exist in the cluster?
```

If Git says a Deployment, Service, NetworkPolicy, or KafkaTopic should exist, Argo CD can show whether the cluster matches Git.

## Argo CD Vs Argo Rollouts

```text
Argo CD
  -> syncs desired state from Git

Argo Rollouts
  -> controls release strategy for one workload
  -> canary, blue/green, analysis, rollback
```

Example flow:

```text
developer changes task-service image tag in Git
  -> Argo CD sees Git changed
  -> Argo CD applies Rollout YAML
  -> Argo Rollouts starts canary
  -> Prometheus checks analysis metrics
  -> rollout promotes or aborts
```

## Sync, Health, Drift

```text
Synced
  -> live cluster matches Git

OutOfSync
  -> Git and cluster are different

Healthy
  -> Kubernetes resources are running correctly

Degraded
  -> resource exists but is not healthy
```

Drift means someone changed the cluster manually and now it does not match Git.

## Current Lab Rule

For now, Applications use conservative autosync.

```text
autosync: enabled
selfHeal: enabled
prune: disabled
```

That means Argo CD applies Git changes and repairs drift, but does not delete live resources that disappear from Git yet.

## Production Direction

```text
raw YAML
  -> grouped Argo CD Applications
  -> Helm/Kustomize overlays
  -> CI updates image tags in Git
  -> Argo CD syncs
```
