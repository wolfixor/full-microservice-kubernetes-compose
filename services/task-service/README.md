# Task Service

A microservice for task management.

## Features
- CRUD operations for tasks
- Health endpoint (`/health`)
- Readiness endpoint (`/ready`)
- Structured logging
- Environment-based configuration

## API Endpoints
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{id}` - Get a specific task
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/{id}` - Update a task
- `DELETE /api/tasks/{id}` - Delete a task

## Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Docker
```bash
# Build image
docker build -t task-service .

# Run container
docker run -p 8002:8002 task-service
```

## Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```