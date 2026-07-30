# Prometheus Operator Install

Production rule: pin the operator version. Do not install from `master` or `latest`.

Install the Prometheus Operator first. It creates the CRDs for:

```text
Prometheus
ServiceMonitor
PodMonitor
PrometheusRule
Alertmanager
```

```bash
OPERATOR_VERSION=v0.93.0
TMPDIR=$(mktemp -d)

curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/v0.93.0/kustomization.yaml" > ./kustomization.yaml"
curl -sL "https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/refs/tags/v0.93.0/bundle.yaml" > ./bundle.yaml

cd "${TMPDIR}"
kustomize edit set namespace monitoring
kubectl apply -k "${TMPDIR}"

kubectl wait pod -n monitoring -l app.kubernetes.io/name=prometheus-operator --for=condition=Ready --timeout=300s
```

After this, apply the platform monitoring resources from `k8s/monitoring/`.
