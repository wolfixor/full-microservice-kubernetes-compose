# Operators

Third-party controllers are installed before their custom resources.

```text
Helmfile
  -> installs operators and CRDs
Argo CD child Applications
  -> install platform and application custom resources
```

Pinned releases live in `helmfile.yaml.gotmpl`. Environment sizing lives in
`environments/`. Use `local` for Docker Desktop and `prod` only on a cluster
with production capacity.

The local and dev profiles make Kyverno admission fail open because they run a
single admission replica. Staging and production remain fail closed and use
multiple replicas. This prevents a local controller restart from deadlocking
all Kubernetes writes without weakening production admission control.

The local profile also disables Kyverno's reports controller to reduce API
watch pressure. Admission policies still run; staging and production keep
policy reporting enabled.

```bash
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local list
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local template
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local diff
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local apply
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod template
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod diff
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod apply
```

`raw/` is retained only for offline recovery and installation history. Do not
apply a raw bundle and its Helm release to the same cluster.

## Adopt An Existing Operator

Never delete CRDs to move an existing cluster to Helm. Deleting a CRD can also
delete its custom resources and managed workloads. Back up first, then adopt
one operator at a time:

```bash
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local sync \
  -l name=<release> --take-ownership --skip-crds \
  --args '--force-conflicts'
```

Verify the controller and its custom resources before adopting the next one.
If an immutable Deployment selector differs, replace only that controller
Deployment and retry; keep the CRDs and custom resources.

The existing monitoring stack is not a drop-in match for
`kube-prometheus-stack`. Migrate its Prometheus, Grafana, and Alertmanager
resources as a separate change to avoid running duplicate controllers.

Upgrade order:

```text
backup -> read release notes -> update CRDs -> upgrade operator
       -> verify controller -> update custom resources -> verify workloads
```

Strimzi upgrades require an explicit CRD update. The OCI chart download may be
blocked on restricted networks; mirror the chart and images internally before
running Helmfile in production.
