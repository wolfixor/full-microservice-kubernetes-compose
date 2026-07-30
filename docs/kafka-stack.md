# Kafka Event Flow

## Mental Model

Kafka is the event backbone.

The services still handle normal HTTP requests through Kong. Kafka is used after a successful write, so other services can react asynchronously.

```text
HTTP request
  -> service writes to PostgreSQL
  -> service publishes event to Kafka
  -> consumer service reads event
  -> consumer updates its own data store
```

Kafka does not call the consumer like an HTTP webhook. The consumer keeps a long-lived connection open and waits for messages.

## Request Path

```text
Client
  -> NodePort 30085
  -> Kong
  -> task-service
  -> PostgreSQL
```

Example:

```text
Client creates task -> task-service saves task
```

## Event Path

For the same request, `task-service` publishes an event:

```text
task-service
  -> task.created topic
  -> Kafka
  -> search-service consumer
  -> Elasticsearch
```

Then search can find the task without calling the old ingest endpoint.

## Who Publishes Events

These services are producers:

```text
user-service
task-service
comment-service
```

They publish events after their database write succeeds.

Examples:

```text
user.created
task.created
task.updated
task.deleted
comment.created
comment.deleted
```

They do not create topics at runtime. Topics are created from `k8s/kafka/topics.yaml`.

## Who Consumes Events

Right now, these services are consumers:

```text
search-service
activity-service
notification-service
```

`search-service` consumes task and comment events:

```text
task.created
task.updated
task.deleted
comment.created
comment.deleted
```

It uses those events to update Elasticsearch.

`activity-service` consumes all business events:

```text
user.created
user.updated
task.created
task.updated
task.deleted
comment.created
comment.deleted
```

It stores them in `activity_db` as an immutable audit log.

`notification-service` consumes selected events:

```text
user.created
task.created
comment.created
```

It stores notification records in `notification_db`.

These services are not producers right now.

Its consumer loop is always listening:

```text
search-service
  -> keeps connection to Kafka
  -> waits for messages
  -> processes events when they arrive

activity-service
  -> keeps connection to Kafka
  -> waits for messages
  -> stores audit records

notification-service
  -> keeps connection to Kafka
  -> waits for messages
  -> stores notification records
```

## What Strimzi Does

Strimzi is the Kubernetes operator for Kafka.

You do not manually create broker pods. You create Kafka custom resources, and Strimzi creates the real Kubernetes objects.

```text
Kafka yaml
  -> Strimzi operator
  -> broker pods
  -> services
  -> persistent volumes
```

## Kafka Cluster

The cluster is:

```text
3 brokers
persistent storage
replication factor 3
min in-sync replicas 2
```

This means each topic partition has 3 copies, and Kafka needs at least 2 healthy replicas for safe writes.

## Topics

Business topics:

```text
user.created
user.updated
task.created
task.updated
task.deleted
comment.created
comment.deleted
```

Dead-letter topics:

```text
*.dlq
```

If publishing fails after retries, the producer tries to send the failed event to the matching `.dlq` topic.

Important: DLQ is still inside Kafka.

```text
task.created fails
  -> producer retries
  -> producer sends event to task.created.dlq
```

If Kafka is completely down, the producer cannot write to the normal topic or the `.dlq` topic.

So DLQ does not mean the producer saved the event locally. It means Kafka accepted the failed event into a separate Kafka topic.

For stronger reliability when Kafka is down, the next pattern is an outbox table:

```text
service writes data + event to PostgreSQL
worker publishes event to Kafka
worker marks event as sent
```

## Event Shape

Services publish events like this:

```json
{
  "event_id": "...",
  "event_type": "task.created",
  "source": "task-service",
  "occurred_at": "...",
  "payload": {
    "id": "task-1",
    "title": "Kafka test"
  }
}
```

## Search Flow

For task search, the new flow is:

```text
create task
  -> task-service publishes task.created
  -> Kafka stores the event
  -> search-service reads the event
  -> search-service indexes it in Elasticsearch
  -> activity-service reads the same event
  -> activity-service stores it in PostgreSQL
  -> notification-service reads the same event
  -> notification-service stores a notification
  -> /search can return the task
  -> /activities can return the audit record
  -> /notifications can return the notification
```

The old search ingest endpoint still exists as a manual fallback.
