# Velero Local Cleanup

Delete test restore resources:

```powershell
kubectl delete -f k8s/velero/restores/restore-task-api-example.yaml --ignore-not-found
kubectl delete namespace task-api-restore --ignore-not-found
```

Delete backup objects:

```powershell
kubectl delete -f k8s/velero/backups/schedule-task-api.yaml --ignore-not-found
kubectl delete -f k8s/velero/backups/backup-task-api.yaml --ignore-not-found
```

Delete Velero and MinIO:

```powershell
kubectl delete -f k8s/velero/yaml/backup-storage-location.yaml --ignore-not-found
kubectl delete -f k8s/velero/yaml/velero-server.yaml --ignore-not-found
kubectl delete -f k8s/velero/yaml/minio.yaml --ignore-not-found
kubectl delete -f k8s/velero/yaml/namespace.yaml --ignore-not-found
```

If CRDs remain and this is only your local lab:

```powershell
kubectl delete crd backups.velero.io --ignore-not-found
kubectl delete crd backuprepositories.velero.io --ignore-not-found
kubectl delete crd backupstoragelocations.velero.io --ignore-not-found
kubectl delete crd deletebackuprequests.velero.io --ignore-not-found
kubectl delete crd downloadrequests.velero.io --ignore-not-found
kubectl delete crd podvolumebackups.velero.io --ignore-not-found
kubectl delete crd podvolumerestores.velero.io --ignore-not-found
kubectl delete crd restores.velero.io --ignore-not-found
kubectl delete crd schedules.velero.io --ignore-not-found
kubectl delete crd serverstatusrequests.velero.io --ignore-not-found
kubectl delete crd volumesnapshotlocations.velero.io --ignore-not-found
kubectl delete crd datadownloads.velero.io --ignore-not-found
kubectl delete crd datauploads.velero.io --ignore-not-found
```
