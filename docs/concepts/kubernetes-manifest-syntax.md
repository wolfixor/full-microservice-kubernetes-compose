# Kubernetes Manifest Syntax

This is the fast-review map for reading and writing Kubernetes YAML in this repo.

## Basic Shape

Almost every manifest has this shape:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-service
  namespace: task-api
  labels:
    app: search-service
spec:
  replicas: 1
```

Meaning:

```text
apiVersion -> which Kubernetes API understands this object
kind       -> what object this is
metadata   -> name, namespace, labels, annotations
spec       -> desired state
```

Examples:

```text
apiVersion: v1
kind: Service
  -> built-in Kubernetes core API

apiVersion: apps/v1
kind: Deployment
  -> built-in Kubernetes apps API

apiVersion: kafka.strimzi.io/v1
kind: Kafka
  -> custom API installed by Strimzi CRDs

apiVersion: postgresql.cnpg.io/v1
kind: Cluster
  -> custom API installed by CloudNativePG CRDs
```

If Kubernetes says `no matches for kind`, the CRD/controller is probably not installed yet.

## Metadata

### Labels

Labels identify and group objects.

```yaml
labels:
  app: search-service
  app.kubernetes.io/part-of: task-api-platform
```

Meaning:

```text
app=search-service
  -> usually used by Services, NetworkPolicies, and kubectl selectors

app.kubernetes.io/part-of=task-api-platform
  -> this object belongs to the platform
```

Useful commands:

```bash
kubectl get pods -n task-api -l app=search-service
kubectl get all -n task-api -l app.kubernetes.io/part-of=task-api-platform
```

Labels do not do anything by themselves. Other objects use them with selectors.

### Annotations

Annotations attach extra metadata.

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

Meaning:

```text
Prometheus may scrape this object on port 8000 and path /metrics.
```

Labels are for selecting.
Annotations are for extra instructions/information.

## Selectors

Selectors connect objects to pods.

Deployment selector:

```yaml
selector:
  matchLabels:
    app: search-service
```

Service selector:

```yaml
spec:
  selector:
    app: search-service
```

NetworkPolicy selector:

```yaml
spec:
  podSelector:
    matchLabels:
      app: search-service
```

Meaning:

```text
find pods with label app=search-service
```

The label is on the Pod template:

```yaml
template:
  metadata:
    labels:
      app: search-service
```

If selector and pod labels do not match, traffic/policies/controllers will not target the pod.

## Deployment

Deployment runs stateless pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: search-service
  template:
    metadata:
      labels:
        app: search-service
    spec:
      containers:
      - name: search-service
        image: registry.example.com/search-service:1.0.0
```

Flow:

```text
Deployment
  -> creates ReplicaSet
  -> creates Pods
```

Use Deployment for:

```text
API services
workers
gateways
stateless tools
```

## Service

Service gives pods a stable network name.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: search-service
spec:
  selector:
    app: search-service
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP
```

Meaning:

```text
Service name: search-service
Service port: 80
Pod port: 8000
Target pods: app=search-service
```

Request flow:

```text
other pod
  -> http://search-service
  -> Service port 80
  -> selected Pod port 8000
```

## Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

Liveness:

```text
Is the container alive?
If it fails repeatedly, kubelet restarts the container.
```

Readiness:

```text
Is the pod ready for traffic?
If it fails, Kubernetes removes the pod from Service endpoints.
The pod keeps running.
```

Mental model:

```text
liveness  -> should I restart it?
readiness -> should I send traffic to it?
```

Production rule:

```text
readiness can check dependencies
liveness should not be too strict
```

If liveness depends on a slow database, Kubernetes may restart healthy apps during a database incident.

## Resources

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Meaning:

```text
requests -> scheduler reserves this much capacity
limits   -> container cannot exceed this limit
```

CPU:

```text
1000m = 1 CPU core
200m  = 0.2 CPU core
```

Memory:

```text
256Mi = 256 mebibytes
```

Production note:

```text
missing requests -> bad scheduling
missing limits   -> noisy neighbor risk
too low limits   -> throttling or OOMKilled
```

## Environment Variables

Plain value:

```yaml
- name: APP_NAME
  value: "search-service"
```

Value from Secret:

```yaml
- name: ELASTICSEARCH_PASSWORD
  valueFrom:
    secretKeyRef:
      name: elasticsearch-es-elastic-user
      key: elastic
```

Meaning:

```text
read key elastic from Kubernetes Secret elasticsearch-es-elastic-user
put it into env var ELASTICSEARCH_PASSWORD
```

Production direction:

```text
Vault
  -> ExternalSecret
  -> Kubernetes Secret
  -> env var / mounted file
```

## Init Containers

Init containers run before the main container.

```yaml
initContainers:
- name: wait-for-elasticsearch
  image: curlimages/curl:8.10.1
  command:
  - sh
  - -c
  - |
    until curl -fsS http://elasticsearch-es-http:9200; do
      sleep 5
    done
```

Flow:

```text
init container succeeds
  -> main container starts

init container fails
  -> main container does not start yet
```

Use for:

```text
wait for dependency
prepare files
run small bootstrap checks
```

Do not put long business logic in init containers.

## Jobs

Job runs something until it succeeds.

```yaml
apiVersion: batch/v1
kind: Job
spec:
  backoffLimit: 3
```

`backoffLimit: 3` means:

```text
retry failed pods
after 3 failed retries, mark the Job failed
```

Use Job for:

```text
database migration
one-time setup
backup drill
batch task
```

## StatefulSet And Storage

StatefulSet is for stable pod identity and stable storage.

```yaml
volumeClaimTemplates:
- metadata:
    name: postgres-data
  spec:
    accessModes: ["ReadWriteOnce"]
    resources:
      requests:
        storage: 1Gi
```

Meaning:

```text
create one PVC per StatefulSet pod
```

Example:

```text
postgres-0 -> postgres-data-postgres-0
postgres-1 -> postgres-data-postgres-1
```

`ReadWriteOnce` means:

```text
volume can be mounted read/write by one node at a time
```

Good for databases.

## ServiceAccount, Role, RoleBinding

This is the part that usually feels confusing.

### The Short Version

```text
ServiceAccount -> who the pod is
Role           -> what actions are allowed
RoleBinding    -> attach the Role to the identity
```

Full flow:

```text
Pod
  -> runs as ServiceAccount
  -> ServiceAccount is bound to Role
  -> Role allows verbs on resources
  -> Kubernetes API allows or denies requests
```

### ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: task-api-workload
  namespace: task-api
automountServiceAccountToken: false
```

Meaning:

```text
create pod identity task-api-workload
do not automatically mount a Kubernetes API token
```

### Pod Uses ServiceAccount

```yaml
spec:
  serviceAccountName: task-api-workload
  automountServiceAccountToken: false
```

Meaning:

```text
this pod runs as task-api-workload
but cannot easily call Kubernetes API because token mount is disabled
```

Use this for normal app pods.

### Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: task-api-developer
  namespace: task-api
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "services"]
  verbs: ["get", "list", "watch"]
```

Meaning:

```text
inside namespace task-api
allow read access to pods, pod logs, and services
```

`apiGroups: [""]` means core API group.

Core resources:

```text
pods
services
secrets
configmaps
endpoints
serviceaccounts
```

Other examples:

```text
apiGroups: ["apps"]
resources: ["deployments", "statefulsets"]

apiGroups: ["batch"]
resources: ["jobs", "cronjobs"]

apiGroups: ["argoproj.io"]
resources: ["rollouts"]
```

### RoleBinding

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

Meaning:

```text
bind group platform-developers
to Role task-api-developer
inside namespace task-api
```

`apiGroup: rbac.authorization.k8s.io` tells Kubernetes:

```text
this subject/roleRef belongs to the RBAC API group
```

### RBAC Step By Step

When you need new access, do this:

```text
1. Who needs access?
   user, group, or ServiceAccount

2. In which namespace?
   task-api, kafka, monitoring, etc.

3. Which resource?
   pods, pods/log, deployments, secrets, jobs

4. Which verbs?
   get, list, watch, create, patch, update, delete

5. Create or edit Role

6. Create RoleBinding

7. Verify allowed action

8. Verify dangerous actions are still denied
```

Commands:

```bash
kubectl auth can-i get pods \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api

kubectl auth can-i get secrets \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api
```

Expected production habit:

```text
needed action -> yes
dangerous action -> no
```

### Pod ServiceAccount RBAC Example

If a pod really needs Kubernetes API access:

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

Then Deployment:

```yaml
spec:
  template:
    spec:
      serviceAccountName: log-reader
      automountServiceAccountToken: true
```

Flow:

```text
pod runs as log-reader
  -> token is mounted
  -> RoleBinding grants log-reader Role
  -> pod can get/list pods and pod logs
```

Do not give app pods `secrets get/list` unless there is a strong reason.

## ServiceAccount Vs Service

These names are similar but unrelated.

```text
ServiceAccount
  -> identity and permissions

Service
  -> stable network endpoint
```

Flow:

```text
Deployment creates Pod
  -> pod runs as ServiceAccount task-api-workload
  -> pod has label app=search-service

Service search-service
  -> selector app=search-service
  -> sends traffic to matching Pods
```

The ServiceAccount does not point to a Service.
The Deployment points the Pod to a ServiceAccount.
The Service points traffic to Pods by labels.

## NetworkPolicy

RBAC controls Kubernetes API access.
NetworkPolicy controls pod network traffic.

```text
RBAC:
  Can this identity call Kubernetes API to read Secrets?

NetworkPolicy:
  Can this pod connect to Redis on TCP 6379?
```

### Default Deny

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-app-workloads
  namespace: task-api
spec:
  podSelector:
    matchExpressions:
    - key: app
      operator: In
      values:
      - search-service
      - task-service
  policyTypes:
  - Ingress
  - Egress
```

Meaning:

```text
for selected pods
deny ingress and egress unless another policy allows it
```

### Ingress

Ingress means traffic entering selected pods.

```yaml
spec:
  podSelector:
    matchLabels:
      app: task-service
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: kong-gateway
    ports:
    - protocol: TCP
      port: 8000
```

Meaning:

```text
selected destination pods:
  app=task-service

allowed source:
  app=kong-gateway

allowed port:
  TCP 8000
```

Flow:

```text
kong-gateway -> task-service:8000 allowed
other pod    -> task-service:8000 denied
```

### Egress

Egress means traffic leaving selected pods.

```yaml
spec:
  podSelector:
    matchLabels:
      app: search-service
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          elasticsearch.k8s.elastic.co/cluster-name: elasticsearch
    ports:
    - protocol: TCP
      port: 9200
```

Meaning:

```text
search-service pods may connect to Elasticsearch pods on TCP 9200
```

### namespaceSelector

```yaml
- to:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: kube-system
```

Meaning:

```text
allow traffic to a namespace whose name label is kube-system
```

Common use:

```text
allow DNS to CoreDNS in kube-system
```

DNS policy example:

```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: kube-system
  ports:
  - protocol: UDP
    port: 53
  - protocol: TCP
    port: 53
```

Without DNS egress, pods may fail to resolve service names.

### podSelector With Operator Labels

```yaml
podSelector:
  matchLabels:
    cnpg.io/poolerName: task-db-pooler-rw
```

Meaning:

```text
select CloudNativePG PgBouncer pooler pods
```

Operators often add their own labels.
Use `kubectl get pod --show-labels` to discover them.

### ipBlock

```yaml
ingress:
- from:
  - ipBlock:
      cidr: 0.0.0.0/0
```

Meaning:

```text
allow traffic from any IPv4 address
```

This is broad. Use carefully.

Good local use:

```text
port-forward / local lab access
```

Production direction:

```text
allow ingress controller
allow load balancer CIDR
allow office/VPN CIDR
avoid 0.0.0.0/0 unless it is truly public
```

### NetworkPolicy Step By Step

When you write NetworkPolicy:

```text
1. Pick the destination pods to protect.
   spec.podSelector

2. Decide direction.
   Ingress, Egress, or both

3. Add DNS egress if pods need service names.

4. Add application ingress.
   Example: Kong -> services

5. Add dependency egress.
   Example: services -> PostgreSQL/Redis/Kafka/Elasticsearch

6. Add dependency ingress if destination is also isolated.
   Example: PostgreSQL allows app pods

7. Test from allowed pod.

8. Test from denied pod.
```

Debug commands:

```bash
kubectl get networkpolicy -n task-api
kubectl describe networkpolicy allow-search-and-logs-to-elasticsearch -n task-api
kubectl get pod -n task-api --show-labels
kubectl exec -n task-api deploy/search-service -- nslookup elasticsearch-es-http
kubectl exec -n task-api deploy/search-service -- curl -s http://elasticsearch-es-http:9200
```

Important:

```text
NetworkPolicy needs CNI support.
Calico and Cilium enforce it well.
Some local clusters may show NetworkPolicy objects but not enforce them.
```

## Pod Security Namespace Labels

```yaml
labels:
  pod-security.kubernetes.io/audit: baseline
  pod-security.kubernetes.io/audit-version: latest
  pod-security.kubernetes.io/warn: baseline
  pod-security.kubernetes.io/warn-version: latest
```

Meaning:

```text
warn/audit when pods violate baseline Pod Security
do not block yet
```

Modes:

```text
warn    -> show warning to user
audit   -> write audit event
enforce -> block violating pods
```

Levels:

```text
privileged -> weak
baseline   -> reasonable default
restricted -> strongest common profile
```

Production flow:

```text
warn/audit baseline
  -> fix workloads
  -> enforce baseline
  -> test restricted where possible
```

## Affinity, Anti-Affinity, Hard And Soft

This is probably what interviewers mean by hard vs soft scheduling.

Hard rule:

```yaml
requiredDuringSchedulingIgnoredDuringExecution
```

Meaning:

```text
Kubernetes must obey this.
If no matching node exists, pod stays Pending.
```

Soft rule:

```yaml
preferredDuringSchedulingIgnoredDuringExecution
```

Meaning:

```text
Kubernetes tries to obey this.
If not possible, pod can still run somewhere else.
```

Example use:

```text
hard:
  database must run on nodes with fast disk

soft:
  try to spread API pods across different nodes
```

Production interview answer:

```text
Hard rules give strict placement but can reduce availability when capacity is missing.
Soft rules guide placement while keeping workloads schedulable.
For high traffic apps, use topology spread constraints or soft pod anti-affinity to spread replicas across nodes/zones.
Use hard rules only for real requirements like GPU, disk type, compliance, or dedicated nodes.
```

## Topology Spread

For high traffic services, do not put all replicas on one node.

Common production idea:

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: kubernetes.io/hostname
  whenUnsatisfiable: ScheduleAnyway
  labelSelector:
    matchLabels:
      app: task-service
```

Meaning:

```text
spread task-service pods across nodes
try to keep pod count balanced
if perfect spread is impossible, still schedule
```

`ScheduleAnyway` is soft.
`DoNotSchedule` is hard.

## Quick Reading Checklist

When you open a manifest, read in this order:

```text
1. apiVersion/kind
   What object is this?

2. metadata.name/namespace
   Where does it live?

3. labels
   How will other objects select it?

4. spec.selector / podSelector
   Which pods are targeted?

5. serviceAccountName
   Which identity will pods use?

6. env / secrets
   Where does config come from?

7. probes
   How does Kubernetes know healthy/ready?

8. resources
   What CPU/memory behavior is expected?

9. volumes / PVC
   Is data persistent?

10. ingress/egress/RBAC
   Who can access it?
```

## Common Debug Commands

```bash
kubectl explain deployment.spec.template.spec.containers
kubectl explain networkpolicy.spec.ingress
kubectl explain role.rules

kubectl get pod -n task-api --show-labels
kubectl describe pod <pod> -n task-api
kubectl describe service search-service -n task-api
kubectl get endpoints search-service -n task-api

kubectl auth can-i get pods \
  --as=developer@example.com \
  --as-group=platform-developers \
  -n task-api

kubectl get networkpolicy -n task-api
kubectl describe networkpolicy <name> -n task-api
```

## One-Line Mental Model

```text
apiVersion/kind says what object this is.
metadata names and labels it.
spec says desired behavior.
selectors connect objects to pods.
ServiceAccount/RBAC controls API identity and permissions.
NetworkPolicy controls pod traffic.
Probes control health and traffic readiness.
Resources and scheduling control where and how pods run.
```
