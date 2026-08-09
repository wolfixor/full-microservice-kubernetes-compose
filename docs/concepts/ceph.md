# Ceph And Rook

Ceph is distributed storage. Rook is the Kubernetes operator that creates and manages Ceph inside Kubernetes.

## Local Flow

```text
Rook Operator
  -> watches CephCluster CR
  -> creates MON, MGR, and OSD pods
  -> CephBlockPool defines where RBD volumes live
  -> StorageClass exposes Ceph RBD to Kubernetes
  -> PVC asks Kubernetes for storage from the default StorageClass
  -> Ceph CSI creates an RBD volume
  -> pod mounts the volume
```

## Main Concepts

- MON: keeps cluster membership and quorum.
- MGR: exposes cluster status, dashboard, and metrics.
- OSD: stores the actual data.
- Pool: logical place where Ceph stores objects.
- RBD: Ceph block device, used by normal ReadWriteOnce PVCs.
- CephFS: shared filesystem, useful for ReadWriteMany.
- RGW: S3-compatible object storage, useful later for backups.
- CSI: Kubernetes storage driver that creates and mounts volumes.

## Local vs Production

Local Docker Desktop Ceph is only for learning:

```text
one machine
one Kubernetes node
PVC-backed OSD from the default StorageClass
replica size 1
```

Production Ceph is different:

```text
3+ real nodes
dedicated raw disks
replica size 3
failure domains across servers
real disk and node failure recovery
```

For now, do not migrate PostgreSQL, Kafka, Redis, Elasticsearch, or Prometheus to Ceph. Prompt 18 only proves that Ceph can provision a test PVC.

## Docker Desktop Limitation

Rook PVC-backed OSDs need block-mode PVC support. On Docker Desktop, the default `standard` StorageClass may bind the MON PVC but leave the OSD PVC pending.

That looks like this:

```text
rook-ceph-mon-a    Bound
set1-data-...      Pending
```

When this happens, the local lab is not worth forcing. Clean it up and continue real Ceph later on real servers in prompt 42.

## Commands

Install and test:

```powershell
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/crds.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/common.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/csi-operator.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/operator.yaml
kubectl wait deployment/rook-ceph-operator -n rook-ceph --for=condition=Available --timeout=300s

kubectl apply -f k8s/rook-ceph/local/ceph-cluster.yaml
kubectl wait cephcluster/rook-ceph -n rook-ceph --for=condition=Ready --timeout=900s

kubectl apply -f k8s/rook-ceph/local/ceph-blockpool.yaml
kubectl apply -f k8s/rook-ceph/local/ceph-storageclass.yaml
kubectl apply -f k8s/rook-ceph/local/test-pvc.yaml
kubectl apply -f k8s/rook-ceph/local/test-pod.yaml
```

Validate:

```powershell
kubectl get pods -n rook-ceph
kubectl get cephcluster -n rook-ceph
kubectl get cephblockpool -n rook-ceph
kubectl get storageclass rook-ceph-block
kubectl get pvc -n task-api ceph-rbd-test-pvc
kubectl exec -n task-api ceph-rbd-test -- cat /data/ceph-test.txt
```

## References

- Rook quickstart: https://rook.io/docs/rook/latest-release/Getting-Started/quickstart/
- Rook PVC-backed cluster: https://www.rook.io/docs/rook/latest-release/CRDs/Cluster/pvc-cluster/
- Rook example configurations: https://www.rook.io/docs/rook/latest-release/Getting-Started/example-configurations/
