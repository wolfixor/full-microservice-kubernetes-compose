# Production Monitoring Checklist

## Mental Model

Do not monitor everything.

Monitor what answers these questions:

```text
Is the user impacted?
Is data at risk?
Is money at risk?
Is security at risk?
Does a human need to act?
```

Good monitoring is:

```text
metrics for fast detection
logs for investigation
traces for request flow
alerts for human action
runbooks for response
```

## Golden Signals

Every service should have:

```text
traffic     -> request rate
errors      -> 5xx, failed jobs, failed events
latency     -> p95 / p99 response time
saturation  -> CPU, memory, queue lag, connection pool usage
```

Good alerts:

```text
error rate high for 5 minutes
p95 latency high for 5 minutes
service has traffic but zero successful responses
```

Avoid noisy alerts:

```text
CPU high for 10 seconds
one request failed
one pod restarted once
```

## Kubernetes

Watch:

```text
pod not ready
CrashLoopBackOff
restart count increasing
deployment unavailable
node disk pressure
node memory pressure
PVC almost full
```

Tools:

```text
Prometheus
kube-state-metrics
node-exporter
cAdvisor
Grafana
```

## Databases

Watch:

```text
database down
connection pool exhausted
slow queries
replication lag
disk usage
backup success/failure
restore test status
```

For PostgreSQL:

```text
primary healthy
replicas healthy
replication lag low
PgBouncer pool not exhausted
```

## Redis

Watch:

```text
cluster state
memory usage
evictions
command errors
cache hit ratio
master/replica health
```

Alert when:

```text
Redis Cluster is not OK
memory close to max
replica missing
evictions rising unexpectedly
```

## Kafka

Watch:

```text
broker count
under-replicated partitions
offline partitions
consumer lag
consumer group active members
failed event processing
DLQ growth
```

Alert when:

```text
consumer lag grows for 5 minutes
consumer group has no active members
under-replicated partitions > 0
DLQ messages increase
```

## Logs

Use logs for investigation, not every alert.

Good log searches:

```text
level: ERROR
service: search-service and message: *Kafka consumer crashed*
service: task-service and message: *database*
message: *permission denied*
```

Tools:

```text
ELK
Loki
Fluent Bit
Kibana
Grafana Explore
```

## Security

Security monitoring is different from app monitoring.

Watch:

```text
unknown SSH login
many failed login attempts
new admin user created
forbidden API access spike
container starts a shell unexpectedly
pod reads sensitive host paths
image with critical CVE deployed
```

Tools:

```text
Falco              -> runtime security
Wazuh / SIEM       -> host and security logs
Trivy              -> image and manifest scanning
Kyverno / OPA      -> policy enforcement
audit logs         -> Kubernetes API activity
```

## Business Signals

Each product has its own important actions.

Examples:

```text
login failure rate
payment failure rate
order creation failure rate
task creation failure rate
notification delivery failure rate
search indexing lag
```

Business alerts should be based on user impact, not only infrastructure.

## Alert Quality Rule

Before adding an alert, answer:

```text
What broke?
Who owns it?
How urgent is it?
What command checks it?
What command fixes or mitigates it?
Where is the runbook?
```

If there is no action, make a dashboard panel instead of an alert.

## Senior DevOps Toolkit

```text
k9s / Lens              -> cluster navigation
stern                   -> multi-pod logs
Prometheus              -> metrics
Grafana                 -> dashboards
Alertmanager            -> alert routing
ELK / Loki              -> logs
OpenTelemetry           -> traces
Tempo / Jaeger          -> trace storage
Argo CD                 -> GitOps
Argo Rollouts           -> progressive delivery
Velero                  -> backup and restore
Trivy                   -> security scanning
Falco                   -> runtime security
Kyverno / OPA Gatekeeper -> policy
```

## Project Checklist

For every production project, start with:

```text
service golden signals
pod health and restarts
database health and backups
cache health
queue/event lag
centralized logs
security events
business failure signals
runbooks for important alerts
```

