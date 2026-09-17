# Velero

Velero backs up and restores Kubernetes resources. It can also work with volume snapshots when the cluster storage supports snapshots.

For this local cluster, we use:

```text
Velero + MinIO + YAML
```

## Flow

```text
YAML
  -> creates MinIO
  -> creates Velero server
  -> creates BackupStorageLocation
  -> Backup CR stores Kubernetes objects in MinIO
  -> Restore CR recreates objects from a backup
```

## Local vs Production

Local:

```text
MinIO inside cluster
no volume snapshots
resource backup only
```

Production later:

```text
Ceph RGW or real S3 object storage
CSI snapshots when storage supports it
database-native backup and PITR for PostgreSQL
restore drills
```

## What Velero Is Useful For

Velero is useful for backing up Kubernetes objects:

```text
Namespaces
Deployments
StatefulSets
DaemonSets
Services
ConfigMaps
Secrets
Ingress/Kong resources
CRDs and custom resources
PVC definitions
```

This answers:

```text
How do I recreate the Kubernetes objects?
```

## What Velero Is Not Enough For

Velero is not a full database backup by itself.

A database is real application data, not only Kubernetes YAML. PostgreSQL, Kafka, Redis, and Elasticsearch all need workload-aware backup and restore procedures.

Examples:

```text
PostgreSQL     -> CNPG backup, WAL archive, PITR, pg_dump/pg_basebackup
Kafka          -> replication, topic recovery plan, broker/data restore procedure
Redis          -> RDB/AOF persistence and cluster-aware restore
Elasticsearch  -> Elasticsearch snapshot repository and index restore
```

Velero may back up PVC definitions, and in production it may also create volume snapshots when the storage supports it. But snapshots are not the same as a database-safe backup. A database can have in-memory writes, WAL files, locks, and consistency rules.

Production needs both:

```text
Velero
  -> restore Kubernetes objects

database-native backups
  -> restore correct application data
```

## Commands

Install:

```powershell
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backups.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backuprepositories.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backupstoragelocations.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_deletebackuprequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_downloadrequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_podvolumebackups.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_podvolumerestores.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_restores.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_schedules.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_serverstatusrequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_volumesnapshotlocations.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v2alpha1/bases/velero.io_datadownloads.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v2alpha1/bases/velero.io_datauploads.yaml

kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/namespace.yaml
kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/minio.yaml
kubectl rollout status deployment/minio -n velero --timeout=300s
kubectl wait --for=condition=complete job/minio-create-velero-bucket -n velero --timeout=300s

kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/velero-server.yaml
kubectl rollout status deployment/velero -n velero --timeout=300s
kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/backup-storage-location.yaml
```

Back up `task-api`:

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/backups/backup-task-api.yaml
kubectl get backups.velero.io -n velero
kubectl describe backups.velero.io task-api-manual -n velero
```

Restore into a test namespace:

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/restores/restore-task-api-example.yaml
kubectl get restores.velero.io -n velero
kubectl describe restores.velero.io task-api-restore-example -n velero
kubectl get all -n task-api-restore
```

Schedule daily backup:

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/backups/schedule-task-api.yaml
kubectl get schedules.velero.io -n velero
```

## References

- Velero MinIO quickstart: https://velero.io/docs/v1.15/contributions/minio/
- Velero BackupStorageLocation: https://velero.io/docs/v1.0.0/api-types/backupstoragelocation/
- Velero install from CLI reference: https://velero.io/docs/v1.18/basic-install/
