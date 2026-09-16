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

Then add this repo to Argo CD:

```bash
kubectl apply -f k8s/argocd/projects/task-api-platform.yaml
kubectl apply -f k8s/argocd/applications/
```

These Applications use manual sync for now.

Full command doc:

```text
docs/commands/argocd.md
```
