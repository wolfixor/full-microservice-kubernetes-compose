# CloudNativePG Flow

## Mental Model

CloudNativePG is the PostgreSQL operator.

```text
CloudNativePG Operator
  -> watches Cluster CR
  -> creates PostgreSQL pods, PVCs, services, replication
  -> handles failover
```

So we do not manually create the task PostgreSQL `StatefulSet` anymore.

## Old Manual Way

```text
task-service/k8s/postgres-statefulset-manual.yaml
  -> StatefulSet/task-service-db
  -> one PostgreSQL pod
  -> one PVC
```

This is good for learning, but it is not a production database pattern.

## New Operator Way

```text
task-service/k8s/postgres-cnpg.yaml
  -> Cluster/task-db
  -> 3 PostgreSQL pods
  -> primary plus replicas
  -> automatic failover
```

The task service connects through PgBouncer:

```text
task-service
  -> task-db-pooler-rw
  -> task-db primary
```

Migration jobs should connect to the direct write service:

```text
task-service-migrations
  -> task-db-rw
  -> task-db primary
```

## Why PgBouncer

Apps can open many database connections.

PgBouncer keeps a smaller stable connection pool to PostgreSQL, so the database is protected from too many direct app connections.

## Apply Flow

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.0.yaml
kubectl wait deployment/cnpg-controller-manager -n cnpg-system --for=condition=Available --timeout=300s

kubectl apply -f task-service/k8s/postgres-cnpg.yaml
kubectl wait cluster/task-db -n task-api --for=condition=Ready --timeout=600s
kubectl apply -f task-service/k8s/pooler.yaml
```

## Check

```bash
kubectl get cluster -n task-api
kubectl get pooler -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | grep task-db
```

## Current Scope

For now, only `task-service` uses CloudNativePG.

The other services still use the manual PostgreSQL StatefulSet pattern until we convert them one by one.

## Data Migration Note

This creates a new PostgreSQL cluster.

If the old `task-service-db` StatefulSet already has important data, export and restore it before switching production traffic:

```text
old task-service-db
  -> pg_dump
  -> restore into task-db
  -> run migrations
  -> deploy task-service
```
