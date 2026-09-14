# CRD Map

CRD means Kubernetes learned a new object type.
An operator usually watches that object and creates real resources from it.

## Quick Map

| Command | Kind | Owner | Meaning |
| --- | --- | --- | --- |
| `kubectl get rollout -n task-api` | Rollout | Argo Rollouts | progressive deploy instead of normal Deployment |
| `kubectl get analysisrun -n task-api` | AnalysisRun | Argo Rollouts | Prometheus checks during canary |
| `kubectl get analysistemplate -n task-api` | AnalysisTemplate | Argo Rollouts | reusable metric checks |
| `kubectl get kafka -n kafka` | Kafka | Strimzi | Kafka cluster desired state |
| `kubectl get kafkatopic -n kafka` | KafkaTopic | Strimzi | Kafka topic desired state |
| `kubectl get cluster -n task-api` | Cluster | CloudNativePG | Postgres cluster desired state |
| `kubectl get pooler -n task-api` | Pooler | CloudNativePG | PgBouncer pooler desired state |
| `kubectl get backup -n task-api` | Backup | CloudNativePG | Postgres backup job/status |
| `kubectl get externalsecret -n task-api` | ExternalSecret | ESO | sync external secret into Kubernetes Secret |
| `kubectl get secretstore -n task-api` | SecretStore | ESO | connection config to Vault |
| `kubectl get prometheus -n monitoring` | Prometheus | Prometheus Operator | managed Prometheus instance |
| `kubectl get servicemonitor -A` | ServiceMonitor | Prometheus Operator | what Prometheus scrapes |
| `kubectl get elasticsearch -n task-api` | Elasticsearch | ECK | Elasticsearch cluster desired state |
| `kubectl get kibana -n task-api` | Kibana | ECK | Kibana desired state |
| `kubectl get policyreport -A` | PolicyReport | Kyverno | policy audit results |
| `kubectl get vulnerabilityreports -A` | VulnerabilityReport | Trivy Operator | image CVE scan report |

## How To Read Any CRD

```bash
kubectl get <kind> -A
kubectl describe <kind> <name> -n <namespace>
kubectl get <kind> <name> -n <namespace> -o yaml
```

Look for:

```text
spec
  -> what we asked for

status
  -> what the operator actually did

conditions
  -> Ready/Healthy/Error reason

events
  -> recent warnings and failures
```

## Debug Order

```text
1. CR object
2. CR status/conditions
3. operator logs
4. generated Kubernetes objects
5. pod logs/events
```

Example:

```text
ExternalSecret failed
  -> describe ExternalSecret
  -> check SecretStore
  -> check ESO logs
  -> check Vault path/policy
  -> check generated Kubernetes Secret
```

