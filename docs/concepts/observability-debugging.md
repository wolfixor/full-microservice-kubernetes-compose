# Observability Debugging

## Problem We Saw

`search-service` was running, but it was not healthy.

```text
Redis health check failed
Kafka consumer had no active members
search-service consumer lag increased
```

The dangerous part was this:

```text
/ready returned 200
even while Redis was unhealthy
```

So Kubernetes still believed the pod was ready.

## Better Detection Flow

```text
application exposes health metrics
  -> Prometheus scrapes /metrics
  -> PrometheusRule checks bad states
  -> alert fires before we manually read logs
```

For this project:

```text
search_service_redis_healthy
search_service_kafka_consumer_active
search_service_kafka_events_failed_total
```

## Readiness Rule

`/health` means:

```text
process is alive
```

`/ready` means:

```text
service can receive traffic
critical dependencies are ready
```

For `search-service`, readiness checks:

```text
Redis healthy
Kafka consumer active
```

If one is broken, `/ready` returns `503`.

## Alert Rules

```text
SearchServiceRedisUnhealthy
SearchServiceKafkaConsumerDown
SearchServiceKafkaEventProcessingFailures
```

Apply:

```bash
kubectl apply -f k8s/monitoring/prometheus-rules.yaml
kubectl apply -f k8s/monitoring/prometheus-managed.yaml
```

Check:

```bash
kubectl get prometheusrule -n monitoring
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Then open:

```text
http://localhost:9090/alerts
```

## Senior DevOps Tools

Common tools for managing and debugging clusters:

```text
k9s / Lens              -> cluster navigation
stern                   -> multi-pod logs
Prometheus + Grafana    -> metrics and dashboards
Alertmanager            -> alert routing
ELK or Loki             -> centralized logs
Argo CD                 -> GitOps reconciliation
Argo Rollouts           -> progressive delivery
Velero                  -> backup and restore
Trivy                   -> image and manifest scanning
Kyverno or OPA Gatekeeper -> policy enforcement
```

Image tags and rollback strategy should be handled during the CI/CD step.

