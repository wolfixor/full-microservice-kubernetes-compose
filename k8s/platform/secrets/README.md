# Platform Secrets

This Kustomize base manages the Vault-backed External Secrets resources used by
the `task-api` namespace.

```text
Vault
  -> SecretStore
  -> ExternalSecret
  -> Kubernetes Secret
  -> workload
```

Render without changing the cluster:

```bash
kubectl kustomize k8s/platform/secrets/base
```

Argo CD owns this base through the `platform-secrets` Application.
