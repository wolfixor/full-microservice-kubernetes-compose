
# Prometheus Stack

## Mental Model

Prometheus is operator-managed in Kubernetes.

```text
Prometheus Operator
  -> watches Prometheus custom resource
  -> creates Prometheus StatefulSet
  -> watches ServiceMonitor resources
  -> generates scrape config
```

So we do not manually maintain `prometheus.yml` for Kubernetes scraping anymore.

## Manual vs Operator

Old manual flow:

```text
prometheus-config.yaml
  -> prometheus.yml scrape_configs
  -> Prometheus Deployment
```

New operator flow:

```text
ServiceMonitor
  -> Prometheus Operator
  -> generated scrape config
  -> Prometheus StatefulSet
```

## Exact Installation Flow

### Step 1: Install the Operator

```bash
OPERATOR_VERSION=v0.93.0
TMPDIR=$(mktemp -d)

curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/${OPERATOR_VERSION}/kustomization.yaml" > "${TMPDIR}/kustomization.yaml"
curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/${OPERATOR_VERSION}/bundle.yaml" > "${TMPDIR}/bundle.yaml"

cd "${TMPDIR}"
kustomize edit set namespace monitoring
kubectl apply -k "${TMPDIR}"
```

What this does:

```text
bundle.yaml contains:
  -> CRDs (Prometheus, ServiceMonitor, PodMonitor, AlertmanagerConfig, ...)
  -> Operator Deployment
  -> RBAC (ClusterRole, ClusterRoleBinding, ServiceAccount)

kustomize edit set namespace monitoring
  -> patches all resources to use the monitoring namespace

kubectl apply -k
  -> installs CRDs into the cluster
  -> creates the Prometheus Operator Deployment in monitoring namespace
```

After this step the cluster knows new kinds:

```text
Prometheus
ServiceMonitor
PodMonitor
Alertmanager
PrometheusRule
```

And one new pod is running:

```text
monitoring namespace
  -> prometheus-operator-xxx pod (Deployment)
```

Wait for it:

```bash
kubectl wait pod -n monitoring -l app.kubernetes.io/name=prometheus-operator --for=condition=Ready --timeout=300s
```

### Step 2: Create the Prometheus Instance

```bash
kubectl apply -f k8s/monitoring/prometheus-managed.yaml
```

What this does:

```text
prometheus-managed.yaml contains kind: Prometheus

Prometheus Operator sees this CR
  -> creates a StatefulSet in monitoring namespace
  -> StatefulSet runs the actual Prometheus pod(s)
  -> replica count comes from the CR spec
  -> Prometheus image version comes from the CR spec
```

So you never create the Prometheus StatefulSet manually.
The operator creates it from your CR.

```text
you apply:   kind: Prometheus
operator creates: StatefulSet/prometheus-k8s
                  Pod/prometheus-k8s-0
                  Service/prometheus-operated
```

### Step 3: Apply ServiceMonitors

```bash
kubectl apply -f k8s/monitoring/service-monitors.yaml
```

What this does:

```text
ServiceMonitor tells Prometheus what to scrape

Prometheus Operator watches ServiceMonitor CRs
  -> reads the selector and endpoints
  -> generates scrape_configs inside Prometheus
  -> Prometheus starts scraping those targets
```

You never edit `prometheus.yml` directly.
Adding a ServiceMonitor is enough.

### Step 4: Apply Everything Else

```bash
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml
kubectl apply -f k8s/monitoring/postgres-exporter.yaml
kubectl apply -f k8s/monitoring/redis-exporter.yaml
kubectl apply -f k8s/monitoring/elasticsearch-exporter.yaml
kubectl apply -f k8s/monitoring/node-exporter.yaml
kubectl apply -f k8s/monitoring/kube-state-metrics.yaml
kubectl apply -f k8s/monitoring/prometheus-rules.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

## Full Flow Summary

```text
Step 1: kubectl apply bundle.yaml
  -> CRDs installed (cluster learns new kinds)
  -> Prometheus Operator Deployment created

Step 2: kubectl apply prometheus-managed.yaml
  -> kind: Prometheus CR created
  -> Operator sees it
  -> Operator creates StatefulSet + Pod

Step 3: kubectl apply service-monitors.yaml
  -> kind: ServiceMonitor CRs created
  -> Operator sees them
  -> Operator generates scrape config inside Prometheus
  -> Prometheus scrapes targets

Step 4: apply exporters, rules, grafana
  -> exporters expose metrics for databases and infra
  -> ServiceMonitors point Prometheus at exporters
  -> Grafana reads from Prometheus
```

## Main Components

```text
Prometheus Operator    -> manages Prometheus lifecycle
Prometheus             -> stores and queries metrics
ServiceMonitor         -> tells Prometheus what to scrape
PrometheusRule         -> defines alert rules
Grafana                -> dashboards
Exporters              -> expose database/cache/search metrics
```

## What Gets Monitored

| Component | What it Monitors | Main Question |
| --- | --- | --- |
| API Server | Kubernetes Control Plane | Is Kubernetes itself healthy? |
| Kubelet | Node Agent | Is the node agent working correctly? |
| cAdvisor | Containers | Which container is using CPU/RAM/Disk/Network? |
| Node Exporter | Linux Host | Is the server healthy? |
| kube-state-metrics | Kubernetes Objects | What does Kubernetes think exists? |
| Application Exporters | PostgreSQL, Redis, Elasticsearch | Is my application/database healthy? |
| Kong Gateway | API Gateway | How is client traffic flowing? |

## Important Files

```text
k8s/monitoring/prometheus-managed.yaml   -> kind: Prometheus CR
k8s/monitoring/service-monitors.yaml     -> kind: ServiceMonitor CRs
k8s/monitoring/prometheus-rules.yaml     -> kind: PrometheusRule CRs
k8s/monitoring/prometheus-rbac.yaml      -> RBAC so Prometheus can read pods/services
```
