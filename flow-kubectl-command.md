kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml

kubectl create -f https://download.elastic.co/downloads/eck/3.1.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/3.1.0/operator.yaml


kubectl get pods -n elastic-system 

kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/elasticsearch-deployment.yaml

kubectl get pods -n task-api
kubectl get elasticsearch -n task-api

kubectl apply -f user-service/k8s/postgres.yaml
kubectl apply -f task-service/k8s/postgres.yaml
kubectl apply -f comment-service/k8s/postgres.yaml

kubectl get pods -n task-api


kubectl apply -f user-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f comment-service/k8s/migration-job.yaml

kubectl wait --for=condition=complete job/user-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/task-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/comment-service-migrations -n task-api --timeout=300s


kubectl apply -f user-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/deployment.yaml
kubectl apply -f comment-service/k8s/deployment.yaml
kubectl apply -f search-service/k8s/deployment.yaml


kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl apply -f kong-gateway/k8s/deployment.yaml
kubectl apply -f kong-gateway/k8s/service.yaml


http://NODE_IP:30085/users
http://NODE_IP:30085/tasks
http://NODE_IP:30085/comments
http://NODE_IP:30085/search?q=test
http://NODE_IP:30086





kubectl apply -f k8s/monitoring/namespace.yaml
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml
kubectl apply -f k8s/monitoring/postgres-exporter.yaml
kubectl apply -f k8s/monitoring/redis-exporter.yaml
kubectl apply -f k8s/monitoring/elasticsearch-exporter.yaml
kubectl apply -f k8s/monitoring/node-exporter.yaml
kubectl apply -f k8s/monitoring/kube-state-metrics.yaml
kubectl apply -f k8s/monitoring/prometheus-config.yaml
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-dashboards.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml



kubectl apply -f k8s/kibana-deployment.yaml
kubectl apply -f k8s/fluentbit/configmap.yaml
kubectl apply -f k8s/fluentbit/daemonset.yaml
kubectl apply -f kong-gateway/k8s/log-receiver.yaml
kubectl apply -f kong-gateway/k8s/log-endpoint.yaml
kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl rollout restart deployment/kong-gateway -n task-api
kubectl apply -f k8s/fluentbit/kibana-setup.yaml


mirros:

https://k8s-mirror.liara.ir
