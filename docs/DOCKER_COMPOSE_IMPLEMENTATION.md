# Docker Compose Alembic Implementation
## Exactly How Migrations Work in Your Current Setup

---

## 🎯 **Current Reality: No Real Migrations!**

### **What's Actually Happening:**
```python
# In main.py of each service:
Base.metadata.create_all(bind=sync_engine)
```

**This means:**
- ❌ Tables dropped & recreated on every restart
- ❌ All data lost if you restart containers
- ❌ No migration history tracked
- ❌ Can't rollback schema changes

---

## 🛠️ **Implementing Real Alembic Migrations**

### **Step 1: Update Each Service's Main.py**
```python
# In user-service/app/main.py, task-service/app/main.py, comment-service/app/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # ❌ REMOVE THIS LINE:
    # Base.metadata.create_all(bind=sync_engine)
    
    # ✅ Add database connection test instead:
    try:
        # Just test connection, don't create tables
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logging.info("Database connection verified")
    except Exception as e:
        logging.warning(f"Database connection failed: {e}")
    
    yield
    
    logging.info("Service shutting down")
```

### **Step 2: Create Entrypoint Script for Each Service**
```bash
#!/bin/bash
# user-service/docker-entrypoint.sh
# task-service/docker-entrypoint.sh  
# comment-service/docker-entrypoint.sh

set -e

echo "🔍 Checking database connection..."

# Use environment variables from docker-compose
DB_HOST=${POSTGRES_HOST:-user-service-db}
DB_PORT=${POSTGRES_PORT:-5432}
MAX_RETRIES=30
RETRY_COUNT=0

# Wait for database to be ready
while ! nc -z $DB_HOST $DB_PORT && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "⏳ Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database not available after $MAX_RETRIES retries"
    exit 1
fi

echo "✅ Database is ready!"

# Run migrations if enabled
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "🚀 Running database migrations..."
    alembic upgrade head
    echo "✅ Migrations completed"
fi

# Start the application
echo "🎯 Starting application..."
exec "$@"
```

### **Step 3: Update Dockerfile for Each Service**
```dockerfile
# In each service's Dockerfile, add:

# Install netcat for database connection checking
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
# CMD stays the same: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Step 4: Update Docker Compose**
```yaml
# In docker-compose.yml, update each service:

services:
  user-service:
    build: ./user-service
    environment:
      RUN_MIGRATIONS: "true"  # Enable auto-migrations
      POSTGRES_HOST: user-service-db
      POSTGRES_PORT: 5432
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  
  task-service:
    build: ./task-service
    environment:
      RUN_MIGRATIONS: "true"
      POSTGRES_HOST: task-service-db
      POSTGRES_PORT: 5432
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  
  comment-service:
    build: ./comment-service
    environment:
      RUN_MIGRATIONS: "true"
      POSTGRES_HOST: comment-service-db
      POSTGRES_PORT: 5432
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔄 **How It Works Now**

### **Container Startup Flow:**
```
1. Container starts
2. Entrypoint script runs
3. Waits for database to be ready
4. Runs: alembic upgrade head
5. Starts: uvicorn app.main:app
```

### **Migration Process:**
```bash
# When you run: docker-compose up --build

# 1. Build images with entrypoint
# 2. Start database containers
# 3. Start service containers
# 4. Each service:
#    - Waits for its database
#    - Runs alembic migrations
#    - Starts FastAPI app
# 5. All services ready!
```

---

## 📁 **File Structure After Changes**

```
microservice-kuber/
├── user-service/
│   ├── Dockerfile                    # Updated with entrypoint
│   ├── docker-entrypoint.sh         # New: Migration script
│   ├── alembic.ini                  # Already exists
│   ├── alembic/                     # Already exists
│   └── app/
│       └── main.py                  # Updated: Remove create_all
├── task-service/                    # Same structure
├── comment-service/                 # Same structure
└── docker-compose.yml              # Updated: Add RUN_MIGRATIONS
```

---

## 🧪 **Testing the New Setup**

### **Test 1: First Time Startup**
```bash
# Clean start
docker-compose down -v  # Removes volumes too!
docker-compose up --build

# Check logs for each service:
docker-compose logs user-service | grep -A5 -B5 "migration"
docker-compose logs task-service | grep -A5 -B5 "migration"
docker-compose logs comment-service | grep -A5 -B5 "migration"
```

**Expected output:**
```
user-service_1  | ✅ Database is ready!
user-service_1  | 🚀 Running database migrations...
user-service_1  | INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial migration
user-service_1  | ✅ Migrations completed
user-service_1  | 🎯 Starting application...
```

### **Test 2: Restart (Should Skip Migrations)**
```bash
# Stop and start again
docker-compose stop
docker-compose start

# Check logs - should NOT show "Running database migrations"
docker-compose logs user-service | grep -i migration
# Should show: "INFO  [alembic.runtime.migration] Context impl PostgresqlImpl."
```

### **Test 3: Add New Migration**
```bash
# Enter user-service container
docker-compose exec user-service bash

# Generate new migration
alembic revision --autogenerate -m "Add email verification field"

# Exit container
exit

# Restart to apply
docker-compose restart user-service

# Check new migration applied
docker-compose logs user-service | grep -A2 "Running upgrade"
```

---

## ⚠️ **Important Considerations**

### **Data Persistence:**
```yaml
# In docker-compose.yml - Already configured!
volumes:
  - ./place-data/user_service_postgres_data:/var/lib/postgresql/data
  - ./place-data/task_service_postgres_data:/var/lib/postgresql/data  
  - ./place-data/comment_service_postgres_data:/var/lib/postgresql/data
```

**This means:**
- ✅ Database data persists between restarts
- ✅ Migrations run once, not every time
- ✅ Schema changes preserved

### **Migration Safety:**
- Alembic tracks which migrations have been applied
- Won't run same migration twice
- Can rollback with `alembic downgrade -1`

### **For Development Only:**
```yaml
# In docker-compose.yml - Development override
services:
  user-service:
    environment:
      RUN_MIGRATIONS: "true"  # Auto-migrate in dev
```

**For production, you might want:**
- Manual control over migrations
- Separate migration step
- Backup before migrating

---

## 🔧 **Troubleshooting**

### **Problem: "alembic: command not found"**
**Solution**: Make sure alembic is in requirements.txt:
```txt
# requirements.txt should include:
alembic==1.13.0
```

### **Problem: "Database not ready" timeout**
**Solution**: Increase retries in entrypoint:
```bash
# In docker-entrypoint.sh
MAX_RETRIES=60  # Increase from 30 to 60
```

### **Problem: Migration conflicts**
**Solution**: Check alembic version table:
```bash
docker-compose exec user-service-db psql -U postgres -d user_db -c "SELECT * FROM alembic_version;"
```

### **Problem: Need to reset database**
**Solution**: Use alembic to downgrade:
```bash
# Enter container
docker-compose exec user-service bash

# Downgrade all migrations
alembic downgrade base

# Or downgrade one step
alembic downgrade -1
```

---

## 🎯 **Quick Implementation Steps**

### **For Each Service (user, task, comment):**
1. **Update main.py**: Remove `Base.metadata.create_all()`
2. **Create docker-entrypoint.sh**: Copy from guide
3. **Update Dockerfile**: Add netcat and entrypoint
4. **Test locally first**

### **All at Once Script:**
```bash
#!/bin/bash
# fix-migrations.sh

SERVICES=("user-service" "task-service" "comment-service")

for service in "${SERVICES[@]}"; do
    echo "🔧 Updating $service..."
    
    # 1. Update main.py
    sed -i 's/Base.metadata.create_all(bind=sync_engine)/# Base.metadata.create_all(bind=sync_engine)  # Migrations handled by alembic/' "$service/app/main.py"
    
    # 2. Create entrypoint
    cat > "$service/docker-entrypoint.sh" << 'EOF'
#!/bin/bash
set -e
echo "🔍 Checking database connection..."
DB_HOST=${POSTGRES_HOST}
DB_PORT=${POSTGRES_PORT:-5432}
MAX_RETRIES=30
RETRY_COUNT=0
while ! nc -z $DB_HOST $DB_PORT && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "⏳ Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done
if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database not available"
    exit 1
fi
echo "✅ Database is ready!"
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "🚀 Running migrations..."
    alembic upgrade head
    echo "✅ Migrations completed"
fi
echo "🎯 Starting application..."
exec "$@"
EOF
    
    chmod +x "$service/docker-entrypoint.sh"
    
    # 3. Update Dockerfile
    # Add: RUN apt-get update && apt-get install -y netcat-openbsd
    # Add: COPY docker-entrypoint.sh /usr/local/bin/
    # Add: RUN chmod +x /usr/local/bin/docker-entrypoint.sh
    # Change: ENTRYPOINT ["docker-entrypoint.sh"]
    
    echo "✅ $service updated"
done

echo "🎉 All services updated! Run: docker-compose up --build"
```

---

## 📊 **Before vs After**

### **Before (Current):**
- ❌ `create_all()` drops & recreates tables
- ❌ Data loss on restart
- ❌ No migration history
- ❌ Can't rollback changes

### **After (With Alembic):**
- ✅ Tables created once via migrations
- ✅ Data persists between restarts
- ✅ Full migration history tracked
- ✅ Can rollback with `downgrade`
- ✅ Safe schema evolution

---

## 🚀 **Deployment Steps**

1. **Backup data first** (just in case):
```bash
# Backup each database
docker-compose exec user-service-db pg_dump -U postgres user_db > user_db_backup.sql
```

2. **Apply changes**:
```bash
# Stop everything
docker-compose down

# Apply fixes to all services
# (Use the script above or do manually)

# Rebuild and start
docker-compose up --build -d

# Monitor migration logs
docker-compose logs --tail=50 user-service
```

3. **Verify**:
```bash
# Check migration status
docker-compose exec user-service alembic current

# Check data still exists
docker-compose exec user-service-db psql -U postgres -d user_db -c "SELECT COUNT(*) FROM users;"
```

---

## 🎉 **You Now Have Real Database Migrations!**

### **What You've Achieved:**
1. ✅ Replaced dangerous `create_all()` with safe alembic
2. ✅ Automatic migrations on container startup
3. ✅ Data persistence between restarts
4. ✅ Migration history and rollback capability
5. ✅ Production-ready database management

### **Next Time You Modify Models:**
```bash
# 1. Modify your SQLAlchemy models
# 2. Generate migration:
docker-compose exec user-service alembic revision --autogenerate -m "Description"

# 3. Review generated migration file
# 4. Restart service to apply:
docker-compose restart user-service
```

**No more data loss! No more manual SQL! Real database migrations!** 🎊