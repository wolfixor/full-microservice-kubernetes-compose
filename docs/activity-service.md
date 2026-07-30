# Activity Service Flow

## Mental Model

`activity-service` is the audit log service.

It does not create business data. It listens to Kafka and saves a permanent history of events.

```text
Kafka event
  -> activity-service consumer
  -> activity_db PostgreSQL
  -> GET /activities
```

## Why It Exists

Search answers:

```text
what can I find?
```

Activity answers:

```text
what happened?
when did it happen?
which service produced it?
which entity changed?
what was the payload?
```

## Event Flow

Example with task creation:

```text
Client
  -> Kong
  -> task-service
  -> task_db
  -> task.created topic
  -> Kafka
  -> activity-service
  -> activity_db
```

The same `task.created` event can also be consumed by `search-service`.

That is the point of Kafka:

```text
one producer event
  -> many independent consumers
```

## Consumed Topics

`activity-service` consumes all business topics:

```text
user.created
user.updated
task.created
task.updated
task.deleted
comment.created
comment.deleted
```

It is only a consumer right now. It does not publish Kafka events.

## Stored Data

Each Kafka event becomes one activity row:

```text
event_id
event_type
source
aggregate_id
occurred_at
payload
created_at
```

`aggregate_id` is the affected object ID.

Example:

```text
event_type: task.created
source: task-service
aggregate_id: task id
payload: task data
```

## API

Through Kong:

```bash
curl "http://localhost:8888/activities/?event_type=task.created"
```

Direct service path:

```bash
curl "http://localhost:8005/api/activities/?event_type=task.created"
```

Useful filters:

```text
event_type
aggregate_id
limit
offset
```

## Deploy Flow

```bash
kubectl apply -f activity-service/k8s/postgres.yaml
kubectl apply -f activity-service/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/activity-service-migrations -n task-api --timeout=300s
kubectl apply -f activity-service/k8s/deployment.yaml
```

Kong route:

```bash
kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl rollout restart deployment/kong-gateway -n task-api
```

