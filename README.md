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

# Deploy services (after migrations complete)
kubectl apply -f user-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/deployment.yaml
kubectl apply -f comment-service/k8s/deployment.yaml
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
```

### Through Kong API Gateway (external)
```bash
# Get Kong external IP
KONG_IP=$(kubectl get service kong-gateway -n task-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test routes through Kong
curl http://$KONG_IP/users
curl http://$KONG_IP/tasks
curl http://$KONG_IP/comments
```

## Redis Caching Features
- **Cache-aside pattern**: Intelligent read-through caching
- **Redis health monitoring**: Integrated into service readiness
- **Database separation**: Each service uses different Redis database
- **Cache invalidation**: Automatic on data updates
- **Graceful degradation**: Services work without Redis
- **Performance optimized**: 5-minute TTL with LRU eviction

## Future Evolution
This is Phase 2 with Redis caching. Future phases will add:
- Redis clustering for high availability
- Cache warming strategies
- Cache analytics and monitoring
- Inter-service communication
- Message queues (Kafka/RabbitMQ)
- Service discovery
- Authentication/Authorization
- Enhanced rate limiting
- API analytics



### the architecture at the end will be this:
```


                    Internet
                        |
                        |
                   +---------+
                   |  Kong   |
                   | Gateway |
                   +---------+
                        |
      -----------------------------------------
      |           |            |             |
      v           v            v             v

+------------+ +------------+ +------------+ +------------+
| User       | | Task       | | Comment    | | Search     |
| Service    | | Service    | | Service    | | Service    |
+------------+ +------------+ +------------+ +------------+
      |              |              |             |
      v              v              v             v

+------------+ +------------+ +------------+ +----------------+
| PostgreSQL | | PostgreSQL | | PostgreSQL | | Elasticsearch  |
+------------+ +------------+ +------------+ +----------------+

                     |
                     v
                 +---------+
                 | Kafka   |
                 +---------+
                     |
     ------------------------------------
     |                                  |
     v                                  v

+---------------+               +---------------+
| Notification  |               | Activity      |
| Service       |               | Service       |
+---------------+               +---------------+
                     |
                     v
                  +--------+
                  | Redis  |
                  +--------+

```