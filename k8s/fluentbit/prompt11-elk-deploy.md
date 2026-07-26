Deploying to Kubernetes
# 1. Apply Fluent Bit (reads all pod logs, enriches, sends to ES)
kubectl apply -f k8s/fluentbit/configmap.yaml
kubectl apply -f k8s/fluentbit/daemonset.yaml

# 2. Deploy Kong log receiver (captures http-log plugin data)
kubectl apply -f kong-gateway/k8s/log-receiver.yaml
kubectl apply -f kong-gateway/k8s/log-endpoint.yaml

# 3. Update Kong config (if already deployed, reload)
kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl rollout restart deployment/kong-gateway -n task-api

# 4. Set up Kibana dashboards (run once after ES/Kibana is ready)
kubectl apply -f k8s/fluentbit/kibana-setup.yaml

# 5. Rollout services to pick up JSON logging
kubectl rollout restart deployment/user-service -n task-api
kubectl rollout restart deployment/task-service -n task-api
kubectl rollout restart deployment/comment-service -n task-api
kubectl rollout restart deployment/search-service -n task-api