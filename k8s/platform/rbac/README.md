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

This is the single managed RBAC source. Security drills live under
`k8s/security-drills` and are never part of Argo CD autosync.
Do not edit both paths long term. The production path is `k8s/platform/rbac/base`.
