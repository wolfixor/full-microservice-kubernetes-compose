# Alertmanager Commands

## Apply

Check CRDs first:

```bash
kubectl api-resources | grep -E "prometheuses|alertmanagers|prometheusrules"
```

If `prometheuses` or `alertmanagers` is missing, reinstall the Prometheus Operator CRDs first:

```bash
kubectl apply -f k8s/operators/raw/prometheus-operator/bundle.yaml
kubectl rollout status deployment/prometheus-operator -n monitoring --timeout=300s
```

Then apply:

```bash
kubectl apply -f k8s/platform/observability/base/alertmanager.yaml
kubectl apply -f k8s/platform/observability/base/prometheus-managed.yaml
kubectl apply -f k8s/platform/observability/base/platform-alert-rules.yaml
kubectl apply -f k8s/platform/observability/base/prometheus-rules.yaml
```

## Check

```bash
kubectl get alertmanager,prometheusrule -n monitoring
kubectl get pods -n monitoring | grep -E "alertmanager|prometheus"
kubectl describe prometheus platform-prometheus -n monitoring
```

Port-forward UIs:

```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
```

Open:

```text
http://localhost:9090/alerts
http://localhost:9093
```

## Runbook Format

```text
alert
  -> what it means
  -> query
  -> first command
  -> recovery action
```

## ServiceTargetDown

Meaning: Prometheus cannot scrape a target.

Query:

```promql
up{namespace=~"task-api|monitoring"} == 0
```

First command:

```bash
kubectl get pods,svc,endpoints -A | grep <service>
```

Recovery:

```bash
kubectl describe pod -n <namespace> <pod>
kubectl logs -n <namespace> <pod> --tail=120
```

## KubernetesDeploymentReplicasUnavailable

Meaning: Deployment has fewer ready pods than desired.

Query:

```promql
kube_deployment_status_replicas_available{namespace="task-api"} < kube_deployment_spec_replicas{namespace="task-api"}
```

First command:

```bash
kubectl get deploy,pods -n task-api
```

Recovery:

```bash
kubectl describe deploy -n task-api <deployment>
kubectl describe pod -n task-api <pod>
```

## KubernetesStatefulSetReplicasUnavailable

Meaning: StatefulSet has fewer ready pods than desired.

Query:

```promql
kube_statefulset_status_replicas_ready{namespace="task-api"} < kube_statefulset_replicas{namespace="task-api"}
```

First command:

```bash
kubectl get statefulset,pods,pvc -n task-api
```

Recovery:

```bash
kubectl describe statefulset -n task-api <statefulset>
kubectl describe pvc -n task-api <pvc>
```

## PersistentVolumeClaimPending

Meaning: a PVC cannot bind to storage.

Query:

```promql
kube_persistentvolumeclaim_status_phase{namespace="task-api",phase="Pending"} == 1
```

First command:

```bash
kubectl get pvc -n task-api
kubectl describe pvc -n task-api <pvc>
kubectl get storageclass
```

Recovery:

```bash
kubectl describe storageclass <storageclass>
```

Fix StorageClass, capacity, or volume binding.

## PersistentVolumeClaimPressure

Meaning: a bound PVC is running out of free space.

Query:

```promql
kubelet_volume_stats_available_bytes{namespace="task-api"} / kubelet_volume_stats_capacity_bytes{namespace="task-api"} < 0.15
```

First command:

```bash
kubectl get pvc -n task-api
kubectl describe pvc -n task-api <pvc>
kubectl exec -n task-api <pod> -- df -h
```

Recovery:

```text
delete safe old data, expand the PVC if storage supports it, or move workload data to a larger managed store.
```

Note: this needs kubelet volume metrics. If the query returns no series, add kubelet scraping or a storage exporter before relying on this alert.

## PostgresExporterDown

Meaning: Prometheus cannot scrape PostgreSQL exporter.

Query:

```promql
up{namespace="monitoring",service="postgres-exporter"} == 0
```

First command:

```bash
kubectl get pod -n monitoring -l app=postgres-exporter
kubectl logs -n monitoring -l app=postgres-exporter --tail=120
```

Recovery: fix exporter credentials, service DNS, or database reachability.

## PostgresReplicationLagHigh

Meaning: replica is behind primary.

Query:

```promql
pg_replication_lag_seconds > 30
```

First command:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select application_name,state,sync_state,sent_lsn,replay_lsn,pg_wal_lsn_diff(sent_lsn,replay_lsn) as bytes_lag from pg_stat_replication;"
```

Recovery: check replica CPU/disk/network, WAL retention, and long-running transactions.

## RedisExporterDown

Meaning: Prometheus cannot scrape Redis exporter.

Query:

```promql
up{namespace="monitoring",service="redis-exporter"} == 0
```

First command:

```bash
kubectl get pod -n monitoring -l app=redis-exporter
kubectl logs -n monitoring -l app=redis-exporter --tail=120
```

Recovery: check Redis password, Redis service, and exporter args.

## RedisMemoryPressure

Meaning: Redis memory usage is high.

Query:

```promql
redis_memory_used_bytes / redis_memory_max_bytes > 0.85
```

First command:

```bash
kubectl exec -n task-api redis-cluster-0 -- \
  redis-cli -c -a ${REDIS_PASSWORD} info memory
```

Recovery: inspect key growth, eviction policy, maxmemory, and app cache behavior.

## SearchServiceRedisUnhealthy

Meaning: search-service can run, but its Redis dependency health check is failing.

Query:

```promql
search_service_redis_healthy{service="search-service"} == 0
```

First command:

```bash
kubectl logs -n task-api -l app=search-service --tail=120
kubectl exec -n task-api redis-cluster-0 -- redis-cli -c -a ${REDIS_PASSWORD} ping
```

Recovery: check Redis cluster health, password, DNS/service name, and search-service Redis env vars.

## SearchServiceKafkaConsumerDown

Meaning: search-service is not actively consuming Kafka events, so Elasticsearch indexing may fall behind.

Query:

```promql
search_service_kafka_consumer_active{service="search-service",group_id="search-service"} == 0
```

First command:

```bash
kubectl logs -n task-api -l app=search-service --tail=120
kubectl get pods -n kafka
kubectl get kafkatopic -n kafka
```

Check consumer lag manually:

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --describe --all-groups
```

Recovery: restore Kafka/topics, fix search-service Kafka env vars, then restart search-service if the consumer task is stuck.

## SearchServiceKafkaEventProcessingFailures

Meaning: search-service receives Kafka events but fails while processing or indexing them.

Query:

```promql
increase(search_service_kafka_events_failed_total{service="search-service"}[5m]) > 0
```

First command:

```bash
kubectl logs -n task-api -l app=search-service --tail=160
kubectl get pod -n task-api -l elasticsearch.k8s.elastic.co/cluster-name=elasticsearch
kubectl get svc -n task-api | grep elasticsearch
```

Recovery: fix invalid event payloads, Elasticsearch connectivity, or search-service indexing code. Reprocess from Kafka/DLQ if needed.

## HighHttp5xxRate

Meaning: service is returning too many server errors.

Query:

```promql
sum by (service) (rate(http_requests_total{status=~"5.."}[5m])) > 0.5
```

First command:

```bash
kubectl logs -n task-api -l app=<service> --tail=120
```

Recovery: check recent deploy, dependency errors, and database/cache/Kafka availability.

## HighHttpLatencyP95

Meaning: p95 request latency is above 1 second.

Query:

```promql
histogram_quantile(0.95, sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))) > 1
```

First command:

```bash
kubectl top pods -n task-api
kubectl logs -n task-api -l app=<service> --tail=120
```

Recovery: check slow database queries, pod CPU throttling, dependency latency, and replicas.

## Silence During Planned Work

Open Alertmanager UI:

```text
http://localhost:9093
```

Create silence with:

```text
matcher: service="<service>"
duration: exact maintenance window
comment: planned work ticket or reason
```

Never create open-ended silences.

## Failure Drills

Trigger service down:

```bash
kubectl scale deployment/comment-service -n task-api --replicas=0
```

Recover:

```bash
kubectl scale deployment/comment-service -n task-api --replicas=1
```

Trigger exporter down:

```bash
kubectl scale deployment/redis-exporter -n monitoring --replicas=0
```

Recover:

```bash
kubectl scale deployment/redis-exporter -n monitoring --replicas=1
```

Trigger search-service Kafka consumer alert:

```bash
kubectl scale deployment/search-service -n task-api --replicas=0
```

Recover:

```bash
kubectl scale deployment/search-service -n task-api --replicas=1
```

Trigger PVC pending by applying a broken test PVC:

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: alert-drill-pending-pvc
  namespace: task-api
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: does-not-exist
  resources:
    requests:
      storage: 1Gi
EOF
```

Recover:

```bash
kubectl delete pvc alert-drill-pending-pvc -n task-api
```

## Noisy Alert Review

After a drill or incident, ask:

```text
did it detect real impact?
was severity correct?
was the first command useful?
did it fire too early or too late?
should it page, ticket, or only show on dashboard?
```

## Current Limits

- Kafka consumer lag is checked manually with `kafka-consumer-groups.sh`.
- Production should add a Kafka exporter or Strimzi metrics pipeline before relying on automated Kafka lag alerts.
- Deployment, StatefulSet, and PVC alerts need healthy `kube-state-metrics`.
- PVC pressure also needs kubelet volume metrics.
- Certificate expiry alerting is deferred until cert-manager or a certificate exporter is part of the stack.
