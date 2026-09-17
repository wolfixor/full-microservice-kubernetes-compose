# CloudNativePG Install

CloudNativePG is the PostgreSQL operator.

It watches PostgreSQL custom resources and creates the real database pods, services, PVCs, replication, failover, and backups.

## Install Operator

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.0.yaml
kubectl wait deployment/cnpg-controller-manager -n cnpg-system --for=condition=Available --timeout=300s
```

## Apply Task Database

```bash
kubectl apply -f k8s/platform/data/task-db/base/cluster.yaml
kubectl wait cluster/task-db -n task-api --for=condition=Ready --timeout=600s

kubectl apply -f k8s/platform/data/task-db/base/pooler.yaml
```

## Apply Backup Setup

This uses the local MinIO from the Velero step as S3-compatible storage.

```bash
kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/minio-create-cnpg-bucket.yaml
kubectl wait --for=condition=complete job/minio-create-cnpg-bucket -n velero --timeout=300s

kubectl apply -f k8s/platform/data/task-db/base/cluster.yaml
kubectl apply -f k8s/apps/task-service/operations/postgres-backup.yaml
```

## Check

```bash
kubectl get cluster -n task-api
kubectl get pooler -n task-api
kubectl get backup -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | grep task-db
```

## Important

Do not run the old `k8s/examples/task-service/postgres-statefulset.yaml` and the new `k8s/platform/data/task-db/base/cluster.yaml` for the same service at the same time.

Use one database path:

```text
manual StatefulSet
or
CloudNativePG Cluster
```

If `task-service-db` already contains important data, dump and restore that data into `task-db` before deploying the app against the new pooler service.
