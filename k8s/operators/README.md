# Operators

Third-party controllers are installed before their custom resources.

```text
Helmfile
  -> installs operators and CRDs
Argo CD child Applications
  -> install platform and application custom resources
```

Pinned releases live in `helmfile.yaml.gotmpl`. Environment switches live in
`environments/`. The local switch is intentionally off because this existing
lab cluster was installed from raw bundles; Helm must not silently adopt it.

```bash
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local list
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod template
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod diff
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e prod apply
```

`raw/` is retained only for offline recovery and installation history. Do not
apply a raw bundle and its Helm release to the same cluster.

Upgrade order:

```text
backup -> read release notes -> update CRDs -> upgrade operator
       -> verify controller -> update custom resources -> verify workloads
```

Strimzi upgrades require an explicit CRD update. The OCI chart download may be
blocked on restricted networks; mirror the chart and images internally before
running Helmfile in production.
