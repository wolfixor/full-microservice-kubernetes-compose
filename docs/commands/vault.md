# Vault Commands

## 1. Install Local Vault

```bash
kubectl apply -f k8s/vault/namespace.yaml
kubectl apply -f k8s/vault/vault-dev.yaml
kubectl rollout status deployment/vault -n vault --timeout=300s
kubectl get pods -n vault
```

Local image if pull is slow:

```bash
docker pull docker.arvancloud.ir/hashicorp/vault:1.17.6
docker tag docker.arvancloud.ir/hashicorp/vault:1.17.6 hashicorp/vault:1.17.6
```

This is dev mode only.

## 2. Open Vault UI

```bash
kubectl port-forward -n vault svc/vault 8200:8200
```

Open:

```text
http://localhost:8200
```

Login token:

```text
<vault-dev-token>
```

## 3. Configure Kubernetes Auth

Get pod:

```bash
VAULT_POD=$(kubectl get pod -n vault -l app=vault -o jsonpath='{.items[0].metadata.name}')
```

Linux shell:

```bash
kubectl exec -n vault "$VAULT_POD" -- sh -c '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$VAULT_DEV_TOKEN"
vault auth enable kubernetes || true
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"
'
```

PowerShell:

```powershell
kubectl exec -n vault <vault-pod-name> --% -- sh -c "export VAULT_ADDR=http://127.0.0.1:8200; export VAULT_TOKEN=$VAULT_DEV_TOKEN; vault auth enable kubernetes || true; TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token); vault write auth/kubernetes/config kubernetes_host=https://kubernetes.default.svc:443 kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt token_reviewer_jwt=$TOKEN"
```

Meaning:

```text
Vault can now validate Kubernetes ServiceAccount tokens.
```

## 4. Create Secret And Policy

```bash
kubectl cp k8s/vault/task-api-read-policy.hcl vault/"$VAULT_POD":/tmp/task-api-read.hcl

kubectl exec -n vault "$VAULT_POD" -- sh -c '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$VAULT_DEV_TOKEN"
vault secrets enable -path=secret kv-v2 || true
vault kv put secret/task-api/config username="$TASK_API_USERNAME" password="$TASK_API_PASSWORD"
vault kv put secret/task-service/db username="$TASK_DB_USERNAME" password="$TASK_DB_PASSWORD"
vault kv put secret/task-service/redis REDIS_PASSWORD="$TASK_REDIS_PASSWORD"
vault kv put secret/kibana/encryption-keys \
  securityEncryptionKey="$KIBANA_SECURITY_ENCRYPTION_KEY" \
  savedObjectsEncryptionKey="$KIBANA_SAVED_OBJECTS_ENCRYPTION_KEY" \
  reportingEncryptionKey="$KIBANA_REPORTING_ENCRYPTION_KEY"
vault policy write task-api-read /tmp/task-api-read.hcl
'
```

Meaning:

```text
secret/task-api/config exists in Vault
secret/task-service/db exists in Vault
secret/task-service/redis exists in Vault
secret/kibana/encryption-keys exists in Vault
policy task-api-read can read those secret paths
```

## 5. Bind Kubernetes Identity To Vault

```bash
kubectl apply -f k8s/vault/task-api-vault-reader.yaml
```

```bash
kubectl exec -n vault "$VAULT_POD" -- sh -c '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$VAULT_DEV_TOKEN"
vault write auth/kubernetes/role/task-api \
  bound_service_account_names=vault-secret-reader \
  bound_service_account_namespaces=task-api \
  policies=task-api-read \
  ttl=1h
'
```

Meaning:

```text
ServiceAccount task-api/vault-secret-reader
  -> can login to Vault role task-api
  -> receives policy task-api-read
```

## 6. Test Direct Vault Read

```bash
kubectl apply -f k8s/security-drills/vault-read-secret-pod.yaml
kubectl logs -n task-api vault-read-secret
```

Expected:

```text
Vault login token length: <number>
"username":"task-user"
"password":"<task-api-password>"
```

Clean up:

```bash
kubectl delete -f k8s/security-drills/vault-read-secret-pod.yaml --ignore-not-found
```

## 7. Install External Secrets Operator

See:

```text
docs/commands/external-secrets.md
```

Short check:

```bash
kubectl get pods -n external-secrets
kubectl api-resources --api-group=external-secrets.io
```

## 8. Sync Vault Secret Into Kubernetes

```bash
kubectl apply -f k8s/external-secrets/vault-secretstore.yaml
kubectl apply -f k8s/external-secrets/task-service-secrets.yaml
kubectl apply -f k8s/external-secrets/kibana-secrets.yaml
```

Check:

```bash
kubectl get secretstore,externalsecret -n task-api
kubectl get secret task-api-config -n task-api
kubectl get secret task-service-db-from-vault task-service-redis-from-vault -n task-api
kubectl get secret kibana-encryption-keys -n task-api
```

Expected:

```text
SecretStore vault-task-api     READY=True
ExternalSecret task-api-config READY=True SecretSynced
Secret task-api-config         exists
ExternalSecret task-service-db READY=True SecretSynced
ExternalSecret task-service-redis READY=True SecretSynced
ExternalSecret kibana-encryption-keys READY=True SecretSynced
```

## 9. Test Kubernetes Secret Read

```bash
kubectl apply -f k8s/security-drills/external-secret-read-pod.yaml
kubectl logs -n task-api external-secret-read
```

Expected:

```text
username=task-user
password=<task-api-password>
```

Clean up:

```bash
kubectl delete -f k8s/security-drills/external-secret-read-pod.yaml --ignore-not-found
```

## Debug

Vault:

```bash
kubectl get pods -n vault
kubectl logs -n vault deploy/vault
```

Vault config:

```bash
kubectl exec -n vault "$VAULT_POD" -- sh -c '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$VAULT_DEV_TOKEN"
vault auth list
vault read auth/kubernetes/role/task-api
vault kv get secret/task-api/config
vault kv get secret/task-service/db
vault kv get secret/task-service/redis
vault kv get secret/kibana/encryption-keys
'
```

ESO:

```bash
kubectl get pods -n external-secrets
kubectl describe secretstore vault-task-api -n task-api
kubectl describe externalsecret task-api-config -n task-api
kubectl describe externalsecret task-service-db -n task-api
kubectl describe externalsecret task-service-redis -n task-api
kubectl describe externalsecret kibana-encryption-keys -n task-api
```

Common failures:

```text
Vault pod not running
  -> image pull or readiness problem

Vault login denied
  -> ServiceAccount, Vault role, or policy mismatch

SecretStore not Ready
  -> ESO cannot connect/login to Vault

ExternalSecret not Ready
  -> wrong Vault path/property or policy denied

Secret exists but value is base64
  -> normal Kubernetes Secret behavior
```
