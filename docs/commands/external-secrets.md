# External Secrets Commands

## Install Operator

Create namespace:

```bash
kubectl apply -f k8s/external-secrets/namespace.yaml
```

Install with Helm:

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm upgrade --install external-secrets external-secrets/external-secrets \
  -n external-secrets \
  --set installCRDs=true
```

PowerShell local path:

```powershell
C:\Users\Afra\scoop\shims\helm.exe repo add external-secrets https://charts.external-secrets.io
C:\Users\Afra\scoop\shims\helm.exe repo update
C:\Users\Afra\scoop\shims\helm.exe upgrade --install external-secrets external-secrets/external-secrets -n external-secrets --set installCRDs=true
```

If Helm fails with locked config/cache paths or a bad proxy, use workspace-local Helm paths:

```powershell
$env:HELM_CONFIG_HOME = "$PWD\.tmp\helm\config"
$env:HELM_CACHE_HOME = "$PWD\.tmp\helm\cache"
$env:HELM_DATA_HOME = "$PWD\.tmp\helm\data"
$env:HELM_REPOSITORY_CONFIG = "$PWD\.tmp\helm\repositories.yaml"
$env:HELM_REPOSITORY_CACHE = "$PWD\.tmp\helm\repository"
$env:TEMP = "$PWD\.tmp"
$env:TMP = "$PWD\.tmp"
$env:HTTP_PROXY = ''
$env:HTTPS_PROXY = ''
$env:http_proxy = ''
$env:https_proxy = ''
New-Item -ItemType Directory -Force .tmp\helm\config,.tmp\helm\cache,.tmp\helm\data,.tmp\helm\repository | Out-Null

C:\Users\Afra\scoop\shims\helm.exe repo add external-secrets https://charts.external-secrets.io
C:\Users\Afra\scoop\shims\helm.exe repo update
C:\Users\Afra\scoop\shims\helm.exe upgrade --install external-secrets external-secrets/external-secrets -n external-secrets --set installCRDs=true
```

Check:

```bash
kubectl get pods -n external-secrets
kubectl get crd externalsecrets.external-secrets.io secretstores.external-secrets.io
kubectl api-resources --api-group=external-secrets.io
```

Current installed ESO serves `external-secrets.io/v1`. If apply says `no matches for kind`, check the served versions:

```bash
kubectl get crd externalsecrets.external-secrets.io secretstores.external-secrets.io \
  -o jsonpath="{range .items[*]}{.metadata.name}{' '}{range .spec.versions[*]}{.name}{':served='}{.served}{' '}{end}{'\n'}{end}"
```

Image needed by all ESO pods:

```text
ghcr.io/external-secrets/external-secrets:v2.10.0
```

If pods stay in `ContainerCreating` while pulling:

```bash
docker pull ghcr.io/external-secrets/external-secrets:v2.10.0
kubectl rollout restart deployment/external-secrets -n external-secrets
kubectl rollout restart deployment/external-secrets-cert-controller -n external-secrets
kubectl rollout restart deployment/external-secrets-webhook -n external-secrets
```

## Apply Vault Sync

Vault must already be configured with:

```text
secret/task-api/config
secret/task-service/db
secret/task-service/redis
secret/kibana/encryption-keys
auth/kubernetes/role/task-api
policy task-api-read
ServiceAccount task-api/vault-secret-reader
```

Apply:

```bash
kubectl apply -f k8s/external-secrets/vault-secretstore.yaml
kubectl apply -f k8s/external-secrets/task-service-secrets.yaml
kubectl apply -f k8s/external-secrets/kibana-secrets.yaml
```

Check:

```bash
kubectl get secretstore,externalsecret -n task-api
kubectl describe externalsecret task-api-config -n task-api
kubectl describe externalsecret task-service-db -n task-api
kubectl describe externalsecret task-service-redis -n task-api
kubectl describe externalsecret kibana-encryption-keys -n task-api
kubectl get secret task-api-config -n task-api
kubectl get secret task-service-db-from-vault task-service-redis-from-vault -n task-api
kubectl get secret kibana-encryption-keys -n task-api
```

Apply task-service after the Vault-backed Secrets exist:

```bash
kubectl apply -f task-service/k8s/rollout.yaml
kubectl get pods -n task-api -l app=task-service
```

## Test Synced Secret

```bash
kubectl apply -f k8s/security-drills/external-secret-read-pod.yaml
kubectl get pod external-secret-read -n task-api
kubectl logs -n task-api external-secret-read
```

Expected:

```text
username=task-user
password=<task-api-password>
```

Clean up the test pod:

```bash
kubectl delete -f k8s/security-drills/external-secret-read-pod.yaml --ignore-not-found
```

## Debug

Operator:

```bash
kubectl get pods -n external-secrets
kubectl logs -n external-secrets deploy/external-secrets --tail=120
```

Resources:

```bash
kubectl describe secretstore vault-task-api -n task-api
kubectl describe externalsecret task-api-config -n task-api
kubectl get events -n task-api --sort-by=.lastTimestamp
```

Vault role:

```bash
kubectl exec -n vault <vault-pod-name> -- sh -c '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$VAULT_DEV_TOKEN"
vault read auth/kubernetes/role/task-api
vault kv get secret/task-api/config
vault kv get secret/task-service/db
vault kv get secret/task-service/redis
vault kv get secret/kibana/encryption-keys
'
```

Common failures:

```text
SecretStore not Ready
  -> Vault URL/auth/role problem

ExternalSecret not Ready
  -> wrong key/property or policy denied

Kubernetes Secret missing
  -> ESO has not synced yet or auth failed
```
