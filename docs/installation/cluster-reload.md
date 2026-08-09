# Common Restart Commands

## Current App Workloads

```bash
kubectl rollout restart deployment/user-service deployment/comment-service deployment/search-service deployment/activity-service deployment/notification-service -n task-api
kubectl apply -f task-service/k8s/rollout.yaml
```

`task-service` is managed by Argo Rollouts, not a normal Deployment.

## Current Stateful Workloads

```bash
kubectl rollout restart statefulset/redis-cluster -n task-api
kubectl rollout restart statefulset/user-service-db statefulset/comment-service-db statefulset/activity-service-db statefulset/notification-service-db -n task-api
```

`task-service` PostgreSQL is managed by CloudNativePG:

```bash
kubectl get cluster task-db -n task-api
```

## Manual Legacy Workloads

Only use these if you intentionally apply the manual manifests:

```bash
kubectl apply -f task-service/k8s/postgres-statefulset-manual.yaml
kubectl apply -f k8s/redis-standalone-manual.yaml
```
