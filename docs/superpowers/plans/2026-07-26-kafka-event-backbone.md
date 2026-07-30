# Kafka Event Backbone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Kafka as the platform event backbone using Strimzi and publish user/task/comment domain events without changing existing HTTP APIs.

**Architecture:** Strimzi manages a 3-broker Kafka cluster with persistent storage. User, task, and comment services publish domain events asynchronously after successful database writes; failed publishes retry and then attempt a dead-letter topic.

**Tech Stack:** Kubernetes, Strimzi, KafkaTopic custom resources, FastAPI, aiokafka, pytest.

## Global Constraints

- Keep existing HTTP API paths, request models, and response models unchanged.
- Use 3 Kafka brokers with persistent storage.
- Use replication factor 3 for normal and DLQ topics.
- Publish events asynchronously after DB commit.
- Kafka publish failures must not break existing API responses.

---

### Task 1: Strimzi Kafka Manifests

**Files:**
- Create: `k8s/kafka/namespace.yaml`
- Create: `k8s/kafka/strimzi-install.md`
- Create: `k8s/kafka/kafka-cluster.yaml`
- Create: `k8s/kafka/topics.yaml`

**Interfaces:**
- Produces: Kafka bootstrap DNS `platform-kafka-kafka-bootstrap.kafka.svc:9092`
- Produces: topics `user.created`, `user.updated`, `task.created`, `task.updated`, `task.deleted`, `comment.created`, `comment.deleted`
- Produces: DLQ topics using `<topic>.dlq`

- [ ] Add namespace and installation notes for Strimzi.
- [ ] Add a 3-broker Kafka CR with persistent JBOD storage.
- [ ] Add KafkaTopic resources with `partitions: 3`, `replicas: 3`, and `min.insync.replicas: 2`.
- [ ] Run `kubectl apply --dry-run=client -f k8s/kafka`.

### Task 2: Async Producer Abstraction

**Files:**
- Create: `user-service/app/core/event_producer.py`
- Create: `task-service/app/core/event_producer.py`
- Create: `comment-service/app/core/event_producer.py`
- Modify: `*/app/core/config.py`
- Modify: `*/requirements.txt`
- Test: `user-service/tests/test_event_producer.py`

**Interfaces:**
- Produces: `build_event(event_type: str, source: str, payload: dict) -> dict`
- Produces: `dead_letter_topic(topic: str) -> str`
- Produces: `publish_event(topic: str, key: str, payload: dict) -> bool`
- Produces: `close_event_producer() -> None`

- [ ] Write tests for event envelope and DLQ topic naming.
- [ ] Implement event helper and async aiokafka producer.
- [ ] Add Kafka settings and `aiokafka` dependency.
- [ ] Run the focused test.

### Task 3: Publish Domain Events From APIs

**Files:**
- Modify: `user-service/app/api/endpoints/users.py`
- Modify: `task-service/app/api/endpoints/tasks.py`
- Modify: `comment-service/app/api/endpoints/comments.py`
- Modify: `*/app/main.py`

**Interfaces:**
- Consumes: `publish_event(topic, key, payload)`
- Consumes: `close_event_producer()`

- [ ] Add FastAPI `BackgroundTasks` to write endpoints.
- [ ] Publish `user.created` and `user.updated`.
- [ ] Publish `task.created`, `task.updated`, and `task.deleted`.
- [ ] Publish `comment.created` and `comment.deleted`.
- [ ] Close the producer during service shutdown.

### Task 4: Kubernetes Env Wiring and Docs

**Files:**
- Modify: `user-service/k8s/deployment.yaml`
- Modify: `task-service/k8s/deployment.yaml`
- Modify: `comment-service/k8s/deployment.yaml`
- Modify: `README.md`

**Interfaces:**
- Consumes: bootstrap DNS `platform-kafka-kafka-bootstrap.kafka.svc:9092`

- [ ] Add Kafka env vars to producer service deployments.
- [ ] Add Kafka to README architecture and deployment flow.
- [ ] Run YAML dry-runs for changed manifests.

