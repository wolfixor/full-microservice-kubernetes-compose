kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml

kubectl create -f https://download.elastic.co/downloads/eck/3.1.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/3.1.0/operator.yaml


kubectl get pods -n elastic-system 

kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/elasticsearch-deployment.yaml

kubectl get pods -n task-api
kubectl get elasticsearch -n task-api


# Kafka / Strimzi event backbone
# first apply namespace, then install Strimzi operator
kubectl apply -f k8s/kafka/namespace.yaml
kubectl create -f https://strimzi.io/install/latest?namespace=kafka -n kafka
kubectl wait deployment/strimzi-cluster-operator -n kafka --for=condition=Available --timeout=300s

# after this you should see only the operator pod first
kubectl get pods -n kafka

# now create the real Kafka cluster and topics
kubectl apply -f k8s/kafka/kafka-cluster.yaml

# wait until Strimzi creates Kafka brokers, PVCs, and services
kubectl get kafka -n kafka
kubectl get pods -n kafka
kubectl get pvc -n kafka
kubectl get svc -n kafka

# create business event topics and dlq topics
kubectl apply -f k8s/kafka/topics.yaml
kubectl get kafkatopic -n kafka

kubectl apply -f user-service/k8s/postgres.yaml
kubectl apply -f task-service/k8s/postgres.yaml
kubectl apply -f comment-service/k8s/postgres.yaml
kubectl apply -f activity-service/k8s/postgres.yaml
kubectl apply -f notification-service/k8s/postgres.yaml

kubectl get pods -n task-api


kubectl apply -f user-service/k8s/migration-job.yaml
kubectl apply -f task-service/k8s/migration-job.yaml
kubectl apply -f comment-service/k8s/migration-job.yaml
kubectl apply -f activity-service/k8s/migration-job.yaml
kubectl apply -f notification-service/k8s/migration-job.yaml

kubectl wait --for=condition=complete job/user-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/task-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/comment-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/activity-service-migrations -n task-api --timeout=300s
kubectl wait --for=condition=complete job/notification-service-migrations -n task-api --timeout=300s


kubectl apply -f user-service/k8s/deployment.yaml
kubectl apply -f task-service/k8s/deployment.yaml
kubectl apply -f comment-service/k8s/deployment.yaml
kubectl apply -f search-service/k8s/deployment.yaml
kubectl apply -f activity-service/k8s/deployment.yaml
kubectl apply -f notification-service/k8s/deployment.yaml

# if user/task/comment images were already running before Kafka env/code changes
kubectl rollout restart deployment/user-service -n task-api
kubectl rollout restart deployment/task-service -n task-api
kubectl rollout restart deployment/comment-service -n task-api


kubectl apply -f kong-gateway/k8s/configmap.yaml
kubectl apply -f kong-gateway/k8s/deployment.yaml
kubectl apply -f kong-gateway/k8s/service.yaml


http://NODE_IP:30085/users
http://NODE_IP:30085/tasks
http://NODE_IP:30085/comments
http://NODE_IP:30085/search?q=test
http://NODE_IP:30086





kubectl apply -f k8s/monitoring/namespace.yaml
# Follow docs/installation/prometheus-operator-install.md to install pinned Prometheus Operator v0.93.0
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml
kubectl apply -f k8s/monitoring/postgres-exporter.yaml
kubectl apply -f k8s/monitoring/redis-exporter.yaml
kubectl apply -f k8s/monitoring/elasticsearch-exporter.yaml
kubectl apply -f k8s/monitoring/node-exporter.yaml
kubectl apply -f k8s/monitoring/kube-state-metrics.yaml
kubectl apply -f k8s/monitoring/service-monitors.yaml
kubectl apply -f k8s/monitoring/prometheus-managed.yaml
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


# Velero local backup stack with YAML
# This uses MinIO as a local S3-compatible backup target.
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backups.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backuprepositories.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_backupstoragelocations.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_deletebackuprequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_downloadrequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_podvolumebackups.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_podvolumerestores.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_restores.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_schedules.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_serverstatusrequests.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v1/bases/velero.io_volumesnapshotlocations.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v2alpha1/bases/velero.io_datadownloads.yaml
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/v1.18.1/config/crd/v2alpha1/bases/velero.io_datauploads.yaml

kubectl apply -f k8s/velero/yaml/namespace.yaml
kubectl apply -f k8s/velero/yaml/minio.yaml
kubectl rollout status deployment/minio -n velero --timeout=300s
kubectl wait --for=condition=complete job/minio-create-velero-bucket -n velero --timeout=300s
kubectl apply -f k8s/velero/yaml/velero-server.yaml
kubectl rollout status deployment/velero -n velero --timeout=300s
kubectl apply -f k8s/velero/yaml/backup-storage-location.yaml
kubectl get backupstoragelocation -n velero

kubectl apply -f k8s/velero/backups/backup-task-api.yaml
kubectl describe backups.velero.io task-api-manual -n velero

kubectl apply -f k8s/velero/backups/schedule-task-api.yaml
kubectl get schedules.velero.io -n velero


mirros:

https://k8s-mirror.liara.ir
https://quay-mirror.liara.ir
