# Local Rook-Ceph Cleanup

Only use this for the local lab profile.

## Remove Test Workload

```powershell
kubectl delete -f k8s/rook-ceph/local/test-pod.yaml --ignore-not-found
kubectl delete -f k8s/rook-ceph/local/test-pvc.yaml --ignore-not-found
```

## Remove StorageClass And Pool

```powershell
kubectl delete -f k8s/rook-ceph/local/ceph-storageclass.yaml --ignore-not-found
kubectl delete -f k8s/rook-ceph/local/ceph-blockpool.yaml --ignore-not-found
```

## Remove Ceph Cluster

```powershell
kubectl delete -f k8s/rook-ceph/local/ceph-cluster.yaml --ignore-not-found
kubectl delete cephcluster rook-ceph -n rook-ceph --ignore-not-found
```

Wait until Ceph pods are gone:

```powershell
kubectl get pods -n rook-ceph
kubectl get pvc -n rook-ceph
```

If local PVCs remain and this is only your lab cluster:

```powershell
kubectl delete pvc -n rook-ceph --all
```

## Remove Operator

```powershell
kubectl delete -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/operator.yaml --ignore-not-found
kubectl delete -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/csi-operator.yaml --ignore-not-found
kubectl delete -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/common.yaml --ignore-not-found
kubectl delete -f https://raw.githubusercontent.com/rook/rook/v1.20.3/deploy/examples/crds.yaml --ignore-not-found
```
