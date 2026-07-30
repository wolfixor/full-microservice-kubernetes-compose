# Operator and CRD

## Manual Way

Kubernetes already knows normal resources:

```text
Deployment
Service
ConfigMap
Secret
PVC
StatefulSet
```

Before, Prometheus was manual:

```text
prometheus-config.yaml
  -> ConfigMap with prometheus.yml

prometheus-deployment.yaml
  -> Deployment running Prometheus
```

So we had to write scrape config ourselves.

```text
you write prometheus.yml
  -> Prometheus reads it
  -> Prometheus scrapes targets
```

## CRD

`CRD` means Custom Resource Definition.

It teaches Kubernetes a new resource type.

After installing Prometheus Operator CRDs, Kubernetes understands:

```text
Prometheus
ServiceMonitor
PodMonitor
PrometheusRule
Alertmanager
```

So this becomes valid:

```bash
kubectl get prometheus -n monitoring
kubectl get servicemonitor -n monitoring
```

## Operator

An operator is a controller running inside Kubernetes.

It watches custom resources and creates the real Kubernetes objects.

Normal Kubernetes controller:

```text
Deployment
  -> ReplicaSet
  -> Pods
```

Prometheus Operator:

```text
Prometheus CR
  -> StatefulSet
  -> Prometheus pod
  -> generated config
```

## Current Prometheus Flow

```text
Prometheus Operator
  -> watches Prometheus CR
  -> watches ServiceMonitor CRs
  -> generates scrape config
  -> creates Prometheus StatefulSet
```

`Prometheus` CR says how Prometheus should run:

```text
replicas
storage
retention
version
ServiceMonitor selector
```

`ServiceMonitor` CR says what Prometheus should scrape:

```text
which Service labels
which port
which path
which namespace
```

## Old vs New

Old manual way:

```text
you write prometheus.yml
you write Prometheus Deployment
```

New operator way:

```text
you write Prometheus CR
you write ServiceMonitor CRs
operator creates StatefulSet and config
```

## Source of Truth

Manual way:

```text
prometheus.yml is source of truth
```

Operator way:

```text
Prometheus CR + ServiceMonitor CRs are source of truth
```

So when we add a new service later:

```text
add /metrics endpoint
add Kubernetes Service
add ServiceMonitor
operator updates Prometheus config
```

No manual `prometheus.yml`.

