# Kong API Gateway

Kong API Gateway setup for routing requests to microservices.

## Architecture

```
External Requests → Kong Gateway (LoadBalancer) → Internal Microservices (ClusterIP)
```

## Routes Configuration

- `/users` → `user-service`
- `/tasks` → `task-service`
- `/comments` → `comment-service`

## Features

1. **Request Routing**: Routes traffic to appropriate microservices based on path
2. **Rate Limiting**: 60 requests per minute per service
3. **Request Logging**: HTTP log plugin sends logs to Kong's admin endpoint
4. **Correlation IDs**: Adds unique request IDs for tracing

## Kubernetes Deployment

### Apply Kong Gateway

```bash
kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl apply -f kong-gateway/k8s/deployment.yaml
kubectl apply -f kong-gateway/k8s/service.yaml
```

### Or apply all at once

```bash
kubectl apply -f kong-gateway/k8s/
```

## Access Points

- **External API**: `http://<kong-loadbalancer-ip>/` (port 80)
- **Kong Admin**: `http://<kong-loadbalancer-ip>:8001/` (internal only)

## API Endpoints

All endpoints are now routed through Kong:

- `GET /users` → User service
- `GET /tasks` → Task service  
- `GET /comments` → Comment service

## Sample Requests

```bash
# Access through Kong gateway
curl http://<kong-ip>/users
curl http://<kong-ip>/tasks
curl http://<kong-ip>/comments

# Check Kong status
curl http://<kong-ip>:8001/status
```

## Security Notes

1. Only Kong gateway is exposed externally via LoadBalancer
2. All microservices are ClusterIP type (internal only)
3. Rate limiting prevents abuse
4. Request logging provides audit trail