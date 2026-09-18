# Apps

Business application manifests belong here.

Current applications:

```text
user-service
task-service
comment-service
search-service
activity-service
notification-service
kong
pgadmin
```

Layout:

```text
base/         long-running resources reconciled by Argo CD
operations/   one-shot migrations, backups, restores, and drills
```

The local environment composes application bases here:

```text
k8s/environments/local/apps/kustomization.yaml
```

Do not add files from `operations/` to an autosynced Kustomization.
