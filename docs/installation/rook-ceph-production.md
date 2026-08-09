# Production Rook-Ceph Placeholder

Do not apply the local Rook-Ceph manifests on real servers.

Prompt 18 uses:

```text
k8s/rook-ceph/local/
```

That profile is only for Docker Desktop or a local learning cluster:

- one Kubernetes node
- PVC-backed OSD
- replica size 1
- no real disk or node failure protection

Prompt 42 will create the real production profile:

```text
k8s/rook-ceph/production/
```

Production Ceph should use:

- 3 or more real Kubernetes nodes
- dedicated raw block devices for OSDs
- replication across failure domains
- real monitoring and alerting
- tested backup and recovery

If the local Docker Desktop lab fails because the OSD PVC stays pending, do not treat that as a Ceph architecture failure. It usually means the local StorageClass cannot provide the block-mode storage Rook expects for PVC-backed OSDs.
