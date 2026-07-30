# Notification Service Flow

## Mental Model

`notification-service` reacts to Kafka events and stores notifications.

For now it does not send email, SMS, or push messages. It only creates notification records in PostgreSQL.

```text
Kafka event
  -> notification-service consumer
  -> notification_db PostgreSQL
  -> GET /notifications
```

## Why It Exists

Activity answers:

```text
what happened?
```

Notification answers:

```text
what should a user be told about?
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
  -> notification-service
  -> notification_db
```

The same `task.created` event can also be consumed by `search-service` and `activity-service`.

```text
one Kafka event
  -> search index
  -> activity audit log
  -> notification record
```

## Consumed Topics

`notification-service` consumes selected business topics:

```text
user.created
task.created
comment.created
```

It is only a consumer right now. It does not publish Kafka events.

## Stored Data

Each supported Kafka event becomes one notification row:

```text
event_id
event_type
source
user_id
type
title
message
status
payload
occurred_at
created_at
```

`status` starts as:

```text
unread
```

## API

Through Kong:

```bash
curl "http://localhost:8888/notifications/?type=task_created"
```

Direct service path:

```bash
curl "http://localhost:8006/api/notifications/?type=task_created"
```

Useful filters:

```text
user_id
status
type
limit
offset
```

## Deploy Flow

```bash
kubectl apply -f notification-service/k8s/postgres.yaml
kubectl apply -f notification-service/k8s/migration-job.yaml
kubectl wait --for=condition=complete job/notification-service-migrations -n task-api --timeout=300s
kubectl apply -f notification-service/k8s/deployment.yaml
```

Kong route:

```bash
kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl rollout restart deployment/kong-gateway -n task-api
```

