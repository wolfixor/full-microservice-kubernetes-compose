kubectl rollout restart statefulset/comment-service-db   statefulset/task-service-db  statefulset/user-service-db -n task-api

kubectl rollout   restart deployment/comment-service  deployment/task-service  deployment/user-service  deployment/redis deployment/search-service  -n task-api