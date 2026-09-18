# Local Vault

This is an ephemeral Vault dev server for learning only. A restart removes its
policies, auth configuration, and secrets.

```bash
kubectl apply -k k8s/environments/local/platform/vault
```

After a Vault pod restart, restore the local lab state from the retained
Kubernetes Secrets:

```powershell
.\k8s\environments\local\platform\vault\restore-dev-vault.ps1
```

The script restores Vault Kubernetes authentication, policy, role, and secret
paths, then forces External Secrets reconciliation. It does not print secret
values. It requires the generated Kubernetes Secrets to still exist.

Production uses HA Vault with persistent integrated storage, TLS, unseal/key
management, audit devices, backups, and no dev root token.
