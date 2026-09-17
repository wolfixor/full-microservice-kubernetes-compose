# Kafka Emergency

## Topic Not Found

Symptom:

```text
Topic task.created not found in cluster metadata
```

Meaning:

```text
Kafka is running, but the required KafkaTopic CR/topic is missing or not ready.
```

First commands:

```powershell
kubectl get kafka -n kafka
kubectl get pods -n kafka
kubectl get kafkatopic -n kafka
```

Fix path:

```powershell
kubectl apply -f k8s/platform/messaging/base/topics.yaml
kubectl get kafkatopic -n kafka
```

Restart producer if metadata stays stale:

```powershell
kubectl patch rollout task-service -n task-api --type merge `
  -p '{"spec":{"restartAt":"2026-08-10T00:00:00Z"}}'
```

## Check Topic Data

```powershell
kubectl exec -n kafka -it platform-kafka-brokers-0 -- `
  /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 `
  --topic task.created `
  --from-beginning
```

## Consumer Lag

```powershell
kubectl exec -n kafka -it platform-kafka-brokers-0 -- `
  /opt/kafka/bin/kafka-consumer-groups.sh `
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 `
  --describe --all-groups
```

Read output:

```text
LAG > 0 and growing -> consumer is behind
consumer missing    -> service may not be running or group id changed
```
