# Install Elasticsearch With ECK

Install the ECK operator first:

```bash
kubectl apply -f https://download.elastic.co/downloads/eck/3.1.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/3.1.0/operator.yaml
kubectl wait deployment/elastic-operator -n elastic-system --for=condition=Available --timeout=300s
```

Then create Elasticsearch:

```bash
kubectl apply -f k8s/elasticsearch-deployment.yaml
kubectl wait elasticsearch/elasticsearch -n task-api --for=condition=ReconciliationComplete --timeout=600s
```

Check:

```bash
kubectl get elasticsearch -n task-api
kubectl get pods -n task-api -l elasticsearch.k8s.elastic.co/cluster-name=elasticsearch
kubectl get svc -n task-api | grep elasticsearch
```

The service used by apps is:

```text
elasticsearch-es-http.task-api.svc.cluster.local:9200
```

