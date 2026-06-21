# Database Migration Guide
## How Alembic Works in Docker Compose vs Kubernetes

---

## 📦 **Current Setup (Development Mode)**

### **What's Happening Now:**
```python
# app/main.py - Line 23-28
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables (in production, use migrations instead)
    try:
        Base.metadata.create_all(bind=sync_engine)  # ⚠️ DEV ONLY!
        logging.info("Database tables created/verified")
```

**Problem**: This uses `create_all()` which:
- ❌ Drops and recreates tables (data loss!)
- ❌ No version control
- ❌ No rollback capability
- ❌ Not suitable for production

---

## 🔄 **How Alembic Should Work**

### **Migration Flow:**
```
Developer → Creates Migration → Alembic → Database
      ↓            ↓              ↓          ↓
   Changes    Version file    Applies     Schema
   code       (upgrade/down)  changes     updated
```

### **Two Migration Approaches:**

#### **1. 🐳 Docker Compose Approach** (Simple)
- Run alembic as part of service startup
- Auto-migrate on container start
- Good for development/testing

#### **2. ☸️ Kubernetes Approach** (Production)
- Separate "migration job" pod
- Run before app deployment
- Validate migrations before app starts
- Roll back if migration fails

---

## 🐳 **Docker Compose Migration Strategy**

### **Option A: Entrypoint Script (Recommended)**
```dockerfile
# Dockerfile - Add entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
#!/bin/bash
# docker-entrypoint.sh

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z user-service-db 5432; do
  sleep 1
done

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"
```

### **Option B: Docker Compose Health Check + Migration**
```yaml
# docker-compose.yml
services:
  user-service:
    build: ./user-service
    command: >
      sh -c "
      echo 'Waiting for database...' &&
      while ! nc -z user-service-db 5432; do sleep 1; done &&
      echo 'Running migrations...' &&
      alembic upgrade head &&
      echo 'Starting app...' &&
      uvicorn app.main:app --host 0.0.0.0 --port 8000
      "
    depends_on:
      user-service-db:
        condition: service_healthy
```

### **Option C: Separate Migration Service**
```yaml
# docker-compose.yml
services:
  user-service-migrate:
    build: ./user-service
    command: alembic upgrade head
    depends_on:
      user-service-db:
        condition: service_healthy
    networks:
      - user-service-network
  
  user-service:
    build: ./user-service
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    depends_on:
      - user-service-migrate  # Wait for migrations
    networks:
      - user-service-network
```

---

## ☸️ **Kubernetes Migration Strategy**

### **Option 1: Init Container (Simple)**
```yaml
# k8s/user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  template:
    spec:
      initContainers:
      - name: migrate
        image: user-service:latest
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL_SYNC
          value: "postgresql://postgres:postgres@user-service-db/user_db"
      containers:
      - name: user-service
        image: user-service:latest
        command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Pros**: Simple, runs before app starts  
**Cons**: No rollback if migration fails

### **Option 2: Job + Init Container (Recommended)**
```yaml
# k8s/user-service-migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-migration
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: user-service:latest
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: postgres-credentials
      restartPolicy: Never
  backoffLimit: 3  # Retry 3 times if fails
```

```yaml
# k8s/user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  template:
    spec:
      initContainers:
      - name: wait-for-migration
        image: busybox
        command: ['sh', '-c', 'while ! kubectl get job user-service-migration -o jsonpath="{.status.succeeded}" | grep -q 1; do sleep 5; done']
      containers:
      - name: user-service
        image: user-service:latest
```

### **Option 3: Helm Hook (Advanced)**
```yaml
# Helm chart templates/job-migration.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Chart.Name }}-migration
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        command: ["alembic", "upgrade", "head"]
```

---

## 🛠️ **Implementing Proper Migrations**

### **Step 1: Update Main.py (Remove create_all)**
```python
# app/main.py - Remove or comment out:
# Base.metadata.create_all(bind=sync_engine)  # ❌ Remove this line!
```

### **Step 2: Create Migration Entrypoint Script**
```bash
#!/bin/bash
# user-service/docker-entrypoint.sh

set -e

echo "🔍 Checking database connection..."
max_retries=30
retry_count=0

while ! nc -z ${POSTGRES_HOST} ${POSTGRES_PORT} && [ $retry_count -lt $max_retries ]; do
  echo "⏳ Waiting for database... ($retry_count/$max_retries)"
  sleep 2
  retry_count=$((retry_count+1))
done

if [ $retry_count -eq $max_retries ]; then
  echo "❌ Database not available after $max_retries retries"
  exit 1
fi

echo "✅ Database is ready!"

# Run migrations if requested
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "🚀 Running database migrations..."
  alembic upgrade head
  echo "✅ Migrations completed"
fi

# Start the application
echo "🎯 Starting application..."
exec "$@"
```

### **Step 3: Update Dockerfile**
```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install netcat for database checking
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic.ini ./alembic.ini
COPY alembic/ ./alembic/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Step 4: Update Docker Compose**
```yaml
# docker-compose.yml
services:
  user-service:
    build: ./user-service
    environment:
      RUN_MIGRATIONS: "true"  # Enable migrations
      POSTGRES_HOST: user-service-db
      POSTGRES_PORT: 5432
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 **Migration Strategies Comparison**

| Strategy | Docker Compose | Kubernetes | Pros | Cons |
|----------|----------------|------------|------|------|
| **Entrypoint** | ✅ | ✅ | Simple, automatic | No control, runs every time |
| **Separate Service** | ✅ | ❌ | Clear separation | Complex compose file |
| **Init Container** | ❌ | ✅ | Kubernetes-native | No rollback |
| **Job + Wait** | ❌ | ✅ | Production-ready | Complex setup |
| **Helm Hook** | ❌ | ✅ | Helm integration | Helm required |

---

## 🚀 **Production-Ready Implementation**

### **For Kubernetes (Recommended)**
```yaml
# Structure:
# 1. migration-job.yaml      - Runs alembic upgrade head
# 2. wait-for-migration.yaml - Waits for job completion  
# 3. deployment.yaml         - Starts app after migration
```

### **Step-by-Step Deployment:**
```bash
# 1. Create migration job
kubectl apply -f k8s/migration-job.yaml

# 2. Wait for completion
kubectl wait --for=condition=complete job/user-service-migration --timeout=300s

# 3. Deploy application
kubectl apply -f k8s/deployment.yaml
```

### **Rollback Strategy:**
```yaml
# k8s/rollback-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-rollback
spec:
  template:
    spec:
      containers:
      - name: rollback
        image: user-service:previous-version
        command: ["alembic", "downgrade", "-1"]
```

---

## 🔧 **Migration Best Practices**

### **1. Always Test Migrations First**
```bash
# Dry run
alembic upgrade head --sql

# Test on staging
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### **2. Use Transaction Wrappers**
```python
# alembic/versions/xxx_add_column.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False)
    )
    
def downgrade():
    op.drop_table('new_table')
```

### **3. Handle Data Migrations Carefully**
```python
def upgrade():
    # Add column first
    op.add_column('users', sa.Column('new_field', sa.String(100)))
    
    # Then migrate data
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET new_field = 'default' WHERE new_field IS NULL"
    )
```

### **4. Version Control Migrations**
```bash
# Always generate migration files
alembic revision --autogenerate -m "Add user profile fields"

# Review generated SQL before applying
cat alembic/versions/xxx_add_profile_fields.py
```

---

## ⚠️ **Common Pitfalls & Solutions**

### **Pitfall 1: Concurrent Migrations**
**Problem**: Two pods try to migrate simultaneously  
**Solution**: Use Kubernetes Job (runs once) or database locks

### **Pitfall 2: Failed Migration Blocks Startup**
**Problem**: Migration fails, app never starts  
**Solution**: Separate migration job + health checks

### **Pitfall 3: No Rollback Plan**
**Problem**: Can't revert bad migration  
**Solution**: Always write `downgrade()` functions

### **Pitfall 4: Long-running Migrations**
**Problem**: Migration takes minutes, times out  
**Solution**: Break into smaller migrations, increase timeouts

---

## 📋 **Migration Checklist**

### **Before Deployment:**
- [ ] Test migration locally
- [ ] Generate migration file with `--autogenerate`
- [ ] Review generated SQL
- [ ] Write `downgrade()` function
- [ ] Test rollback

### **During Deployment:**
- [ ] Run migration job
- [ ] Wait for completion
- [ ] Verify schema changes
- [ ] Start application

### **After Deployment:**
- [ ] Monitor application logs
- [ ] Verify data integrity
- [ ] Clean up old migration jobs

---

## 🎯 **Recommended Approach**

### **For This Project:**
1. **Development**: Use entrypoint script in Docker Compose
2. **Staging**: Separate migration service in compose
3. **Production**: Kubernetes Job + Init Container wait

### **Quick Start (Development):**
```bash
# 1. Update main.py to remove create_all
# 2. Create docker-entrypoint.sh
# 3. Update Dockerfile
# 4. Set RUN_MIGRATIONS=true in compose
# 5. docker-compose up --build
```

### **Production (Kubernetes):**
```bash
# 1. Create migration-job.yaml
# 2. Add initContainer to deployment
# 3. Apply job first, wait for completion
# 4. Apply deployment
```

---

## 🔍 **Debugging Migration Issues**

### **Check Database State:**
```bash
# See applied migrations
kubectl exec deploy/user-service -- alembic current

# See migration history
kubectl exec deploy/user-service -- alembic history

# Check database schema
kubectl exec deploy/user-service -- psql -U postgres -d user_db -c "\dt"
```

### **Common Errors:**
```bash
# "Database not ready"
# Solution: Add database readiness check in entrypoint

# "Migration already applied"
# Solution: alembic stamp head

# "Connection refused"
# Solution: Check database service name and port
```

### **Logs to Check:**
```bash
# Migration job logs
kubectl logs job/user-service-migration

# Init container logs
kubectl logs deploy/user-service -c wait-for-migration

# Database logs
kubectl logs deploy/user-service-db
```

---

## 🏁 **Summary**

### **Current State:** ❌
- Uses `create_all()` (development-only)
- No version control
- Data loss risk
- No rollback capability

### **Target State:** ✅
- Alembic migrations
- Version-controlled schema changes
- Safe rollbacks
- Production-ready

### **Migration Path:**
1. Remove `create_all()` from main.py
2. Add entrypoint script with migration option
3. Update Dockerfile and compose
4. For Kubernetes: Add migration job + init container

Choose the right strategy based on your environment, but **always use alembic** instead of `create_all()` for any production deployment!