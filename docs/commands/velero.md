# Velero Local Install With YAML

This step uses plain Kubernetes YAML.

Local flow:

```text
YAML
  -> creates MinIO
  -> creates Velero server
  -> creates BackupStorageLocation
  -> Velero writes backups to MinIO
```

## Install

Apply Velero CRDs first. These CRDs define resources like `Backup`, `Schedule`, `Restore`, and `BackupStorageLocation`.

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
```

Then apply local MinIO and Velero:

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/namespace.yaml
kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/minio.yaml
kubectl rollout status deployment/minio -n velero --timeout=300s
kubectl wait --for=condition=complete job/minio-create-velero-bucket -n velero --timeout=300s

kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/velero-server.yaml
kubectl rollout status deployment/velero -n velero --timeout=300s

kubectl apply -f k8s/environments/local/platform/backup/velero/yaml/backup-storage-location.yaml
```

## Check

```powershell
kubectl get pods -n velero
kubectl get backupstoragelocation -n velero
kubectl describe backupstoragelocation default -n velero
```

## Create Manual Backup

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/backups/backup-task-api.yaml
kubectl get backups.velero.io -n velero
kubectl describe backups.velero.io task-api-manual -n velero
```

## Create Schedule

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/backups/schedule-task-api.yaml
kubectl get schedules.velero.io -n velero
kubectl describe schedules.velero.io task-api-daily -n velero
```

## Restore Test

The restore example maps `task-api` into `task-api-restore` so the test does not overwrite the running namespace.

```powershell
kubectl apply -f k8s/environments/local/platform/backup/velero/restores/restore-task-api-example.yaml
kubectl get restores.velero.io -n velero
kubectl describe restores.velero.io task-api-restore-example -n velero
kubectl get all -n task-api-restore
```

## What This Backs Up

This local setup backs up Kubernetes resource definitions into MinIO.

It does not create storage snapshots:

```yaml
snapshotVolumes: false
```

Database-safe backup still needs database-aware backup and PITR later.
