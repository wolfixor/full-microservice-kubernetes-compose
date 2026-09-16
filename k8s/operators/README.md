# Operators

Operator installs and CRDs belong here.

Examples:

```text
Strimzi
CloudNativePG
ECK
Prometheus Operator
External Secrets Operator
Kyverno
Trivy Operator
Argo Rollouts
cert-manager
```

Rule:

```text
operator must exist before custom resources that use it
```

Current repo still keeps many operator manifests in their existing folders.
Prompt 34 migrates them here one component at a time.
