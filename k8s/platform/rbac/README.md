# Platform RBAC

RBAC is the first Prompt 34 component converted to Kustomize style.

Current desired path:

```text
k8s/platform/rbac/base
```

Argo CD app:

```text
platform-rbac
```

Why RBAC first:

```text
no pods restart
no data plane change
small blast radius
easy to verify with kubectl auth can-i
```

The old raw manifests in `k8s/rbac` are kept temporarily as legacy learning files.
Do not edit both paths long term. The production path is `k8s/platform/rbac/base`.
