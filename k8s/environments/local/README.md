# Local Environment

Local is for Docker Desktop / kind-style learning clusters.

Expected differences from production:

```text
fewer replicas
smaller storage
smaller CPU/memory requests
local-path or hostpath storage
NodePort/port-forward instead of real load balancer
dev-mode Vault
lab object storage
```

Production should change:

```text
real HA control plane
real CNI such as Cilium or Calico
real storage such as Ceph/cloud disks
real Vault HA
real backup targets
real domains/TLS/load balancers
stronger resource sizing
```
