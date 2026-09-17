# Production IaC Commands

Use this when converting raw manifests to production-style GitOps.

## Inspect Current State

```bash
kubectl get applications -n argocd
kubectl get applications -n argocd -o wide
kubectl get all -n task-api
kubectl get crd | sort
```

## Argo CD Checks

```bash
kubectl get application -n argocd
kubectl describe application platform-root -n argocd
kubectl describe application platform-secrets -n argocd
```

Force refresh:

```bash
kubectl annotate application -n argocd platform-root \
  argocd.argoproj.io/refresh=hard --overwrite
```

## Kustomize

Render:

```bash
kubectl kustomize k8s/environments/local
```

Validate client-side:

```bash
kubectl apply --dry-run=client --validate=false \
  -k k8s/environments/local
```

Diff against cluster:

```bash
kubectl diff -k k8s/environments/local
```

Apply manually only for local lab/testing:

```bash
kubectl apply -k k8s/environments/local
```

Production direction:

```text
Git commit -> Argo CD sync
not manual kubectl apply
```

## Helm

Render chart:

```bash
helm template <release> <chart> \
  -n <namespace> \
  -f values-local.yaml
```

Install or upgrade:

```bash
helm upgrade --install <release> <chart> \
  -n <namespace> \
  -f values-local.yaml
```

Rollback:

```bash
helm history <release> -n <namespace>
helm rollback <release> <revision> -n <namespace>
```

## Helm Diff

Install plugin:

```bash
helm plugin install https://github.com/databus23/helm-diff
```

Diff:

```bash
helm diff upgrade --allow-unreleased <release> <chart> \
  -n <namespace> \
  -f values-local.yaml
```

## Helmfile

Diff:

```bash
helmfile -f helmfile.yaml diff
```

Apply:

```bash
helmfile -f helmfile.yaml apply
```

Environment-specific:

```bash
helmfile -e local -f helmfile.yaml diff
helmfile -e prod -f helmfile.yaml diff
```

## Safe Migration Checklist

Before moving a component:

```text
1. Identify current owner.
   raw YAML, Argo app, Helm release, operator?

2. Check live health.
   pods ready, services endpoints, app route works

3. Render new desired state.
   helm template or kubectl kustomize

4. Diff.
   know exactly what will change

5. Keep rollback.
   previous Git commit, Helm revision, or original YAML

6. Apply through Argo CD.
   prefer GitOps over manual apply

7. Watch rollout.
   pods, events, logs, metrics

8. Verify behavior.
   curl endpoint, check dependencies, check alerts
```

## First Components To Convert

Start with low-risk platform pieces:

```text
rbac
network-policies
external-secrets
pgadmin
```

Current first conversion:

```bash
kubectl kustomize k8s/platform/rbac/base
kubectl apply --dry-run=client --validate=false -k k8s/platform/rbac/base
kubectl auth can-i get pods --as=developer@example.com --as-group=platform-developers -n task-api
kubectl auth can-i get secrets --as=developer@example.com --as-group=platform-developers -n task-api
kubectl auth can-i create pods --subresource=exec --as=operator@example.com --as-group=platform-operators -n task-api
kubectl auth can-i create pods --as=operator@example.com --as-group=platform-operators -n task-api
```

Current second conversion:

```bash
kubectl kustomize k8s/platform/secrets/base
kubectl apply --dry-run=client --validate=false -k k8s/platform/secrets/base
kubectl get application platform-secrets -n argocd
kubectl get secretstore,externalsecret -n task-api
```

Avoid first:

```text
postgres cluster
kafka cluster
elasticsearch
kong gateway
```

## Rollback Commands

GitOps rollback:

```bash
git revert <bad-commit>
git push origin main
kubectl annotate application -n argocd <app-name> \
  argocd.argoproj.io/refresh=hard --overwrite
```

Deployment rollback:

```bash
kubectl rollout history deployment/<name> -n <namespace>
kubectl rollout undo deployment/<name> -n <namespace>
```

Argo Rollouts rollback:

```bash
kubectl argo rollouts history <rollout-name> -n <namespace>
kubectl argo rollouts undo <rollout-name> -n <namespace>
```

Helm rollback:

```bash
helm history <release> -n <namespace>
helm rollback <release> <revision> -n <namespace>
```

## Debug Drift

```bash
kubectl get application -n argocd
kubectl describe application <app-name> -n argocd
kubectl get events -n argocd --sort-by=.lastTimestamp
```

Common drift reasons:

```text
manual kubectl edit/patch
operator adds fields
generated Secret changes
Argo app points to old Git revision
excluded file still applied manually
```
