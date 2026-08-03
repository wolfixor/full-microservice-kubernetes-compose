# PostgreSQL Cutover Flow

## Goal

Move `task-service` from the old manual PostgreSQL StatefulSet to CloudNativePG.

```text
old: task-service -> task-service-db
new: task-service -> task-db-pooler-rw -> task-db-rw
```

## Maintenance Window Flow

This is not true zero downtime.

It is the safe learning flow with writes stopped.

```text
scale task-service to 0
  -> dump old task-service-db
  -> restore into task-db
  -> run Alembic migrations
  -> scale task-service back to 10
  -> verify reads and writes
```

## Commands

Scale app down:

```bash
kubectl scale rollout/task-service -n task-api --replicas=0
kubectl get pods -n task-api | grep task-service
```

Dump and restore:

```bash
kubectl exec -n task-api task-service-db-0 -- \
  env PGPASSWORD=postgres \
  pg_dump -U postgres -d task_db --clean --if-exists --no-owner --no-privileges \
| kubectl exec -i -n task-api task-db-1 -- \
  env PGPASSWORD=task_app_password \
  psql -h task-db-rw -U task_app -d task_db
```

Run migrations:

```bash
kubectl delete job task-service-migrations -n task-api --ignore-not-found
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/task-service-migrations -n task-api --timeout=300s
```

Scale app back up:

```bash
kubectl apply -f task-service/k8s/rollout.yaml
kubectl wait --for=condition=Ready pod -n task-api -l app=task-service --timeout=300s
```

## Verify

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=task_app_password \
  psql -h task-db-pooler-rw -U task_app -d task_db \
  -c "select count(*) from tasks;"

kubectl exec -n task-api task-service-db-0 -- \
  env PGPASSWORD=postgres \
  psql -U postgres -d task_db \
  -c "select count(*) from tasks;"

curl http://localhost:8888/tasks/
```

After cutover, new writes should increase `task-db`.

The old `task-service-db` should stay unchanged and can be kept temporarily for rollback.

## Production Note

True zero downtime needs sync before cutover:

```text
initial copy
  -> logical replication or CDC
  -> wait for lag to reach zero
  -> switch app connection
  -> keep old DB for rollback
```
