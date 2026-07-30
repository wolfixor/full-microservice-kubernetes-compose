# Test Kafka

## 1. Check Cluster

```bash
kubectl get pods -n kafka
kubectl get kafka -n kafka
kubectl get kafkatopic -n kafka
kubectl get svc -n kafka
```

Expected: operator plus 3 broker pods.

## 2. List Topics

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --list
```

Expected: business topics and `.dlq` topics.

## 3. Produce Message

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --topic task.created
```

Type one message:

```json
{"id":"task-1","title":"hello kafka"}
```

## 4. Consume Message

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --topic task.created \
  --from-beginning
```

Expected: the message from step 3.

## 5. Test App Event

```bash
curl -X POST http://NODE_IP:30085/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Kafka test","description":"event test","user_id":"u1"}'
```

Then consume `task.created` again. Expected: a JSON event from `task-service`.

## 6. Deploy Search Consumer

```bash
docker build -t registry.gitlab.shiveh.com/mapir/upstream/kibana:search-service ./search-service
docker push registry.gitlab.shiveh.com/mapir/upstream/kibana:search-service

kubectl apply -f search-service/k8s/deployment.yaml
kubectl rollout restart deployment/search-service -n task-api
```

## 7. Test Search Consumer

After the task event is created, search should read it from Kafka and index it in Elasticsearch:

```bash
curl "http://NODE_IP:30085/search?q=Kafka"
```

Expected: the task appears in search results.

## 8. Test Activity Consumer

The same event should also be stored by `activity-service`:

```bash
curl "http://NODE_IP:30085/activities?event_type=task.created"
```

Expected: the `task.created` event appears in activity results.

## 9. Test Notification Consumer

The same event should also create a notification:

```bash
curl "http://NODE_IP:30085/notifications?type=task_created"
```

Expected: a notification for the created task appears.
