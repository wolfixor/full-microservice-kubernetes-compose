# Search Service

Elasticsearch-based search service for task and comment search.

## Purpose
- Full-text search across tasks and comments
- Elasticsearch as storage backend
- REST API for search operations

## API Endpoints

### Search
```
GET /api/search?q={query}&size={size}
```
Search for tasks and comments by query.

### Index Document
```
POST /api/search/index
```
Index a document for search (for event ingestion simulation).

### Delete Document
```
DELETE /api/search/{document_id}
```
Remove a document from search index.

## Data Model

### Search Document
```json
{
  "id": "string",
  "type": "task|comment",
  "title": "string",
  "content": "string",
  "user_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "metadata": {}
}
```

### Task Document
```json
{
  ...SearchDocument fields,
  "status": "string",
  "description": "string"
}
```

### Comment Document
```json
{
  ...SearchDocument fields,
  "task_id": "string"
}
```

## Health Endpoints
- `/health` - Service health check
- `/ready` - Readiness check with Redis connectivity

## Configuration
Environment variables in `.env.example`:
- `ELASTICSEARCH_HOST`, `ELASTICSEARCH_PORT`
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
- Service URLs for simulated event ingestion

## Deployment

### Build Docker Image
```bash
docker build -t search-service .
```

### Kubernetes Deployment
See `k8s/` directory for manifests.

### Integration
- Subscribes to task and comment events (simulated via HTTP for now)
- Elasticsearch index initialized on startup
- Redis caching for search results