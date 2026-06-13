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
- **Independently deployable**: Each service can be deployed separately
- **API Gateway**: Kong gateway routes external traffic to appropriate services

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

# Create PostgreSQL secret
kubectl apply -f ../k8s/secret.yaml

# Deploy each service
kubectl apply -f user-service/k8s/
kubectl apply -f task-service/k8s/
kubectl apply -f comment-service/k8s/
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

## Future Evolution
This is Phase 1 of the microservices architecture. Future phases will add:
- Inter-service communication
- Message queues (Kafka/RabbitMQ)
- Service discovery
- Authentication/Authorization
- Monitoring and observability
- Enhanced rate limiting
- API analytics