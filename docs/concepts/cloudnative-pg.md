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

## Exact Installation Flow

### Step 1: Install the Operator

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.0.yaml
kubectl wait deployment/cnpg-controller-manager -n cnpg-system --for=condition=Available --timeout=300s
```

What this does:

```text
cnpg-1.30.0.yaml contains:
  -> CRDs (Cluster, Pooler, Backup, ScheduledBackup)
  -> Operator Deployment in cnpg-system namespace
  -> RBAC (ClusterRole, ClusterRoleBinding, ServiceAccount)
```

After this step the cluster knows new kinds:

```text
Cluster
Pooler
Backup
ScheduledBackup
```

And one new pod is running:

```text
cnpg-system namespace
  -> cnpg-controller-manager-xxx pod (Deployment)
```

### Step 2: Create the PostgreSQL Cluster

```bash
kubectl apply -f task-service/k8s/postgres-cnpg.yaml
kubectl wait cluster/task-db -n task-api --for=condition=Ready --timeout=600s
```

What this does:

```text
postgres-cnpg.yaml contains kind: Cluster

CloudNativePG Operator sees this CR
  -> creates PostgreSQL pods (1 primary + 2 replicas)
  -> creates PVCs for each pod
  -> creates services: task-db-rw, task-db-ro, task-db-r
  -> sets up streaming replication between primary and replicas
  -> handles automatic failover if primary fails
```

So you never create PostgreSQL pods manually.
The operator creates them from your CR.

```text
you apply:   kind: Cluster
operator creates: PostgreSQL pods
                  PVCs
                  Services (rw, ro, r)
                  replication setup
```

### Step 3: Create PgBouncer Pooler

```bash
kubectl apply -f task-service/k8s/pooler.yaml
```

What this does:

```text
pooler.yaml contains kind: Pooler

CloudNativePG Operator sees this CR
  -> creates PgBouncer Deployment
  -> creates task-db-pooler-rw Service
  -> PgBouncer sits between app and PostgreSQL
  -> keeps a small stable connection pool to the primary
```

App connects through:

```text
task-service
  -> task-db-pooler-rw (PgBouncer)
  -> task-db-rw (PostgreSQL primary)
```

Migration jobs connect directly:

```text
task-service-migrations
  -> task-db-rw (PostgreSQL primary)
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
