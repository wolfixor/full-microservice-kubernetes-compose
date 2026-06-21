# Database Migration Guide for Kubernetes

## Problem
In Kubernetes, the database migrations were not running because:
1. The `RUN_MIGRATIONS` environment variable was not set in deployments
2. The entrypoint script was continuing even if migrations failed

## Solution
We've implemented a two-pronged approach:

### 1. **Kubernetes Migration Jobs**
Each service now has a dedicated migration Job that runs before the service starts.

```bash
# Run migrations for each service
kubectl apply -f comment-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f user-service/k8s/migration-job.yaml

# Check migration status
kubectl get jobs -n task-api
kubectl logs -n task-api -l job-name=comment-service-migrations
```

### 2. **Improved Entrypoint Script**
The entrypoint now:
- Checks if database tables exist before starting
- Exits with clear error message if tables don't exist
- Includes `psql` for database health checks

## Deployment Workflow

### Option A: Manual Migration Jobs (Recommended)
1. Deploy PostgreSQL databases
2. Run migration jobs
3. Deploy services

```bash
# 1. Deploy databases
kubectl apply -f comment-service/k8s/postgres.yaml
kubectl apply -f task-service/k8s/postgres.yaml
kubectl apply -f user-service/k8s/postgres.yaml

# 2. Run migrations
kubectl apply -f comment-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f user-service/k8s/migration-job.yaml

# 3. Wait for migrations to complete
kubectl wait --for=condition=complete job/comment-service-migrations -n task-api --timeout=300s

# 4. Deploy services
kubectl apply -f comment-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/deployment.yaml
kubectl apply -f user-service/k8s/deployment.yaml
```

### Option B: Automatic Migration (For Development)
Set `RUN_MIGRATIONS=true` in deployment environment variables if you want the service to run migrations on startup.

## Key Changes Made

### 1. **Migration Jobs** (`*/k8s/migration-job.yaml`)
- Dedicated Job resources for each service
- Uses same image as the service
- Runs `alembic upgrade head` command
- `restartPolicy: Never` - runs exactly once
- `backoffLimit: 3` - retries up to 3 times if fails

### 2. **Entrypoint Script** (`*/docker-entrypoint.sh`)
- Added database table existence check
- Installed `postgresql-client` for `psql` command
- Clear error messages when tables don't exist
- Configurable with `CHECK_MIGRATIONS` environment variable

### 3. **Dockerfile Updates**
- Added `postgresql-client` package
- `psql` command available for health checks

### 4. **Deployment Files** (`*/k8s/deployment.yaml`)
- Removed `RUN_MIGRATIONS` environment variable (now using Jobs)

## Verification

After deploying, verify migrations worked:

```bash
# Check service logs for table check
kubectl logs -n task-api deployment/comment-service | grep -A5 "Database tables"

# Expected output:
# 🔍 Checking if database tables exist...
# ✅ Database tables exist
# 🎯 Starting application...

# Test API endpoints
kubectl port-forward -n task-api service/comment-service 8001:80
curl http://localhost:8001/api/comments
```

## Troubleshooting

### Migration Job Fails
```bash
# Check migration job logs
kubectl logs -n task-api -l job-name=comment-service-migrations

# Delete and retry
kubectl delete -f comment-service/k8s/migration-job.yaml
kubectl apply -f comment-service/k8s/migration-job.yaml
```

### Service Won't Start (Tables Not Found)
```bash
# Check service logs
kubectl logs -n task-api deployment/comment-service

# Expected error:
# ❌ Database tables not found. Did migrations run?
# 💡 To fix this, run migrations using: alembic upgrade head

# Solution: Run migration job first
kubectl apply -f comment-service/k8s/migration-job.yaml
```

### Skip Table Check (For Testing Only)
```bash
# Add to deployment environment variables:
- name: CHECK_MIGRATIONS
  value: "false"
```

## Best Practices
1. **Production**: Always run migration jobs before deploying services
2. **Development**: Can use `RUN_MIGRATIONS=true` for convenience
3. **CI/CD**: Include migration jobs in deployment pipeline
4. **Rollback**: Delete migration jobs after successful completion to clean up