# Environments

Environment overlays belong here.

Examples:

```text
local
dev
staging
prod
```

Environment files should answer:

```text
which components are enabled?
which image tags?
how many replicas?
which storage sizes?
which domains?
which resource limits?
```

Secrets should not live here.
Use Vault and External Secrets.
