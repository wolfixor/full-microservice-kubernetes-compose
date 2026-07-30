
# Prometheus Stack

## Mental Model

Prometheus is now operator-managed in Kubernetes.

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

## Main Components

```text
Prometheus Operator    -> manages Prometheus
Prometheus             -> stores and queries metrics
ServiceMonitor         -> tells Prometheus what to scrape
Grafana                -> dashboards
Exporters              -> expose database/cache/search metrics
```

The platform Prometheus CR pins Prometheus to:

```text
v3.13.1
```

Do not override the Prometheus image with an older manual image. The operator-generated config must match the Prometheus runtime version.

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

## Apply Flow

```bash
kubectl apply -f k8s/monitoring/namespace.yaml
```

Install pinned Prometheus Operator `v0.93.0`:

```bash
OPERATOR_VERSION=v0.93.0
TMPDIR=$(mktemp -d)

curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/${OPERATOR_VERSION}/kustomization.yaml" > "${TMPDIR}/kustomization.yaml"
curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/${OPERATOR_VERSION}/bundle.yaml" > "${TMPDIR}/bundle.yaml"

cd "${TMPDIR}"
kustomize edit set namespace monitoring
kubectl apply -k "${TMPDIR}"

kubectl wait pod -n monitoring -l app.kubernetes.io/name=prometheus-operator --for=condition=Ready --timeout=300s
```

Then apply platform monitoring:

```bash
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml
kubectl apply -f k8s/monitoring/postgres-exporter.yaml
kubectl apply -f k8s/monitoring/redis-exporter.yaml
kubectl apply -f k8s/monitoring/elasticsearch-exporter.yaml
kubectl apply -f k8s/monitoring/node-exporter.yaml
kubectl apply -f k8s/monitoring/kube-state-metrics.yaml
kubectl apply -f k8s/monitoring/service-monitors.yaml
kubectl apply -f k8s/monitoring/prometheus-managed.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

## Important Files

```text
k8s/monitoring/prometheus-operator-install.md
k8s/monitoring/prometheus-managed.yaml
k8s/monitoring/service-monitors.yaml
```

```
Memory Map
                Kubernetes Cluster
                       │
        ┌──────────────┴──────────────┐
        │                             │
   API Server                    kube-state-metrics
   (K8s Brain)                    (K8s Objects)

                       │
                  Worker Node
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Kubelet         cAdvisor     Node Exporter
   (Agent)       (Containers)   (Linux Host)

                       │
              Running Applications
        ┌──────────────┼──────────────┐
        │              │              │
   Postgres       Redis        Elasticsearch
      │              │              │
 Postgres Exp.   Redis Exp.   Elasticsearch Exp.
      │              │              │
      └──────────────┼──────────────┘
                     │
               Application Metrics

                       │
                 Kong Gateway
                 (Client Traffic)
```

### One-line cheat sheet:
```
API Server → Kubernetes Brain
Kubelet → Node Agent
cAdvisor → Containers
Node Exporter → Linux Host
kube-state-metrics → Kubernetes Objects
Application Exporters → Application Internals (DB stats, cache hits, JVM metrics, etc.)
Kong → Traffic
```
