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

Current repo still keeps most platform YAML in top-level `k8s/` folders.
Prompt 34 migrates them here gradually.
