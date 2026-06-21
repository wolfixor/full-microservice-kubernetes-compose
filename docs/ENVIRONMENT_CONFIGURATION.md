# Environment Configuration Guide

## Overview
This document explains how environment variables are configured and read in both Docker Compose (development) and Kubernetes (production) environments for the microservices architecture.

## Architecture Principles

### 12-Factor App Compliance
All services follow the [12-Factor App](https://12factor.net/) methodology:
- **Config**: Configuration stored in environment variables
- **Port Binding**: Services export via port binding
- **Concurrency**: Scale via process model
- **Dev/Prod Parity**: Keep development, staging, and production as similar as possible

### Security Principles
- No hardcoded credentials in source code
- Secrets managed via environment variables
- Separate databases per service for isolation
- Different Redis databases for service isolation

## Environment Variable Flow

### 1. Docker Compose (Development)

#### Configuration Sources
```
┌─────────────────────────────────────────┐
│  docker-compose.yml (environment: ...)  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Container Environment Variables        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Pydantic Settings Class                │
│  - Reads from OS environment            │
│  - Falls back to .env file              │
│  - Uses defaults if neither exists      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Application Configuration              │
│  - settings.POSTGRES_HOST               │
│  - settings.REDIS_HOST                  │
│  - etc.                                 │
└─────────────────────────────────────────┘
```

#### Example: User Service in Docker Compose
```yaml
# docker-compose.yml
user-service:
  environment:
    # Database
    POSTGRES_HOST: user-service-db
    POSTGRES_PORT: 5432
    POSTGRES_DB: user_db
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    
    # Redis
    REDIS_HOST: redis           # Shared Redis container
    REDIS_PORT: 6379
    REDIS_DB: 0                 # Database 0 for user service
    REDIS_PASSWORD: ""          # Empty for development
    
    # Application
    HOST: 0.0.0.0
    PORT: 8001
```

#### Pydantic Settings Implementation
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database - empty defaults force env var configuration
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    
    # Redis
    REDIS_HOST: str = "redis-service"  # Default for Kubernetes
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"            # Read from .env file if exists
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()  # Singleton instance
```

#### Priority Order (Docker Compose)
1. **Environment Variables** (from docker-compose.yml) ← Highest Priority
2. **.env file** (local development file)
3. **Default values** (in config.py) ← Lowest Priority

### 2. Kubernetes (Production)

#### Configuration Sources
```
┌─────────────────────────────────────────┐
│  k8s/secret.yaml (encrypted secrets)    │
│  k8s/deployment.yaml (config)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Kubernetes Secret & ConfigMap Objects  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Pod Environment Variables               │
│  - Injected at pod creation             │
│  - Base64 decoded from secrets          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Pydantic Settings Class                │
│  - Same code as Docker Compose          │
│  - Reads from OS environment            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Application Configuration              │
│  - Same code as Docker Compose          │
└─────────────────────────────────────────┘
```

#### Example: Kubernetes Secret
```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  namespace: task-api
type: Opaque
data:
  # Base64 encoded values
  POSTGRES_USER: cG9zdGdyZXM=                # "postgres"
  POSTGRES_PASSWORD: cG9zdGdyZXM=            # "postgres"
  REDIS_PASSWORD: c3VwZXJzZWN1cmU=           # "supersecure"
```

#### Example: Kubernetes Deployment
```yaml
# user-service/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: user-service
        env:
        # Database configuration
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
        
        # Redis configuration
        - name: REDIS_HOST
          value: "redis-service"            # Kubernetes service name
        - name: REDIS_PORT
          value: "6379"
        - name: REDIS_DB
          value: "0"                        # Database 0 for user service
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: REDIS_PASSWORD
        
        # Application configuration
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8001"
```

#### Priority Order (Kubernetes)
1. **Environment Variables** (from deployment.yaml) ← Only Source
2. **Default values** (in config.py) ← Fallback only

## Service-Specific Configuration

### User Service
- **Database**: `user_db` on `user-service-db`
- **Redis**: Database 0
- **Port**: 8001 (dev), 80 via Kong (prod)
- **Key Prefix**: `user:`

### Task Service
- **Database**: `task_db` on `task-service-db`
- **Redis**: Database 1
- **Port**: 8002 (dev), 80 via Kong (prod)
- **Key Prefix**: `task:`

### Comment Service
- **Database**: `comment_db` on `comment-service-db`
- **Redis**: Database 2
- **Port**: 8003 (dev), 80 via Kong (prod)
- **Key Prefix**: `comment:`

## Environment Variables Reference

### Required Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `POSTGRES_HOST` | PostgreSQL hostname | "" | `user-service-db` |
| `POSTGRES_PORT` | PostgreSQL port | 5432 | `5432` |
| `POSTGRES_DB` | Database name | "" | `user_db` |
| `POSTGRES_USER` | Database user | "" | `postgres` |
| `POSTGRES_PASSWORD` | Database password | "" | `postgres` |
| `REDIS_HOST` | Redis hostname | `redis-service` | `redis` (dev) |
| `REDIS_PORT` | Redis port | 6379 | `6379` |
| `REDIS_DB` | Redis database number | 0 | `0`, `1`, `2` |
| `REDIS_PASSWORD` | Redis password | "" | `supersecure` |
| `HOST` | Service bind host | `0.0.0.0` | `0.0.0.0` |
| `PORT` | Service bind port | service-specific | `8001` |

### Optional Variables
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `RUN_MIGRATIONS` | Run DB migrations on startup | `false` | `true` |
| `REDIS_KEY_PREFIX` | Redis key prefix | service-specific | `user:` |
| `CACHE_EXPIRE_SECONDS` | Cache TTL in seconds | 300 | `300` |

## Development Setup

### 1. Using Docker Compose
```bash
# Start all services with default configurations
docker-compose up -d

# Check service logs
docker-compose logs user-service
```

### 2. Local Development (Without Docker)
```bash
# Copy example environment file
cp user-service/.env.example user-service/.env

# Edit .env file with your configuration
# Uncomment appropriate lines for your setup

# Install dependencies
pip install -r requirements.txt

# Run the service
cd user-service
uvicorn app.main:app --reload --port 8001
```

### 3. Creating .env File
```bash
# user-service/.env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=user_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Application
HOST=0.0.0.0
PORT=8001
```

## Production Setup

### 1. Kubernetes Deployment
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (edit secret.yaml first)
kubectl apply -f k8s/secret.yaml

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Deploy services
kubectl apply -f user-service/k8s/
kubectl apply -f task-service/k8s/
kubectl apply -f comment-service/k8s/

# Deploy Kong API Gateway
kubectl apply -f kong-gateway/k8s/
```

### 2. Environment-Specific Configurations
For different environments (staging, production), use:
- Different Kubernetes namespaces
- Different secret files
- Different configuration values in deployment files

## Troubleshooting

### Common Issues

#### 1. Environment Variables Not Being Read
```bash
# Check if environment variables are set in container
docker-compose exec user-service env | grep POSTGRES

# In Kubernetes
kubectl exec -n task-api user-service-pod -- env | grep POSTGRES
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
docker-compose exec user-service-db psql -U postgres -d user_db

# Check database logs
docker-compose logs user-service-db
```

#### 3. Redis Connection Issues
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

#### 4. Service Health Checks
```bash
# Direct service access
curl http://localhost:8001/health
curl http://localhost:8001/ready

# Through Kong API Gateway
KONG_IP=$(kubectl get service kong-gateway -n task-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$KONG_IP/users/health
```

### Debugging Pydantic Settings
```python
# Add debug logging to config.py
import logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # ... fields ...
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"POSTGRES_HOST: {self.POSTGRES_HOST}")
        logger.info(f"REDIS_HOST: {self.REDIS_HOST}")
```

## Best Practices

### 1. Security
- Never commit `.env` files to version control
- Use different passwords for different environments
- Rotate secrets regularly
- Limit secret access with Kubernetes RBAC

### 2. Configuration Management
- Use `.env.example` files as templates
- Keep development and production configurations separate
- Validate environment variables on application startup
- Use descriptive variable names

### 3. Environment-Specific Values
```yaml
# Example: Different Redis hosts per environment
# Development
REDIS_HOST: redis                  # Docker Compose container

# Staging
REDIS_HOST: redis-staging          # Staging Redis service

# Production
REDIS_HOST: redis-production       # Production Redis cluster
```

### 4. Secret Management
```bash
# Generate secure passwords
openssl rand -base64 32

# Base64 encode for Kubernetes secrets
echo -n "supersecurepassword" | base64

# Create Kubernetes secret from file
kubectl create secret generic app-secrets \
  --from-file=postgres-password=./secrets/postgres-password.txt \
  --from-file=redis-password=./secrets/redis-password.txt
```

## Migration Paths

### From Development to Production
1. **Development**: `.env` files or docker-compose.yml
2. **Staging**: Kubernetes ConfigMaps + Secrets (test environment)
3. **Production**: Kubernetes ConfigMaps + Secrets (production environment)

### Scaling Configuration
As the application grows:
1. **Start**: Environment variables in deployment files
2. **Grow**: External configuration (ConfigMaps, external config service)
3. **Scale**: Feature flags, dynamic configuration

## Conclusion

The environment configuration system provides:
- **Consistency**: Same code works in Docker Compose and Kubernetes
- **Security**: No hardcoded credentials, secrets properly managed
- **Flexibility**: Easy to configure for different environments
- **Maintainability**: Clear separation of configuration from code

Both Docker Compose and Kubernetes use the same application code with different environment variable injection methods, ensuring development/production parity while maintaining appropriate security practices for each environment.