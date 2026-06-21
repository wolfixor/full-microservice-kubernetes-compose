# Kubernetes Database Migration Fix - Summary

## Problem Identified
The error `relation "comments" does not exist` was occurring in Kubernetes because:
1. Database migrations weren't running in Kubernetes (unlike Docker Compose)
2. The entrypoint script was continuing even when migrations failed
3. No `RUN_MIGRATIONS` environment variable was set in Kubernetes deployments

## Solution Implemented

### 1. **Kubernetes Migration Jobs** (`*/k8s/migration-job.yaml`)
- Created dedicated Job resources for each service
- Jobs run `alembic upgrade head` before services start
- Use same Docker image as the service
- `restartPolicy: Never` - runs exactly once
- `backoffLimit: 3` - retries on failure

### 2. **Improved Entrypoint Script** (`*/docker-entrypoint.sh`)
- Added database table existence check using `psql`
- Now exits with error if tables don't exist (previously continued)
- Clear error messages: "❌ Database tables not found. Did migrations run?"
- Configurable with `CHECK_MIGRATIONS` environment variable

### 3. **Updated Dockerfiles** (`*/Dockerfile`)
- Added `postgresql-client` package for `psql` command
- `netcat-openbsd` already installed (for database connectivity checks)

### 4. **Deployment Files** (`*/k8s/deployment.yaml`)
- Removed `RUN_MIGRATIONS` environment variable (moved to Jobs)
- All other configuration unchanged

## Files Modified

### Comment Service
- `comment-service/k8s/deployment.yaml` - Removed RUN_MIGRATIONS
- `comment-service/k8s/migration-job.yaml` - NEW: Migration Job
- `comment-service/docker-entrypoint.sh` - Added table check
- `comment-service/Dockerfile` - Added postgresql-client

### Task Service  
- `task-service/k8s/deployment.yaml` - Removed RUN_MIGRATIONS
- `task-service/k8s/migration-job.yaml` - NEW: Migration Job
- `task-service/docker-entrypoint.sh` - Added table check
- `task-service/Dockerfile` - Added postgresql-client

### User Service
- `user-service/k8s/deployment.yaml` - Removed RUN_MIGRATIONS
- `user-service/k8s/migration-job.yaml` - NEW: Migration Job
- `user-service/docker-entrypoint.sh` - Added table check
- `user-service/Dockerfile` - Added postgresql-client

### Documentation
- `k8s/migration-guide.md` - NEW: Complete migration guide
- `k8s/init-container-example.yaml` - NEW: Alternative approach
- `README.md` - Updated deployment instructions

## How to Deploy Now

### Step-by-Step
1. **Deploy databases first**: `kubectl apply -f */k8s/postgres.yaml`
2. **Run migrations**: `kubectl apply -f */k8s/migration-job.yaml`
3. **Wait for migrations**: `kubectl wait --for=condition=complete job/*-migrations`
4. **Deploy services**: `kubectl apply -f */k8s/deployment.yaml`

### Quick Fix for Existing Deployment
If services are already deployed and failing:
```bash
# 1. Run migrations
kubectl apply -f comment-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f user-service/k8s/migration-job.yaml

# 2. Restart services (they'll now check for tables)
kubectl rollout restart deployment -n task-api
```

## Why This is Better

1. **Explicit Control**: Migrations run as separate Jobs, not hidden in entrypoint
2. **Better Error Handling**: Services won't start if tables don't exist
3. **Clear Dependencies**: Migration → Database → Service deployment order
4. **Debugging**: Migration logs are separate from service logs
5. **Production Ready**: Follows Kubernetes best practices for database migrations

## Testing
After deploying, check:
```bash
# Service logs should show:
# 🔍 Checking if database tables exist...
# ✅ Database tables exist
# 🎯 Starting application...

# Test API endpoints
curl http://<service-ip>/api/comments
curl http://<service-ip>/api/tasks  
curl http://<service-ip>/api/users
```