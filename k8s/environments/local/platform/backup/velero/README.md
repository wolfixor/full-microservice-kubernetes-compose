# Local Velero Lab

This folder preserves the local MinIO and raw Velero learning setup. It is not
part of Argo CD autosync. Create credentials at runtime before applying it:

```bash
kubectl create namespace velero --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic minio-credentials -n velero \
  --from-literal=root-user="$MINIO_ROOT_USER" \
  --from-literal=root-password="$MINIO_ROOT_PASSWORD"

# Create credentials-velero.local from credentials-velero.example first.
kubectl create secret generic cloud-credentials -n velero \
  --from-file=cloud=credentials-velero.local
```

Production uses the Velero Helm chart, External Secrets, restricted RBAC, and
real S3 or Ceph RGW. Database backups remain workload-aware and separate.
