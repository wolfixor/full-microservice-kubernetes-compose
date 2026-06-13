# User Service

A microservice for user management.

## Features
- CRUD operations for users
- Health endpoint (`/health`)
- Readiness endpoint (`/ready`)
- Structured logging
- Environment-based configuration

## API Endpoints
- `GET /api/users` - List all users
- `GET /api/users/{id}` - Get a specific user
- `POST /api/users` - Create a new user
- `PUT /api/users/{id}` - Update a user
- `DELETE /api/users/{id}` - Delete a user

## Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Docker
```bash
# Build image
docker build -t user-service .

# Run container
docker run -p 8001:8001 user-service
```

## Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```