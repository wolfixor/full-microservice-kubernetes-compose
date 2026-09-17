# Argo CD Bootstrap

Install Argo CD first:

```bash
kubectl apply -f k8s/argocd/namespace.yaml
kubectl apply --server-side --force-conflicts -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait deployment/argocd-server -n argocd --for=condition=Available --timeout=300s
```

Server-side apply avoids the large CRD annotation error:

```text
metadata.annotations: Too long
```

Bootstrap the project and child Applications once:

```bash
kubectl apply -f k8s/argocd/projects/task-api-platform.yaml
kubectl apply -f k8s/argocd/applications/platform-root.yaml
```

After that, `platform-root` renders `k8s/argocd/kustomization.yaml` and owns
the AppProject plus all child Applications. Child Applications own workloads;
the root Application does not deploy workloads directly.

These Applications use conservative autosync:

```text
selfHeal: true
prune: false
```

Full command doc:

```text
docs/commands/argocd.md
```
