# Strimzi Operator Install

Install Strimzi before applying the Kafka cluster resources:

```bash
kubectl create namespace kafka
kubectl create -f https://strimzi.io/install/latest?namespace=kafka -n kafka
kubectl wait deployment/strimzi-cluster-operator -n kafka --for=condition=Available --timeout=300s
```

Then apply the local Kafka resources:

```bash
kubectl apply -f k8s/kafka/kafka-cluster.yaml
kubectl apply -f k8s/kafka/topics.yaml
```

The internal bootstrap address used by services is:

```text
platform-kafka-kafka-bootstrap.kafka.svc:9092
```
