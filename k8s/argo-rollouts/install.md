# Argo Rollouts Install

Argo Rollouts adds progressive delivery CRDs to Kubernetes.

It manages `Rollout` resources instead of normal `Deployment` resources.

## Install Controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/v1.9.0/download/install.yaml
kubectl wait deployment/argo-rollouts -n argo-rollouts --for=condition=Available --timeout=300s
```

## Verify

```bash
kubectl get pods -n argo-rollouts
kubectl get crd | grep rollouts
```

## Optional CLI

```bash
kubectl argo rollouts version
kubectl argo rollouts get rollout task-service -n task-api
```
