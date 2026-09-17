# Prometheus Stack

`kube-prometheus-stack` is installed by Helmfile and owns the shared monitoring
runtime:

```text
Helmfile
  -> Prometheus Operator and CRDs
  -> Prometheus
  -> Alertmanager
  -> Grafana
  -> kube-state-metrics
  -> node-exporter

Argo CD
  -> ServiceMonitors for platform services
  -> PrometheusRules
  -> Grafana dashboard ConfigMaps
  -> Redis, PostgreSQL, and Elasticsearch exporters
```

Do not deploy a second manual Prometheus, Grafana, Alertmanager,
kube-state-metrics, or node-exporter beside the Helm release.

The Operator watches `ServiceMonitor` and `PrometheusRule` custom resources and
generates Prometheus scrape and alert configuration. Grafana discovers dashboard
ConfigMaps labeled `grafana_dashboard: "1"`.

Environment sizing is in `k8s/operators/environments/`. The local environment
may use cached image versions when public registries are unavailable; staging
and production keep current pinned versions.
