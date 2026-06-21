# Redis Caching Infrastructure for Microservices

This directory contains Redis configuration and deployment manifests.

## Architecture
- Redis deployed as a StatefulSet for persistence
- Each service has its own Redis configuration
- Cache-aside pattern implementation
- Health checks and monitoring

## Services Connection
- user-service: redis://redis-service:6379/0
- task-service: redis://redis-service:6379/1  
- comment-service: redis://redis-service:6379/2

## Cache Keys
- user-service: user:{user_id}
- task-service: task:{task_id}
- comment-service: comment:{comment_id}