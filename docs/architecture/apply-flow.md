# Apply Flow

This doc explains what reacts after `kubectl apply`.

## Mental Model

```text
kubectl apply
  -> API Server stores object
  -> admission controllers check it
  -> controllers/operators reconcile it
  -> lower-level objects are created/updated
  -> kubelet runs pods on nodes
```

## Admission Step

```text
manifest reaches API Server
  -> Kyverno checks policy
  -> audit mode: warning/event/report
  -> enforce mode: reject bad manifest
```

Debug:

```bash
kubectl get events -n task-api --sort-by=.lastTimestamp
kubectl get policyreport -A
kubectl get clusterpolicy
```

## Task Service Rollout

```text
kubectl apply -f task-service/k8s/rollout.yaml
  -> API Server stores Rollout
  -> Kyverno audits manifest
  -> Argo Rollouts sees Rollout changed
  -> Argo creates new ReplicaSet
  -> new pods start
  -> readiness/liveness probes run
  -> Argo creates AnalysisRun
  -> AnalysisRun queries Prometheus
  -> if metrics pass: increase canary
  -> if metrics fail: pause/rollback
```

Debug:

```bash
kubectl get rollout task-service -n task-api
kubectl describe rollout task-service -n task-api
kubectl get analysisrun -n task-api
kubectl describe analysisrun <name> -n task-api
kubectl get pods -n task-api -l app=task-service
kubectl logs -n task-api -l app=task-service --tail=120
```

## Vault Secret Sync

```text
kubectl apply -f k8s/external-secrets/task-service-secrets.yaml
  -> API Server stores ExternalSecret
  -> ESO controller sees ExternalSecret
  -> ESO logs into Vault using SecretStore
  -> ESO reads Vault secret
  -> ESO creates/updates Kubernetes Secret
  -> app pod reads Kubernetes Secret as env vars
```

Debug:

```bash
kubectl get secretstore,externalsecret -n task-api
kubectl describe externalsecret task-service-db -n task-api
kubectl describe externalsecret task-service-redis -n task-api
kubectl get secret task-service-db-from-vault task-service-redis-from-vault -n task-api
kubectl logs -n external-secrets deploy/external-secrets --tail=120
```

## PostgreSQL CNPG

```text
kubectl apply -f task-service/k8s/postgres-cnpg.yaml
  -> API Server stores Cluster
  -> CNPG operator sees Cluster
  -> CNPG creates Postgres pods
  -> CNPG creates services:
       task-db-rw
       task-db-ro
       task-db-r
  -> Pooler creates PgBouncer pods/service
```

Debug:

```bash
kubectl get cluster,pooler -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | grep task-db
kubectl describe cluster task-db -n task-api
```

## Kafka Strimzi

```text
kubectl apply -f k8s/kafka/kafka-cluster.yaml
  -> API Server stores Kafka CR
  -> Strimzi operator creates brokers/controllers
  -> Entity Operator manages KafkaTopic CRs

kubectl apply -f k8s/kafka/topics.yaml
  -> KafkaTopic CRs created
  -> Strimzi creates topics inside Kafka
```

Debug:

```bash
kubectl get kafka,kafkatopic -n kafka
kubectl get pods -n kafka
kubectl describe kafka platform-kafka -n kafka
kubectl describe kafkatopic task.created -n kafka
```

## NetworkPolicy

```text
kubectl apply -f k8s/network-policies/
  -> API Server stores policies
  -> CNI enforces allowed traffic
```

Important:

```text
NetworkPolicy selectors must match real pod labels.
If labels are wrong, traffic is blocked even when services/endpoints exist.
```

Debug:

```bash
kubectl get networkpolicy -n task-api
kubectl get pods -n task-api --show-labels
kubectl run netpol-db-test -n task-api --rm -i --restart=Never \
  --image=busybox:1.36 \
  --labels=app=task-service \
  --command -- sh -c "nc -zvw 5 task-db-pooler-rw 5432"
```

