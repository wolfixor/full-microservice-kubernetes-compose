# Kubernetes Alembic Implementation
## How Database Migrations Work in Production Cluster

---

## ☸️ **Kubernetes Migration Philosophy**

### **Key Differences from Docker Compose:**
1. **Stateless containers**: Pods can restart anywhere
2. **Multiple replicas**: Many pods running same service
3. **Zero-downtime deployments**: Rolling updates
4. **Job-based workflows**: Run-to-completion tasks

### **The Problem:**
```yaml
# What we CAN'T do in Kubernetes:
initContainers:
- name: migrate
  image: user-service:latest
  command: ["alembic", "upgrade", "head"]  # ❌ Runs in EVERY pod!
```

**Every pod would try to migrate!** → Race conditions, conflicts!

---

## 🏗️ **Production-Ready Migration Strategies**

### **Strategy 1: Migration Job + Init Container Wait (Recommended)**
```yaml
# 1. migration-job.yaml - Runs once per deployment
# 2. deployment.yaml    - Waits for job, then starts app
```

### **Strategy 2: Helm Pre-Install Hooks**
```yaml
# For Helm users
annotations:
  "helm.sh/hook": pre-install,pre-upgrade
```

### **Strategy 3: External Migration Service**
```yaml
# Separate migration service/operator
# Manages migrations across cluster
```

---

## 🚀 **Implementation: Job + Init Container**

### **Step 1: Create Migration Job**
```yaml
# k8s/user-service-migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-migration
  labels:
    app: user-service
    component: migration
spec:
  ttlSecondsAfterFinished: 86400  # Delete job after 24 hours
  backoffLimit: 3                 # Retry 3 times if fails
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: user-service:latest
        imagePullPolicy: IfNotPresent
        command: ["alembic", "upgrade", "head"]
        env:
        - name: POSTGRES_HOST
          value: "user-service-db"
        - name: POSTGRES_PORT
          value: "5432"
        - name: POSTGRES_DB
          value: "user_db"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: POSTGRES_PASSWORD
```

### **Step 2: Update Deployment to Wait for Job**
```yaml
# k8s/user-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      initContainers:
      - name: wait-for-migration
        image: bitnami/kubectl:latest
        command:
        - /bin/sh
        - -c
        - |
          echo "⏳ Waiting for migration job to complete..."
          until kubectl get job user-service-migration -o jsonpath='{.status.succeeded}' | grep -q 1; do
            echo "Migration not complete, waiting..."
            sleep 5
          done
          echo "✅ Migration completed, starting application..."
        env:
        - name: KUBECONFIG
          value: /tmp/kubeconfig
        volumeMounts:
        - name: kubeconfig
          mountPath: /tmp
          readOnly: true
      containers:
      - name: user-service
        image: user-service:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_HOST
          value: "user-service-db"
        - name: POSTGRES_PORT
          value: "5432"
        - name: POSTGRES_DB
          value: "user_db"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: POSTGRES_PASSWORD
      volumes:
      - name: kubeconfig
        secret:
          secretName: kubeconfig  # You need to create this
```

---

## 🔧 **Simpler Alternative: Shared Volume Lock**

### **Using ConfigMap as Migration Lock:**
```yaml
# k8s/user-service-migration-lock.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-migration-lock
data:
  migrated: "false"
```

### **Updated Migration Job:**
```yaml
# migration-job.yaml - With lock check
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
        command:
        - /bin/sh
        - -c
        - |
          # Check if already migrated
          MIGRATED=$(kubectl get configmap user-service-migration-lock -o jsonpath='{.data.migrated}')
          if [ "$MIGRATED" = "true" ]; then
            echo "✅ Migrations already applied, skipping..."
            exit 0
          fi
          
          echo "🚀 Running migrations..."
          alembic upgrade head
          
          # Mark as migrated
          kubectl patch configmap user-service-migration-lock --type merge -p '{"data":{"migrated":"true"}}'
          echo "✅ Migrations completed and locked"
```

### **Deployment Without kubectl Wait:**
```yaml
# deployment.yaml - Simpler init container
initContainers:
- name: check-migration
  image: busybox
  command: ['sh', '-c', 'for i in $(seq 1 60); do if wget -q -O- http://user-service-migration-lock-svc/check | grep -q "migrated=true"; then exit 0; fi; sleep 5; done; exit 1']
```

---

## 🎯 **Complete Kubernetes Setup**

### **File Structure:**
```
k8s/
├── namespace.yaml
├── secret.yaml
├── redis-deployment.yaml
├── user-service/
│   ├── migration-job.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap-migration-lock.yaml
├── task-service/          # Same structure
└── comment-service/       # Same structure
```

### **Deployment Order:**
```bash
# 1. Create namespace and secrets
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml

# 2. Deploy databases
kubectl apply -f user-service-db-deployment.yaml
kubectl apply -f task-service-db-deployment.yaml
kubectl apply -f comment-service-db-deployment.yaml

# 3. Wait for databases
kubectl wait --for=condition=ready pod -l app=user-service-db --timeout=300s

# 4. Run migrations (ONE TIME)
kubectl apply -f user-service/migration-job.yaml
kubectl wait --for=condition=complete job/user-service-migration --timeout=300s

# 5. Deploy application
kubectl apply -f user-service/deployment.yaml
kubectl apply -f user-service/service.yaml

# 6. Repeat for other services
```

---

## 🔄 **Rolling Update with Migrations**

### **Version 1 → Version 2 Deployment:**
```bash
# 1. Build new image
docker build -t user-service:v2 ./user-service

# 2. Push to registry
docker push registry.example.com/user-service:v2

# 3. Create new migration job for v2
kubectl apply -f user-service/migration-job-v2.yaml

# 4. Wait for migration
kubectl wait --for=condition=complete job/user-service-migration-v2 --timeout=300s

# 5. Update deployment image
kubectl set image deployment/user-service user-service=registry.example.com/user-service:v2

# 6. Monitor rollout
kubectl rollout status deployment/user-service
```

### **Migration Job for v2:**
```yaml
# migration-job-v2.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-migration-v2
  annotations:
    version: "v2"
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: user-service:v2  # New version!
        command: ["alembic", "upgrade", "head"]
```

---

## ⚠️ **Critical Kubernetes Considerations**

### **1. Database Connection in Cluster:**
```yaml
# In Kubernetes, use Service names:
POSTGRES_HOST: user-service-db.task-api.svc.cluster.local
# Or just: user-service-db (Kubernetes DNS resolves)
```

### **2. Secrets Management:**
```yaml
# Store credentials in Secrets, not in configs
env:
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-credentials
      key: POSTGRES_PASSWORD
```

### **3. Resource Limits for Migration Job:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### **4. Migration Timeouts:**
```yaml
# Job timeout
activeDeadlineSeconds: 600  # 10 minutes max

# Backoff for retries
backoffLimit: 3
```

---

## 🧪 **Testing in Kubernetes**

### **Test Migration Job:**
```bash
# Dry run migration
kubectl create job user-service-migration-test --from=cronjob/user-service-migration --dry-run=client -o yaml

# Test connection
kubectl run migration-test --image=user-service:latest --restart=Never --rm -i --tty -- \
  sh -c "alembic upgrade head --sql"

# Check migration status
kubectl exec deploy/user-service -- alembic current
```

### **Verify Database State:**
```bash
# Connect to database pod
kubectl exec -it deploy/user-service-db -- psql -U postgres -d user_db

# Check alembic version table
\dt alembic_version
SELECT * FROM alembic_version;

# Check tables
\dt
```

### **Monitor Migration Logs:**
```bash
# Watch migration job logs
kubectl logs job/user-service-migration -f

# Check init container logs
kubectl logs deploy/user-service -c wait-for-migration

# Check all migration-related pods
kubectl get pods -l job-name=user-service-migration
```

---

## 🔧 **Troubleshooting Kubernetes Migrations**

### **Problem: Job hangs forever**
```bash
# Check job status
kubectl describe job user-service-migration

# Check pod logs
kubectl logs job/user-service-migration

# Check pod events
kubectl describe pod -l job-name=user-service-migration

# Common causes:
# - Database not ready
# - Wrong credentials
# - Network policies blocking
```

### **Problem: "Database connection refused"**
```bash
# Test database connectivity
kubectl run test-db-connect --image=postgres:latest --restart=Never --rm -i --tty -- \
  sh -c "psql -h user-service-db -U postgres -d user_db -c 'SELECT 1'"

# Check database service
kubectl get svc user-service-db

# Check database pods
kubectl get pods -l app=user-service-db
```

### **Problem: Migration already applied**
```bash
# Check current migrations
kubectl exec deploy/user-service-db -- psql -U postgres -d user_db -c "SELECT * FROM alembic_version;"

# Force stamp if needed
kubectl run alembic-stamp --image=user-service:latest --restart=Never --rm -i --tty -- \
  sh -c "alembic stamp head"
```

### **Problem: Multiple jobs conflict**
```bash
# Delete old jobs
kubectl delete job -l app=user-service,component=migration

# Clean up completed jobs automatically
# Add to job spec:
ttlSecondsAfterFinished: 3600  # Delete after 1 hour
```

---

## 🎯 **Production Best Practices**

### **1. Blue-Green Deployment with Migrations:**
```bash
# Blue (current): v1.0
# Green (new): v1.1 with migrations

# 1. Run migrations against Green database
# 2. Switch traffic to Green
# 3. If issues, switch back to Blue
# 4. Run rollback migrations if needed
```

### **2. Database Backups Before Migration:**
```bash
# Backup job
apiVersion: batch/v1
kind: Job
metadata:
  name: user-service-backup
spec:
  template:
    spec:
      containers:
      - name: backup
        image: postgres:latest
        command: ["pg_dump", "-h", "user-service-db", "-U", "postgres", "-d", "user_db", "-f", "/backup/backup.sql"]
```

### **3. Migration Readiness Probe:**
```yaml
# In deployment
readinessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - |
      # Check if migrations are compatible
      alembic current
      # Or check specific table exists
      psql -h localhost -U postgres -d user_db -c "SELECT 1 FROM users LIMIT 1" || exit 1
  initialDelaySeconds: 10
  periodSeconds: 5
```

### **4. Migration Monitoring:**
```yaml
# Prometheus metrics for migrations
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
```

---

## 🚨 **Emergency Rollback Procedure**

### **If Migration Fails:**
```bash
# 1. Stop rollout
kubectl rollout pause deployment/user-service

# 2. Run rollback job
kubectl apply -f user-service-rollback-job.yaml

# 3. Roll back deployment
kubectl rollout undo deployment/user-service

# 4. Resume
kubectl rollout resume deployment/user-service
```

### **Rollback Job:**
```yaml
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
        command: ["alembic", "downgrade", "-1"]  # Roll back one migration
```

---

## 📊 **Migration Strategy Comparison**

| Strategy | Complexity | Safety | Kubernetes Native | Recommended For |
|----------|------------|--------|-------------------|-----------------|
| **Job + Wait** | Medium | High | ✅ | Production |
| **Init Container** | Low | Medium | ✅ | Staging |
| **Helm Hooks** | High | High | ✅ | Helm users |
| **Operator** | High | Highest | ✅ | Large teams |

### **For Your Microservices:**
1. **Development**: Docker Compose with entrypoint
2. **Staging**: Kubernetes Job + simple wait
3. **Production**: Kubernetes Job + ConfigMap lock + monitoring

---

## 🎉 **Summary: Kubernetes Migration Workflow**

### **Deployment Pipeline:**
```
1. Developer: Creates migration file
2. CI/CD: Builds new Docker image
3. CI/CD: Runs migration job
4. CI/CD: Waits for job completion
5. CI/CD: Updates deployment
6. CI/CD: Runs smoke tests
7. Monitor: Watches for issues
8. Rollback: If problems detected
```

### **Key Files to Create:**
1. `migration-job.yaml` - Runs alembic upgrade
2. `deployment.yaml` - Waits for migration
3. `rollback-job.yaml` - Emergency downgrade
4. `backup-job.yaml` - Pre-migration backup

### **Commands to Remember:**
```bash
# Run migration
kubectl apply -f migration-job.yaml
kubectl wait --for=condition=complete job/migration --timeout=300s

# Check status
kubectl logs job/migration
kubectl exec deploy/app -- alembic current

# Rollback if needed
kubectl apply -f rollback-job.yaml
kubectl rollout undo deployment/app
```

---

## 🏁 **Final Recommendation**

### **For Your Project Right Now:**
1. **Keep Docker Compose** as is for development
2. **Add Kubernetes Job** for production deployments
3. **Use simple wait pattern** (Job + kubectl wait)
4. **Always backup** before migrations
5. **Test thoroughly** in staging first

### **Migration Command Cheat Sheet:**
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Run locally
alembic upgrade head
alembic downgrade -1

# Run in Kubernetes
kubectl create job migration-test --image=app:latest -- alembic upgrade head

# Check status
kubectl exec deploy/app -- alembic current
kubectl exec deploy/db -- psql -c "\dt"
```

**Remember**: In Kubernetes, migrations are **jobs**, not part of the app startup. This ensures they run once, safely, before your application pods start. 🎯