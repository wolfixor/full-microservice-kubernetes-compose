# Network Policy And CNI

## What This Adds

RBAC controls who can use the Kubernetes API.
NetworkPolicy controls which pods can talk to which other pods.
Pod Security Standards check whether pods are allowed to run with risky settings.

## Flow

```text
request
  -> Kong
  -> service pod
  -> dependency: PostgreSQL / Redis / Kafka / Elasticsearch
```

With NetworkPolicy:

```text
pod tries network connection
  -> Kubernetes has NetworkPolicy objects
  -> CNI plugin enforces the allow/deny decision
```

## Traffic Matrix

| Source | Destination | Port | Why |
| --- | --- | --- | --- |
| Internet / port-forward | Kong | 8000 | API traffic |
| Kong | app services | 8000 | Route requests |
| apps | PostgreSQL / PgBouncer | 5432 | database |
| apps | Redis Cluster | 6379 | cache |
| apps | Kafka | 9092 | events |
| search / fluentbit / kibana | Elasticsearch | 9200 | search and logs |
| Prometheus | services | 8000 / 8001 / 2020 | metrics |
| pods | CoreDNS | 53 | service name lookup |

## Important Concepts

- `ingress`: traffic entering a selected pod.
- `egress`: traffic leaving a selected pod.
- `default deny`: after a pod is selected by a deny policy, only explicit allow rules work.
- An allow policy also isolates selected pods for that direction.
- `CNI`: the cluster networking plugin. It gives pods networking and may enforce NetworkPolicy.
- `Calico/Cilium`: production-grade CNIs that enforce NetworkPolicy well.
- `Docker Desktop/kind`: good for learning, but NetworkPolicy enforcement depends on the installed CNI.

## NetworkPolicy Vs Kyverno

NetworkPolicy controls runtime network traffic.

Kyverno controls Kubernetes object admission, for example:

```text
do not allow privileged pods
require resource limits
require approved image registry
```

Think of it like this:

```text
NetworkPolicy asks:
  "This pod is already running. Can it connect to that other pod/IP/port?"

Kyverno asks:
  "Should Kubernetes accept this YAML before the pod is created?"
```

Real example:

```text
Fluent Bit pod -> Elasticsearch:9200
```

NetworkPolicy controls whether that network connection is allowed:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-search-and-logs-to-elasticsearch
  namespace: task-api
spec:
  podSelector:
    matchExpressions:
    - key: app
      operator: In
      values:
      - fluentbit
      - kibana
      - search-service
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

That policy says:

```text
pods with app=fluentbit/kibana/search-service
  -> may connect to Elasticsearch pods
  -> only on TCP 9200
```

Kyverno would not control that connection.

Kyverno controls whether a manifest is accepted. Example policy idea:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
spec:
  validationFailureAction: Audit
  rules:
  - name: require-requests-limits
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must define CPU and memory requests/limits."
      pattern:
        spec:
          containers:
          - resources:
              requests:
                cpu: "?*"
                memory: "?*"
              limits:
                cpu: "?*"
                memory: "?*"
```

That policy says:

```text
when someone applies a Pod
  -> check the YAML
  -> warn/audit if resources are missing
```

Kyverno can block bad YAML before it runs.
NetworkPolicy can block bad traffic after pods run.

## Pod Security Standards

Use audit/warn first:

```text
audit/warn
  -> tell me what would be blocked
enforce
  -> actually block bad pods
```

Production usually starts with audit/warn, fixes workloads, then moves to enforce.

## Production Notes

- Use Calico or Cilium on real clusters.
- Keep policies in GitOps.
- Apply default deny only after allow rules and tests are ready.
- Do not guess production traffic. Build a traffic matrix from real logs, metrics, and service maps.
