# Microservices Architecture

This project has been refactored into 3 independent microservices:

## Services Overview

1. **user-service** (Port 8001)
   - Manages user accounts and profiles
   - Endpoint: `/api/users`

2. **task-service** (Port 8002)
   - Manages tasks with status tracking
   - Endpoint: `/api/tasks`

3. **comment-service** (Port 8003)
   - Manages comments on tasks
   - Endpoint: `/api/comments`

4. **search-service** (Port 8004)
   - Provides full-text search across tasks and comments
   - Elasticsearch backend
   - Endpoint: `/api/search`

## Common Features
Each service includes:
- FastAPI framework
- `/health` endpoint for liveness probes
- `/ready` endpoint for readiness probes
- Structured logging
- Environment-based configuration
- Dockerfile for containerization
- Kubernetes manifests for deployment

## Architecture Principles
- **Simple CRUD only**: No complex business logic yet
- **No inter-service communication**: Services are independent
- **Separate databases**: Each service has its own PostgreSQL instance
- **Redis caching**: Cache-aside pattern with Redis for performance
- **Independently deployable**: Each service can be deployed separately
- **API Gateway**: Kong gateway routes external traffic to appropriate services

## Caching Strategy
- **Cache-aside pattern**: Read from Redis first, fall back to PostgreSQL
- **Redis deployment**: Single Redis instance with separate databases per service
- **Cache invalidation**: Automatic on update/delete operations
- **Health checks**: Redis health included in service readiness checks
- **Graceful degradation**: Services operate without Redis if unavailable

## Deployment Instructions

### 1. Build Docker Images
```bash
# Build user-service
cd user-service
docker build -t user-service .

# Build task-service
cd ../task-service
docker build -t task-service .

# Build comment-service
cd ../comment-service
docker build -t comment-service .

# Build search-service
cd ../search-service
docker build -t search-service .
```

### 2. Deploy to Kubernetes
```bash
# Create namespace (if not exists)
kubectl apply -f ../k8s/namespace.yaml

# Create PostgreSQL secret (includes Redis password)
kubectl apply -f ../k8s/secret.yaml

# Deploy Redis cache
kubectl apply -f ../k8s/redis-deployment.yaml

# Deploy PostgreSQL databases
kubectl apply -f user-service/k8s/postgres.yaml
kubectl apply -f task-service/k8s/postgres.yaml
kubectl apply -f comment-service/k8s/postgres.yaml

# Run database migrations (IMPORTANT: Run before services)
kubectl apply -f user-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f comment-service/k8s/migration-job.yaml

# Wait for migrations to complete
kubectl wait --for=condition=complete job/user-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/task-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/comment-service-migrations -n task-api --timeout=300s

# Deploy Elasticsearch (required for search-service)
kubectl apply -f k8s/elasticsearch-deployment.yaml

# Deploy services (after migrations complete)
kubectl apply -f user-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/deployment.yaml
kubectl apply -f comment-service/k8s/deployment.yaml
kubectl apply -f search-service/k8s/deployment.yaml
```

### 3. Deploy Kong API Gateway
```bash
# Deploy Kong gateway for external access
kubectl apply -f kong-gateway/k8s/
```

### 4. Verify Deployment
```bash
# Check pods
kubectl get pods -n task-api

# Check services
kubectl get svc -n task-api

# Get Kong external IP
kubectl get service kong-gateway -n task-api
```

## Testing the Services

### Direct Access (internal)
```bash
# User Service
curl http://localhost:8001/health
curl http://localhost:8001/api/users

# Task Service
curl http://localhost:8002/health
curl http://localhost:8002/api/tasks

# Comment Service
curl http://localhost:8003/health
curl http://localhost:8003/api/comments

# Search Service
curl http://localhost:8004/health
curl http://localhost:8004/api/search?q=example
```

### Through Kong API Gateway (external)
```bash
# Get Kong external IP
KONG_IP=$(kubectl get service kong-gateway -n task-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test routes through Kong
curl http://$KONG_IP/users
curl http://$KONG_IP/tasks
curl http://$KONG_IP/comments
curl http://$KONG_IP/search?q=example
```

## Redis Caching Features
- **Cache-aside pattern**: Intelligent read-through caching
- **Redis health monitoring**: Integrated into service readiness
- **Database separation**: Each service uses different Redis database
- **Cache invalidation**: Automatic on data updates
- **Graceful degradation**: Services work without Redis
- **Performance optimized**: 5-minute TTL with LRU eviction

## Search Service Features
- **Full-text search**: Elasticsearch-powered search across tasks and comments
- **Event ingestion simulation**: HTTP-based ingestion from task and comment services
- **Flexible indexing**: Support for different document types (task, comment)
- **Fuzzy matching**: Auto-fuzziness for better search results
- **Multi-field search**: Searches across title, content, and description fields
- **Result ranking**: Score-based ranking with recency bias

## Future Evolution
This is Phase 3 with Search Service. Future phases will add:
- **Event-driven architecture**: Replace HTTP ingestion with Kafka/RabbitMQ
- **Search analytics**: Track search patterns and popular queries
- **Advanced search features**: Faceted search, filtering, autocomplete
- **Search relevance tuning**: Custom ranking algorithms
- **Search monitoring**: Integration with Elasticsearch monitoring tools
- **Cross-service search**: Unified search across all microservices
- **Search API enhancements**: Pagination, sorting, field selection



### the architecture at the end will be this:
```

                                         Internet
                                             |
                                             |
                                      +-------------+
                                      |    Kong     |
                                      |   Gateway   |
                                      +-------------+
                                             |
      --------------------------------------------------------------------------------
      |                    |                    |                    |                |
      v                    v                    v                    v                v

+-------------+    +-------------+    +-------------+    +-------------+    +------------------+
| User        |    | Task        |    | Comment     |    | Search      |    | Notification     |
| Service     |    | Service     |    | Service     |    | Service     |    | Service          |
+-------------+    +-------------+    +-------------+    +-------------+    +------------------+
      |                    |                    |                    |                |
      |                    |                    |                    |                |
      v                    v                    v                    v                |
+-------------+    +-------------+    +-------------+    +------------------+        |
| PostgreSQL  |    | PostgreSQL  |    | PostgreSQL  |    | Elasticsearch    |        |
+-------------+    +-------------+    +-------------+    +------------------+        |
      |                    |                    |                    ^                |
      |                    |                    |                    |                |
      ---------------------------------------------------------------------------------
                                             |
                                             v
                                      +-------------+
                                      |    Kafka    |
                                      |  Cluster    |
                                      +-------------+
                                             |
                    -------------------------------------------------
                    |                       |                       |
                    v                       v                       v

             +-------------+       +------------------+    +------------------+
             | Activity    |       | Notification     |    | Search Service   |
             | Service     |       | Service          |    | Kafka Consumer   |
             +-------------+       +------------------+    +------------------+
                    |
                    v
             +-------------+
             | PostgreSQL  |
             | activity_db |
             +-------------+


========================================================================================
                               SHARED PLATFORM SERVICES
========================================================================================

+------------------+      +------------------+      +------------------+
| Redis Cluster    |      | Prometheus       |      | Grafana          |
| Cache Layer      |      | Metrics          |      | Dashboards       |
+------------------+      +------------------+      +------------------+

+------------------+      +------------------+      +------------------+
| Fluent Bit       | ---> | Elasticsearch    | ---> | Kibana           |
| Log Collection   |      | Log Storage      |      | Log Analysis     |
+------------------+      +------------------+      +------------------+

+------------------+
| Argo Rollouts    |
| Canary/BlueGreen |
+------------------+

+------------------+
| Velero           |
| Backups          |
+------------------+

+------------------+
| Rook-Ceph        |
| Storage Layer    |
+------------------+


========================================================================================
                                   STORAGE LAYER
========================================================================================

                          +------------------------+
                          |      Rook-Ceph         |
                          | Distributed Storage    |
                          +------------------------+
                                       |
            ----------------------------------------------------------------
            |                    |                    |                     |
            v                    v                    v                     v

    PostgreSQL HA        Kafka Cluster       Elasticsearch       Backup Storage
    (Primary+Replicas)   (3 Brokers)         Persistent Data     (Velero)

            |
            v

      Redis Cluster

```