# Velero Review

## Core Idea

Velero backs up and restores Kubernetes objects.

In this project:

```text
Velero -> stores backups in MinIO
MinIO  -> local S3-compatible backup storage
YAML   -> installs Velero, MinIO, BackupStorageLocation, Backup, Schedule, Restore
```

## Flow

```text
Backup CR
  -> Velero reads Kubernetes objects
  -> stores backup data in MinIO

Restore CR
  -> Velero reads backup from MinIO
  -> recreates Kubernetes objects
```

## Commands To Remember

```powershell
kubectl get pods -n velero
kubectl get backupstoragelocation -n velero
kubectl get backups.velero.io -n velero
kubectl get restores.velero.io -n velero
kubectl get schedules.velero.io -n velero
```

Create backup:

```powershell
kubectl apply -f k8s/velero/backups/backup-task-api.yaml
```

Restore test:

```powershell
kubectl apply -f k8s/velero/restores/restore-task-api-example.yaml
kubectl get all -n task-api-restore
```

## Common Failure

Backup exists, but restore was never tested.

That means you do not know if the backup is useful.

Always test restore into a separate namespace.

## Production Difference

Local:

```text
MinIO inside cluster
snapshotVolumes: false
Kubernetes object backup only
```

Production:

```text
real S3 or Ceph RGW outside the workload failure domain
CSI snapshots if storage supports it
database-aware backups for PostgreSQL, Redis, Kafka, Elasticsearch
restore drills with RPO/RTO measurement
```

Important:

```text
Velero is not enough for PostgreSQL data safety.
PostgreSQL needs base backup + WAL archive + PITR.
```

## 5 Questions

1. What does Velero back up in our local setup?
2. What is MinIO doing here?
3. What does BackupStorageLocation tell Velero?
4. Why is Velero not enough for PostgreSQL?
5. Why is restore testing more important than backup creation?

