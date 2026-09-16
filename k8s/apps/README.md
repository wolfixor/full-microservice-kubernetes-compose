# Apps

Business application manifests belong here.

Examples:

```text
user-service
task-service
comment-service
search-service
activity-service
notification-service
kong-gateway
```

Rule:

```text
app manifests should be deployable per environment with clear values or overlays
```

Good future shape:

```text
apps/task-service/base
apps/task-service/overlays/local
apps/task-service/overlays/prod
```

Do not migrate every service at once.
Move one service, render/diff, sync, verify, then continue.
