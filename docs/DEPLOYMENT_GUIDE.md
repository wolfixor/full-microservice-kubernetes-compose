# Complete Deployment Guide
## For Docker Compose & Kubernetes with Redis Caching & Alembic Migrations

---

## 🎯 **What's Been Implemented**

### **✅ Redis Caching (Cache-aside Pattern)**
- Individual item lookups cached (`GET /api/{type}/{id}`)
- Collections NOT cached (`GET /api/{type}/`) - by design
- 5-minute TTL with automatic expiration
- Cache invalidation on updates/deletes
- Graceful degradation (works without Redis)

### **✅ Proper Alembic Migrations**
- Replaced dangerous `create_all()` with safe migrations
- Docker Compose: Auto-migrate on startup
- Kubernetes: Separate migration jobs
- Data persistence between restarts
- Rollback capability

### **✅ Production-Ready Configuration**
- Environment-based configuration
- Health checks with Redis monitoring
- Connection pooling and timeouts
- Resource limits and scaling

---

## 🐳 **Docker Compose Deployment**

### **1. First-Time Setup**
```bash
# Clone and navigate to project
cd microservice-kuber

# Build all services with migrations
docker-compose build

# Start everything (migrations will run automatically)
docker-compose up -d

# Check logs for migrations
docker-compose logs user-service | grep -A5 -B5 "migration"
docker-compose logs task-service | grep -A5 -B5 "migration"
docker-compose logs comment-service | grep -A5 -B5 "migration"
```

### **2. Normal Development Workflow**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build -d

# View logs
docker-compose logs -f user-service
```

### **3. Testing Redis Caching**
```bash
# Get a comment ID first
curl http://localhost:8001/api/comments/

# Test individual comment caching (THIS IS CACHED!)
COMMENT_ID="822fd8e5-ba05-4370-992b-831c926d210a"
curl http://localhost:8001/api/comments/$COMMENT_ID  # First: database
curl http://localhost:8001/api/comments/$COMMENT_ID  # Second: Redis cache ⚡

# Check Redis
docker exec -it microservice-kuber-comment-service-redis-1 redis-cli KEYS "*"
```

### **4. Creating New Migrations**
```bash
# Enter service container
docker-compose exec user-service bash

# Generate migration after model changes
alembic revision --autogenerate -m "Add new field"

# Exit and restart to apply
exit
docker-compose restart user-service
```

---

## ☸️ **Kubernetes Deployment**

### **1. Prerequisites**
```bash
# Install kubectl
# Configure kubectl for your cluster
# Ensure namespace exists: kubectl create namespace task-api
```

### **2. First-Time Deployment (With Migrations)**
```bash
# 1. Apply namespace and secrets
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml

# 2. Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# 3. Deploy databases
kubectl apply -f user-service/k8s/db-deployment.yaml
kubectl apply -f task-service/k8s/db-deployment.yaml
kubectl apply -f comment-service/k8s/db-deployment.yaml

# 4. Wait for databases
kubectl wait --for=condition=ready pod -l app=user-service-db -n task-api --timeout=300s

# 5. Run migrations (ONE TIME PER SERVICE)
kubectl apply -f k8s/user-service-migration-job.yaml
kubectl wait --for=condition=complete job/user-service-migration -n task-api --timeout=300s

kubectl apply -f k8s/task-service-migration-job.yaml
kubectl wait --for=condition=complete job/task-service-migration -n task-api --timeout=300s

kubectl apply -f k8s/comment-service-migration-job.yaml
kubectl wait --for=condition=complete job/comment-service-migration -n task-api --timeout=300s

# 6. Deploy applications
kubectl apply -f user-service/k8s/
kubectl apply -f task-service/k8s/
kubectl apply -f comment-service/k8s/

# 7. Verify
kubectl get pods -n task-api
kubectl get services -n task-api
```

### **3. Update Deployment (New Version)**
```bash
# 1. Build and push new image
docker build -t your-registry/user-service:v2 ./user-service
docker push your-registry/user-service:v2

# 2. Create new migration job for v2
# Update k8s/user-service-migration-job.yaml with new image
kubectl apply -f k8s/user-service-migration-job.yaml
kubectl wait --for=condition=complete job/user-service-migration -n task-api --timeout=300s

# 3. Update deployment
kubectl set image deployment/user-service user-service=your-registry/user-service:v2 -n task-api

# 4. Monitor rollout
kubectl rollout status deployment/user-service -n task-api
```

### **4. Emergency Rollback**
```bash
# 1. Pause rollout
kubectl rollout pause deployment/user-service -n task-api

# 2. Run rollback migration
# Create rollback-job.yaml with: command: ["alembic", "downgrade", "-1"]
kubectl apply -f k8s/rollback-job.yaml
kubectl wait --for=condition=complete job/user-service-rollback -n task-api --timeout=300s

# 3. Rollback deployment
kubectl rollout undo deployment/user-service -n task-api

# 4. Resume
kubectl rollout resume deployment/user-service -n task-api
```

---

## 🔧 **Troubleshooting**

### **Docker Compose Issues:**

#### **Problem: "Data lost on restart"**
**Cause**: Still using `create_all()` in main.py  
**Fix**: Ensure `Base.metadata.create_all()` is removed from all main.py files

#### **Problem: "Migrations not running"**
**Fix**: Check `RUN_MIGRATIONS=true` is set in docker-compose.yml

#### **Problem: "Redis cache not working"**
**Test**: 
```bash
# Test individual item (SHOULD cache)
curl http://localhost:8001/api/comments/{id}

# Test collection (WON'T cache - by design)
curl http://localhost:8001/api/comments/
```

### **Kubernetes Issues:**

#### **Problem: "Migration job hangs"**
```bash
# Check job status
kubectl describe job/user-service-migration -n task-api

# Check pod logs
kubectl logs job/user-service-migration -n task-api

# Check database connectivity
kubectl run test-db --image=postgres:latest --rm -it --restart=Never -- \
  psql -h user-service-db -U postgres -d user_db -c "SELECT 1"
```

#### **Problem: "Redis connection failed"**
```bash
# Check Redis deployment
kubectl get pods -l app=redis -n task-api

# Test Redis connection
kubectl run test-redis --image=redis:latest --rm -it --restart=Never -- \
  redis-cli -h redis-service -p 6379 ping
```

#### **Problem: "Service not ready"**
```bash
# Check readiness probe
kubectl describe pod -l app=user-service -n task-api | grep -A10 "Readiness"

# Check service logs
kubectl logs deployment/user-service -n task-api

# Test manually
kubectl exec deployment/user-service -n task-api -- curl http://localhost:8000/ready
```

---

## 📊 **Verification Commands**

### **Docker Compose:**
```bash
# Check all services
docker-compose ps

# Check migration status
docker-compose exec user-service alembic current
docker-compose exec task-service alembic current
docker-compose exec comment-service alembic current

# Check Redis cache
docker exec -it microservice-kuber-user-service-redis-1 redis-cli KEYS "*"
docker exec -it microservice-kuber-task-service-redis-1 redis-cli KEYS "*"
docker exec -it microservice-kuber-comment-service-redis-1 redis-cli KEYS "*"

# Test endpoints
curl http://localhost:8001/ready  # Should include Redis status
curl http://localhost:8002/ready
curl http://localhost:8003/ready
```

### **Kubernetes:**
```bash
# Check all resources
kubectl get all -n task-api

# Check migration jobs
kubectl get jobs -n task-api

# Check database state
kubectl exec deployment/user-service -n task-api -- alembic current
kubectl exec deployment/task-service -n task-api -- alembic current
kubectl exec deployment/comment-service -n task-api -- alembic current

# Check Redis
kubectl exec deployment/redis -n task-api -- redis-cli KEYS "*"

# Test services
kubectl port-forward service/user-service 8003:8000 -n task-api &
curl http://localhost:8003/ready
```

---

## 🎯 **Key Differences: Docker Compose vs Kubernetes**

| Feature | Docker Compose | Kubernetes |
|---------|----------------|------------|
| **Migrations** | Auto on startup | Separate job + wait |
| **Redis** | Separate instance per service | Shared instance, separate DBs |
| **Scaling** | Manual | Auto-scaling possible |
| **Deployment** | `docker-compose up` | Multiple steps with jobs |
| **Best for** | Development | Production |

---

## 🔄 **Migration Flow Comparison**

### **Docker Compose:**
```
1. Container starts
2. Entrypoint waits for DB
3. Runs: alembic upgrade head
4. Starts: uvicorn app
```

### **Kubernetes:**
```
1. Apply: migration-job.yaml
2. Wait: kubectl wait for job completion
3. Apply: deployment.yaml (waits for migration)
4. Pod: Starts uvicorn app
```

---

## ⚡ **Quick Reference**

### **Build Commands:**
```bash
# Docker Compose
docker-compose build
docker-compose up --build -d

# Kubernetes
docker build -t your-registry/service:tag ./service
docker push your-registry/service:tag
```

### **Test Commands:**
```bash
# Test caching
curl http://localhost:8001/api/comments/{id}  # Individual - CACHED
curl http://localhost:8001/api/comments/      # Collection - NOT cached

# Test migrations
docker-compose exec user-service alembic current
kubectl exec deployment/user-service -- alembic current

# Test health
curl http://localhost:8001/ready  # Includes Redis status
```

### **Cleanup Commands:**
```bash
# Docker Compose
docker-compose down -v  # Removes volumes too

# Kubernetes
kubectl delete -f k8s/ --ignore-not-found
kubectl delete namespace task-api --ignore-not-found
```

---

## 🚨 **Critical Notes**

### **1. Data Safety**
- ❌ **Before**: `create_all()` drops data on restart
- ✅ **Now**: Alembic preserves data, safe migrations

### **2. Caching Behavior**
- ✅ **Cached**: Individual lookups (`GET /api/{type}/{id}`)
- ❌ **Not cached**: Collections (`GET /api/{type}/`) - by design

### **3. Production Readiness**
- **Docker Compose**: Good for development
- **Kubernetes**: Required for production
- **Always**: Test migrations before deploying

### **4. Backup Strategy**
```bash
# Before major migrations
docker-compose exec user-service-db pg_dump -U postgres user_db > backup.sql

# In Kubernetes
kubectl exec deployment/user-service-db -- pg_dump -U postgres user_db > backup.sql
```

---

## 🎉 **You're Now Production Ready!**

### **What You Have:**
1. ✅ **Safe migrations** (no more data loss)
2. ✅ **Redis caching** (performance boost)
3. ✅ **Health monitoring** (Redis included)
4. ✅ **Both environments** (Docker Compose + Kubernetes)
5. ✅ **Rollback capability** (emergency recovery)

### **Next Steps:**
1. **Test thoroughly** in staging first
2. **Backup databases** before production migration
3. **Monitor performance** after Redis deployment
4. **Plan scaling** based on usage patterns

**Happy deploying! Your microservices are now production-ready with proper database migrations and Redis caching!** 🚀