# Local Vault

This is an ephemeral Vault dev server for learning only. A restart removes its
policies, auth configuration, and secrets.

```bash
kubectl apply -k k8s/environments/local/platform/vault
```

Production uses HA Vault with persistent integrated storage, TLS, unseal/key
management, audit devices, backups, and no dev root token.
