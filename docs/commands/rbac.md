# RBAC Commands

## Apply

```bash
kubectl apply -f k8s/platform/rbac/base/workload-serviceaccounts.yaml
kubectl apply -f k8s/platform/rbac/base/human-roles.yaml
```

Then apply/restart the workloads that use `task-api-workload`.

## Check ServiceAccounts

```bash
kubectl get serviceaccount -n task-api
kubectl get serviceaccount task-api-workload -n task-api -o yaml
```

## Check Pods Use The Workload Identity

```bash
kubectl get pods -n task-api -o custom-columns=NAME:.metadata.name,SA:.spec.serviceAccountName,AUTOMOUNT:.spec.automountServiceAccountToken
```

## Denied Access Tests

App workload should not list Secrets:

```bash
kubectl auth can-i list secrets \
  --as=system:serviceaccount:task-api:task-api-workload \
  -n task-api
```

Expected:

```text
no
```

App workload should not list pods:

```bash
kubectl auth can-i list pods \
  --as=system:serviceaccount:task-api:task-api-workload \
  -n task-api
```

Expected:

```text
no
```

## Human Group Checks

Developer can read pods:

```bash
kubectl auth can-i get pods \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api
```

Developer cannot update Secrets:

```bash
kubectl auth can-i update secrets \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api
```

Operator can patch deployments:

```bash
kubectl auth can-i patch deployments \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

Operator can exec:

```bash
kubectl auth can-i create pods --subresource=exec \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

Operator must not create arbitrary pods:

```bash
kubectl auth can-i create pods \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

Operator must not change RBAC:

```bash
kubectl auth can-i create rolebindings \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api

kubectl auth can-i create clusterrolebindings \
  --as=operator@example.com \
  --as-group=platform-operators
```

Expected:

```text
create pods --subresource=exec -> yes
create pods -> no
create rolebindings -> no
create clusterrolebindings -> no
```

## Pod Creation Escalation Lab

This lab shows why `create pods` is dangerous.

Create a victim ServiceAccount that can read Secrets:

```bash
kubectl create serviceaccount rbac-victim -n task-api

kubectl create role rbac-victim-secret-reader \
  -n task-api \
  --verb=get,list \
  --resource=secrets

kubectl create rolebinding rbac-victim-secret-reader \
  -n task-api \
  --role=rbac-victim-secret-reader \
  --serviceaccount=task-api:rbac-victim
```

Check victim permission:

```bash
kubectl auth can-i list secrets \
  --as=system:serviceaccount:task-api:rbac-victim \
  -n task-api
```

Expected:

```text
yes
```

If an operator can create pods, they can create a pod using that ServiceAccount:

```bash
kubectl run rbac-escalation-lab \
  -n task-api \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --as=operator@example.com \
  --as-group=platform-operators \
  --overrides='{"spec":{"serviceAccountName":"rbac-victim"}}' \
  --command -- sh -c "sleep 3600"
```

Use the mounted token from inside the pod:

```bash
kubectl exec -n task-api rbac-escalation-lab \
  --as=operator@example.com \
  --as-group=platform-operators \
  -- sh -c 'TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token); CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt; curl -s -o /tmp/secrets.json -w "%{http_code}\n" --cacert "$CACERT" -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/task-api/secrets; rm -f /tmp/secrets.json'
```

Expected in vulnerable RBAC:

```text
200
```

Clean up:

```bash
kubectl delete pod rbac-escalation-lab -n task-api --ignore-not-found
kubectl delete rolebinding rbac-victim-secret-reader -n task-api --ignore-not-found
kubectl delete role rbac-victim-secret-reader -n task-api --ignore-not-found
kubectl delete serviceaccount rbac-victim -n task-api --ignore-not-found
```

After fixing the operator Role, this should be blocked:

```bash
kubectl auth can-i create pods \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

Expected:

```text
no
```

## Debug Forbidden

Check the exact action:

```bash
kubectl auth can-i <verb> <resource> -n <namespace> --as=<identity>
```

Find bindings:

```bash
kubectl get rolebinding -n task-api
kubectl describe rolebinding task-api-developers -n task-api
kubectl describe rolebinding task-api-operators -n task-api
```

Find permissions:

```bash
kubectl describe role task-api-developer -n task-api
kubectl describe role task-api-operator -n task-api
```

Rule:

```text
Do not fix Forbidden by adding cluster-admin.
Find the missing verb/resource/namespace and add the smallest permission.
```

## Add Permission Flow

Example: allow operators to restart deployments by patching deployments.

1. Check current permission:

```bash
kubectl auth can-i patch deployments \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

2. Edit `k8s/platform/rbac/base/human-roles.yaml`:

```yaml
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch", "patch"]
```

3. Apply:

```bash
kubectl apply -f k8s/platform/rbac/base/human-roles.yaml
```

4. Verify allowed action:

```bash
kubectl auth can-i patch deployments \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

5. Verify dangerous actions are still denied:

```bash
kubectl auth can-i create pods \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api

kubectl auth can-i create rolebindings \
  --as=operator@example.com \
  --as-group=platform-operators \
  -n task-api
```

Expected:

```text
patch deployments -> yes
create pods -> no
create rolebindings -> no
```

## Add New Role Flow

Example: create support read-only access.

Add this to a new file or to `k8s/platform/rbac/base/human-roles.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: task-api-support
  namespace: task-api
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "events"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: task-api-support
  namespace: task-api
subjects:
- kind: Group
  name: platform-support
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: task-api-support
  apiGroup: rbac.authorization.k8s.io
```

Apply and test:

```bash
kubectl apply -f k8s/platform/rbac/base/human-roles.yaml

kubectl auth can-i get pods \
  --as=support@example.com \
  --as-group=platform-support \
  -n task-api

kubectl auth can-i get secrets \
  --as=support@example.com \
  --as-group=platform-support \
  -n task-api
```

Expected:

```text
get pods -> yes
get secrets -> no
```

## Break Glass

Apply temporary namespace-scoped emergency access:

```bash
kubectl apply -f k8s/platform/rbac/base/break-glass.yaml
```

Break-glass can read Secrets in `task-api`:

```bash
kubectl auth can-i get secrets \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api
```

Break-glass can exec:

```bash
kubectl auth can-i create pods --subresource=exec \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api
```

Break-glass can patch deployments:

```bash
kubectl auth can-i patch deployments \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api
```

Break-glass must not change RBAC:

```bash
kubectl auth can-i create rolebindings \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api

kubectl auth can-i create clusterrolebindings \
  --as=incident-user@example.com \
  --as-group=platform-break-glass
```

Expected:

```text
get secrets -> yes
create pods --subresource=exec -> yes
patch deployments -> yes
create rolebindings -> no
create clusterrolebindings -> no
```

Remove access after the incident:

```bash
kubectl delete rolebinding task-api-break-glass -n task-api
```

Verify access is gone:

```bash
kubectl auth can-i get secrets \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api
```

Expected:

```text
no
```

## Auditability Checks

Check current RBAC objects:

```bash
kubectl get role,rolebinding -n task-api
kubectl describe role task-api-operator -n task-api
kubectl describe rolebinding task-api-operators -n task-api
```

Check who would be allowed before granting access:

```bash
kubectl auth can-i get secrets \
  --as=incident-user@example.com \
  --as-group=platform-break-glass \
  -n task-api
```

Check recent namespace events:

```bash
kubectl get events -n task-api --sort-by=.lastTimestamp
```

Find break-glass bindings:

```bash
kubectl get rolebinding -n task-api \
  -l access.openai.local/type=break-glass
```

Review break-glass reason:

```bash
kubectl get rolebinding task-api-break-glass -n task-api \
  -o jsonpath='{.metadata.annotations.access\.openai\.local/reason}{"\n"}'
```

Local limit:

```text
These commands do not replace Kubernetes audit logs.
They are local learning checks.
Production needs API server audit logs shipped to a log system.
```

Production audit targets:

```text
secrets get/list/watch
pods/exec create
pods/portforward create
deployments patch/update
roles or rolebindings create/update/delete
clusterroles or clusterrolebindings create/update/delete
serviceaccounts/token create
impersonate users/groups/serviceaccounts
```
