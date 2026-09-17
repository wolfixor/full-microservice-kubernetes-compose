# Argo CD Commands

## Install

```bash
kubectl apply -f k8s/argocd/namespace.yaml
kubectl apply --server-side --force-conflicts -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait deployment/argocd-server -n argocd --for=condition=Available --timeout=300s
```

Use server-side apply for the Argo CD install bundle because some CRDs are too large for normal client-side apply.

If you already hit this error:

```text
metadata.annotations: Too long: may not be more than 262144 bytes
```

run the same server-side apply command again:

```bash
kubectl apply --server-side --force-conflicts -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Then check the missing CRDs:

```bash
kubectl get crd applications.argoproj.io appprojects.argoproj.io applicationsets.argoproj.io
```

## Add This Repo

```bash
kubectl apply -f k8s/argocd/projects/task-api-platform.yaml
kubectl apply -f k8s/argocd/applications/
```

## Check

```bash
kubectl get pods -n argocd
kubectl get crd applications.argoproj.io appprojects.argoproj.io applicationsets.argoproj.io
kubectl get appprojects -n argocd
kubectl get applications -n argocd
kubectl describe application platform-root -n argocd
```

## Open UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open:

```text
https://localhost:8080
```

Get initial admin password:

```bash
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
```

User:

```text
admin
```

## Refresh

```bash
kubectl get applications -n argocd
kubectl annotate application -n argocd platform-rbac platform-networking platform-root platform-observability platform-messaging \
  argocd.argoproj.io/refresh=hard --overwrite
```

Refresh only tells Argo CD to compare Git and cluster again. It does not sync by itself.

## Autosync

The repo Applications use:

```yaml
syncPolicy:
  automated:
    prune: false
    selfHeal: true
```

Meaning:

```text
selfHeal: true
  -> if someone changes a managed object manually, Argo CD repairs it from Git

prune: false
  -> if something is removed from Git, Argo CD does not delete it from the cluster yet
```

Later, when the repo is cleaner, production GitOps usually enables prune carefully.

## What To Look For

```text
SYNC STATUS:
  Synced     -> Git matches cluster
  OutOfSync  -> Git and cluster differ

HEALTH:
  Healthy    -> resource is working
  Progressing -> still reconciling
  Degraded   -> resource exists but has a problem
```

## Rollback

GitOps rollback means revert Git, then sync again.

```bash
git revert <bad-commit>
git push
```

Then:

```bash
kubectl get application <app-name> -n argocd
```

For task-service release rollback, Argo Rollouts is still the release controller:

```bash
kubectl argo rollouts undo task-service -n task-api
```

## Current Applications

```text
platform-root
  -> k8s root YAML files

platform-rbac
  -> k8s/platform/rbac/base

platform-networking
  -> k8s/platform/networking/base

platform-observability
  -> k8s/platform/observability/base

platform-messaging
  -> k8s/platform/messaging/base
```

## Production Note

This is the first GitOps step.

Later we should move toward:

```text
apps/
platform/
clusters/local/
clusters/prod/
charts/
```

and render manifests with Helm or Kustomize before Argo CD syncs them.
