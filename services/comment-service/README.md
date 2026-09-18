# Comment Service

A microservice for comment management.

## Features
- CRUD operations for comments
- Health endpoint (`/health`)
- Readiness endpoint (`/ready`)
- Structured logging
- Environment-based configuration

## API Endpoints
- `GET /api/comments` - List all comments
- `GET /api/comments/{id}` - Get a specific comment
- `POST /api/comments` - Create a new comment
- `PUT /api/comments/{id}` - Update a comment
- `DELETE /api/comments/{id}` - Delete a comment

## Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## Docker
```bash
# Build image
docker build -t comment-service .

# Run container
docker run -p 8003:8003 comment-service
```

## Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```