# Local Rook-Ceph Install Flow

This is a Docker Desktop/local-cluster lab profile. Do not use these manifests on real servers.

## 0. Check Resources

Give Docker Desktop enough room before applying Ceph:

```powershell
kubectl get nodes
kubectl get storageclass
kubectl get pods -A
```

Check that one StorageClass is marked as default:

```text
(default)
```

The local Ceph manifest does not set `storageClassName`, so Kubernetes will use the default StorageClass.

If no StorageClass is default, either mark one default or add `storageClassName` to `ceph-cluster.yaml`.

Important Docker Desktop note:

Rook PVC-backed OSDs need a StorageClass that can provision block-mode PVCs. If the MON PVC is `Bound` but the OSD PVC stays `Pending`, Docker Desktop's `standard` StorageClass is probably not enough for this lab.

Check it with:

```powershell
kubectl get pvc -n rook-ceph
```

If you see this pattern, stop the local Ceph lab and continue Ceph on real servers later:

```text
rook-ceph-mon-a    Bound
set1-data-...      Pending
```

## 1. Install Rook Operator

```powershell
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/crds.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/common.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/csi-operator.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/operator.yaml
kubectl wait deployment/rook-ceph-operator -n rook-ceph --for=condition=Available --timeout=300s
```

## 2. Create Local Ceph Cluster

```powershell
kubectl apply -f k8s/rook-ceph/local/ceph-cluster.yaml
kubectl wait cephcluster/rook-ceph -n rook-ceph --for=condition=Ready --timeout=900s
```

## 3. Create Block Pool And StorageClass

```powershell
kubectl apply -f k8s/rook-ceph/local/ceph-blockpool.yaml
kubectl apply -f k8s/rook-ceph/local/ceph-storageclass.yaml
```

## 4. Test A Ceph-backed PVC

```powershell
kubectl apply -f k8s/rook-ceph/local/test-pvc.yaml
kubectl apply -f k8s/rook-ceph/local/test-pod.yaml
kubectl wait pod/ceph-rbd-test -n task-api --for=condition=Ready --timeout=300s
kubectl exec -n task-api ceph-rbd-test -- cat /data/ceph-test.txt
```

## 5. Validate

```powershell
kubectl get pods -n rook-ceph
kubectl get cephcluster -n rook-ceph
kubectl get cephblockpool -n rook-ceph
kubectl get storageclass rook-ceph-block
kubectl get pvc -n task-api ceph-rbd-test-pvc
```

Optional toolbox:

```powershell
kubectl apply -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/toolbox.yaml
kubectl wait deployment/rook-ceph-tools -n rook-ceph --for=condition=Available --timeout=300s
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph status
kubectl exec -n rook-ceph deploy/rook-ceph-tools -- ceph osd status
```
