### prompt 1:
```
I want to build a production-style learning project that will gradually evolve into a distributed microservices system deployed on Kubernetes.

IMPORTANT:

- Start with the simplest possible architecture.
- Do not introduce microservices yet.
- Do not introduce PostgreSQL, Redis, Kafka, authentication, messaging, caching, or event-driven architecture yet.
- Keep everything intentionally simple.
- The goal is to learn infrastructure incrementally.

Create a Go application named task-api.

Requirements:

- REST API
- In-memory storage only
- CRUD operations for tasks
- Clean architecture
- Dockerfile
- Health endpoint (/health)
- Readiness endpoint (/ready)
- Structured logging
- Configuration through environment variables
- Graceful shutdown

Project structure should be suitable for future growth into microservices.

After generating the application, also generate:

- Kubernetes Deployment manifest
- Kubernetes Service manifest
- Namespace manifest

Do not generate Helm charts yet.

Explain every folder and design decision.
```

### prompt 2:
```
Refactor the task-api application.

Replace in-memory storage with PostgreSQL.

Requirements:

- Repository pattern
- Database migrations
- Connection pooling
- Health checks for PostgreSQL
- Kubernetes Secret for credentials
- PersistentVolumeClaim
- PostgreSQL deployment

Keep everything else unchanged.
```

### prompt 3:
```
Add Redis caching to the task-api.

Requirements:

- Cache task lookups
- Cache invalidation on updates
- Redis health checks
- Kubernetes manifests
- Docker configuration

Keep architecture simple.
```

### prompt 4:
```
Refactor the current FastAPI application into 3 independent microservices:

1. user-service
2. task-service
3. comment-service

IMPORTANT RULES:
- Keep business logic extremely simple (CRUD only)
- No Kafka yet
- No Elasticsearch yet
- No inter-service communication yet
- Each service must be independently deployable
- Each service must have its own Kubernetes Deployment + Service
- Each service must have its own PostgreSQL database (separate instance or schema per service)

Each service must include:
- FastAPI
- Dockerfile
- /health endpoint
- /ready endpoint
- structured logging
- environment-based configuration

Keep architecture minimal but production-structured.
```

### prompt 5:
```
Introduce Kong API Gateway in front of all services.

Requirements:

- Route /users → user-service
- Route /tasks → task-service
- Route /comments → comment-service

Kubernetes setup:
- Kong deployed as ingress gateway
- Services must NOT be publicly exposed anymore
- Only Kong is exposed externally

Add:
- request routing
- basic rate limiting plugin
- request logging plugin

Do NOT add authentication yet.
Keep it simple.
```

### prompt 6:
```
Refactor each microservice to use its own dedicated PostgreSQL database.

Requirements:

- user-service → user_db
- task-service → task_db
- comment-service → comment_db

Each service must:
- use connection pooling
- use migrations
- store secrets in Kubernetes Secrets
- have persistent volume claims

Ensure:
- no shared database between services
- full data isolation per service
```

### prompt 7:
```
Create a new microservice called search-service.

Purpose:
- Provide full-text search across tasks and comments

Requirements:

- Use Elasticsearch as storage backend
- Index data from task-service and comment-service
- Provide REST API:
  GET /search?q=...

Data ingestion:
- subscribe to events (no Kafka yet, simulate ingestion via HTTP calls for now)

Infrastructure:
- Elasticsearch deployment in Kubernetes
- Kibana optional

Keep service simple and focused only on search.
```

### prompt 8:
```
Add Prometheus monitoring to the platform.

Current services:

- user-service
- task-service
- comment-service
- search-service
- Kong Gateway
- PostgreSQL databases
- Redis
- Elasticsearch

Requirements:

- Deploy Prometheus in Kubernetes
- Scrape all application metrics
- Scrape Kong metrics
- Scrape PostgreSQL metrics
- Scrape Redis metrics
- Scrape Elasticsearch metrics

Application metrics:

- HTTP request count
- HTTP request duration
- HTTP error count
- Database query count
- Cache hit/miss count

Generate:

- Prometheus manifests
- ServiceMonitor resources
- scrape configurations
- metric instrumentation for FastAPI services

Use production-oriented Kubernetes patterns.
```

### prompt 9:

```
Add Grafana to the platform.

Requirements:

Create dashboards for:

1. API Dashboard
   - Request rate
   - Error rate
   - Latency

2. PostgreSQL Dashboard
   - Connections
   - Query throughput
   - Replication readiness

3. Redis Dashboard
   - Memory usage
   - Cache hit ratio
   - Command rate

4. Elasticsearch Dashboard
   - Query rate
   - Index size
   - Cluster health

5. Kong Dashboard
   - Requests
   - Upstream latency
   - Error responses

Generate:

- Grafana deployment
- Dashboard JSON files
- Datasource configuration
```

### prompt 10:
```
Add centralized logging using ELK.

Requirements:

Deploy:

- Elasticsearch
- Kibana
- Fluent Bit

Collect logs from:

- user-service
- task-service
- comment-service
- search-service
- Kong
- PostgreSQL
- Redis

Every log entry must include:

- timestamp
- service name
- log level
- request id
- pod name

Generate:

- Kubernetes manifests
- Fluent Bit configuration
- Kibana dashboards

Explain the complete log flow.

```

### prompt 11:

```
Introduce Kafka as the platform event backbone.

Requirements:

Deploy Kafka using Strimzi Operator.

Cluster:

- 3 brokers
- persistent storage
- replication factor 3

Create topics:

- user.created
- user.updated
- task.created
- task.updated
- task.deleted
- comment.created
- comment.deleted

Refactor services:

- publish events to Kafka
- use asynchronous event publishing
- add retries and dead-letter handling

Generate:

- Kubernetes manifests
- topic definitions
- producer implementation

Keep existing APIs unchanged.
```

### prompt 12:
```
Create activity-service.

Purpose:

Maintain an immutable audit log of all business events.

Consume:

- user.*
- task.*
- comment.*

Store events in PostgreSQL.

Schema should contain:

- event id
- event type
- timestamp
- aggregate id
- payload

Expose:

GET /activities

Requirements:

- FastAPI
- Kafka consumer
- PostgreSQL
- Kubernetes deployment
- health checks
- structured logging
```

### prompt 13:

```
Create notification-service.

Purpose:

React to business events.

Consume:

- task.created
- comment.created
- user.created

For now:

- store notifications in PostgreSQL
- expose GET /notifications

Future-ready design:

- email
- sms
- push notifications

Requirements:

- Kafka consumer
- FastAPI
- Kubernetes deployment
- health checks
```

### prompt 14:

```
Replace Kubernetes Deployments with Argo Rollouts.

Requirements:

Implement canary deployments.

Traffic progression:

- 10%
- 25%
- 50%
- 100%

Rollback automatically if:

- error rate exceeds threshold
- latency exceeds threshold

Integrate with Prometheus metrics.

Generate:

- Rollout resources
- Analysis templates
- Traffic policies
```

### prompt 15:
```
Migrate PostgreSQL to a highly available architecture.

Requirements:

Use CloudNativePG.

Topology:

- 1 primary
- 2 replicas

Features:

- automatic failover
- WAL archiving
- backups
- connection pooling

Generate all Kubernetes manifests.

Explain failover procedures.
```

### prompt 16:

```
Migrate Redis to Redis Cluster.

Requirements:

- sharding
- automatic failover
- persistent storage

Update applications if necessary.

Generate:

- cluster manifests
- health checks
- monitoring configuration
```


#### prompt 17:
```
Upgrade Kafka deployment to production-grade operation.

Requirements:

- broker scaling
- partition rebalancing
- rack awareness
- topic replication validation

Add monitoring and operational runbooks.

Generate Kubernetes manifests and documentation.
```


### prompt 18:
```
Deploy Rook-Ceph in Kubernetes.

Requirements:

Provide:

- block storage
- object storage

Create:

- StorageClass for PostgreSQL
- StorageClass for Kafka
- StorageClass for Elasticsearch

Migrate persistent workloads to Ceph-backed volumes.

Explain:

- replication
- recovery
- failure handling
```


### prompt 19:

```
Implement platform backup strategy.

Requirements:

Deploy Velero.

Back up:

- Kubernetes resources
- PostgreSQL
- Redis
- Kafka
- Elasticsearch

Store backups in Ceph object storage.

Create backup schedules.

Generate recovery procedures.
```

### prompt 20:
```
Design disaster recovery procedures.

Scenarios:

1. Kubernetes node failure
2. PostgreSQL primary failure
3. Redis node failure
4. Kafka broker failure
5. Elasticsearch node failure
6. Complete cluster loss

Requirements:

Provide:

- recovery runbooks
- Kubernetes commands
- validation steps
- recovery time objectives
- recovery point objectives

Document full recovery workflows.
```