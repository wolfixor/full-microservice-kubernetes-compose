# RBAC

RBAC controls who can do what in Kubernetes.

Core objects:

```text
ServiceAccount
  -> identity for a pod

Role
  -> permissions inside one namespace

ClusterRole
  -> permissions cluster-wide or reusable permission set

RoleBinding
  -> attaches a Role/ClusterRole to a user, group, or ServiceAccount inside one namespace

ClusterRoleBinding
  -> attaches a ClusterRole cluster-wide
```

## Workload Access

Most app pods do not need the Kubernetes API.

Current app identity:

```text
task-api-workload
  -> used by task-api app workloads
  -> automountServiceAccountToken: false
```

Meaning:

```text
pod has a clear identity
but no Kubernetes API token is mounted
```

This protects the cluster if an app container is compromised.

## Human Access

Example groups:

```text
platform-developers
  -> read pods, logs, services, events, workloads

platform-operators
  -> read more, exec when needed, patch/restart workloads, run jobs
```

Admins should be managed outside app manifests.

## Real RBAC Flow In This Repo

RBAC is always two parts:

```text
permission object
  -> Role or ClusterRole

identity attachment
  -> RoleBinding or ClusterRoleBinding
```

In this project, human access is here:

```text
k8s/platform/rbac/base/human-roles.yaml
```

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: task-api-developer
  namespace: task-api
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "services", "endpoints", "configmaps", "events"]
  verbs: ["get", "list", "watch"]
```

This means:

```text
inside namespace task-api
developer role can read pods, logs, services, endpoints, configmaps, events
developer role cannot change them
```

But a Role alone does nothing. It must be bound:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: task-api-developers
  namespace: task-api
subjects:
- kind: Group
  name: platform-developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: task-api-developer
  apiGroup: rbac.authorization.k8s.io
```

This means:

```text
users in group platform-developers
  -> receive task-api-developer permissions
  -> only inside task-api namespace
```

So the real flow is:

```text
developer@example.com
  -> belongs to group platform-developers
  -> RoleBinding points platform-developers to task-api-developer Role
  -> Role allows get/list/watch pods/log
  -> kubectl logs is allowed
```

## Adding A New Permission

Example request:

```text
Developers need to read ConfigMaps in task-api.
```

Check first:

```bash
kubectl auth can-i get configmaps \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api
```

If it says `no`, edit the developer Role:

```yaml
- apiGroups: [""]
  resources: ["pods", "pods/log", "services", "endpoints", "configmaps", "events"]
  verbs: ["get", "list", "watch"]
```

Apply:

```bash
kubectl apply -f k8s/platform/rbac/base/human-roles.yaml
```

Verify:

```bash
kubectl auth can-i get configmaps \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api
```

Expected:

```text
yes
```

The production habit is:

```text
1. define exact need
2. test current permission with kubectl auth can-i
3. edit the smallest Role rule
4. apply through GitOps later
5. verify allowed action
6. verify dangerous actions are still denied
```

Do not jump straight to:

```text
cluster-admin
* resources
* verbs
```

That is how production clusters become impossible to secure.

## Adding A New Role

Example request:

```text
Give support engineers read-only access to pods and logs, but not ConfigMaps.
```

Add a new Role:

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
```

Bind it to a group:

```yaml
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

Verify:

```bash
kubectl auth can-i get pods \
  --as=support@example.com \
  --as-group=platform-support \
  -n task-api

kubectl auth can-i get configmaps \
  --as=support@example.com \
  --as-group=platform-support \
  -n task-api
```

Expected:

```text
get pods -> yes
get configmaps -> no
```

## Workload ServiceAccount Flow

Pods can also have identities.

Important:

```text
ServiceAccount does not point to a Service.

Deployment/Rollout points Pods to a ServiceAccount.
Service points network traffic to Pods by labels.
```

The objects touch the Pod from different sides:

```text
ServiceAccount
  -> pod identity

Deployment / Rollout
  -> creates Pods
  -> sets serviceAccountName

Service
  -> routes network traffic
  -> selects Pods by labels
```

Example flow:

```text
task-service Deployment
  -> creates task-service Pods
  -> sets serviceAccountName: task-api-workload

task-service Pod
  -> runs as ServiceAccount task-api-workload
  -> has label app=task-service

task-service Service
  -> selector app=task-service
  -> sends HTTP traffic to those Pods
```

In this repo:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: task-api-workload
  namespace: task-api
automountServiceAccountToken: false
```

This means:

```text
pod identity exists
but Kubernetes API token is not mounted into the container
```

Deployment/Rollout example:

```yaml
spec:
  template:
    metadata:
      labels:
        app: task-service
    spec:
      serviceAccountName: task-api-workload
      automountServiceAccountToken: false
```

Service example:

```yaml
spec:
  selector:
    app: task-service
```

So:

```text
serviceAccountName controls pod identity.
Service selector controls network routing.
```

Why?

Most app containers do not need to call Kubernetes API.

If the app is compromised, the attacker should not automatically get a Kubernetes token from:

```text
/var/run/secrets/kubernetes.io/serviceaccount/token
```

If a workload really needs Kubernetes API access, then:

```text
1. create a dedicated ServiceAccount
2. allow token mount only for that workload
3. create a tiny Role
4. bind only that ServiceAccount
```

Example:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: log-reader
  namespace: task-api
automountServiceAccountToken: true
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: log-reader
  namespace: task-api
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: log-reader
  namespace: task-api
subjects:
- kind: ServiceAccount
  name: log-reader
  namespace: task-api
roleRef:
  kind: Role
  name: log-reader
  apiGroup: rbac.authorization.k8s.io
```

The flow:

```text
pod runs as ServiceAccount log-reader
  -> token is mounted
  -> RoleBinding attaches log-reader Role
  -> pod can read pod logs
  -> pod cannot read Secrets
```

## Least Privilege

Rule:

```text
give only the permission needed
for only the namespace needed
for only the identity that needs it
```

Do not give app workloads access to Secrets, pods, or deployments unless the app truly calls the Kubernetes API.

## Dangerous Permissions

Some permissions are more powerful than they look:

```text
secrets get/list/watch
  -> can expose DB passwords, tokens, TLS keys, cloud credentials

pods/exec create
  -> can open shell inside containers

pods/portforward create
  -> can reach private internal services

pods create
  -> can create a pod using another ServiceAccount

deployments patch/update
  -> can change image, command, env, mounted secrets, or restart workloads

rolebindings create/update
  -> can grant namespace permissions

clusterrolebindings create/update
  -> can grant cluster-wide permissions

serviceaccounts/token create
  -> can request a token for a ServiceAccount

impersonate users/groups/serviceaccounts
  -> can act as another identity
```

## Pod Creation Escalation

`create pods` can become privilege escalation.

Lab shape:

```text
operator cannot read secrets directly
operator can create pods
rbac-victim ServiceAccount can read secrets
operator creates pod with serviceAccountName: rbac-victim
pod receives rbac-victim token
pod can call Kubernetes API and read secrets
```

Lesson:

```text
Do not give humans create pods casually.
If operators need debugging, prefer pods/exec create without pods create.
```

RBAC rule shape:

```text
pods, pods/log
  -> get/list/watch

pods/exec
  -> create

pods
  -> no create
```

## Forbidden Errors

`Forbidden` means authentication worked, but authorization denied the action.

Debug flow:

```text
who am I?
what verb?
what resource?
which namespace?
which RoleBinding grants it?
```

Use `kubectl auth can-i` before changing RBAC.

## Break Glass

Emergency access should be:

```text
temporary
approved
audited
removed after incident
```

Production shape:

```text
normal operator access
  -> enough for common debugging

break-glass access
  -> temporary elevated access during incident
  -> namespace-scoped where possible
  -> removed after incident
```

In this project:

```text
platform-break-glass
  -> can read Secrets in task-api
  -> can exec into pods
  -> can patch workloads
  -> can create/delete jobs
  -> cannot create RoleBindings or ClusterRoleBindings
  -> cannot manage cluster-wide resources
```

Rule:

```text
Break-glass is not a normal daily role.
It is an emergency procedure with review and cleanup.
```

## Auditability

In production, RBAC is incomplete without audit logs.

You need to answer:

```text
who read a Secret?
who exec'd into a pod?
who changed a Role or RoleBinding?
who created a ClusterRoleBinding?
who patched a Deployment or Rollout?
who used break-glass access?
```

Kubernetes audit logs are API server logs. They record API requests such as:

```text
verb
resource
namespace
user
groups
source IP
response status
timestamp
```

Local learning limit:

```text
Docker Desktop / kind-style clusters may not expose production audit logs clearly.
For now, use kubectl auth can-i, Role/RoleBinding review, events, and manifest history.
Later prompt 38 covers Kubernetes audit logging properly.
```

Production rule:

```text
No permanent high privilege without audit.
No break-glass without approval, reason, timestamp, and cleanup.
```
