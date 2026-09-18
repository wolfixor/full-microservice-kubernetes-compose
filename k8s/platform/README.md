# Platform

Shared platform resources belong here.

Examples:

```text
Kafka cluster and topics
monitoring stack
logging stack
Vault and External Secrets config
RBAC
NetworkPolicy
Pod Security labels
Redis
storage classes
backup tooling
```

Rule:

```text
platform resources are shared by multiple apps or control the cluster runtime
```

Every active platform component has a Kustomize entry point under this
directory. Argo CD child Applications reference those entry points directly.
