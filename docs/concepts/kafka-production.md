# Kafka Production Operation

## Current Local Setup

Kafka is managed by Strimzi.

```text
KafkaNodePool
  -> 3 broker/controller pods
  -> persistent volumes
  -> KafkaTopic CRs
  -> replicated partitions
```

Current safety settings:

```text
replication factor: 3
min in-sync replicas: 2
auto topic creation: disabled
normal topic retention: 7 days
DLQ topic retention: 30 days
```

This means every partition has 3 copies. Kafka accepts safe writes while at least 2 replicas are in-sync.

## Local Vs Real Production

Local cluster:

```text
3 Kubernetes nodes
3 Kafka pods
PVCs on local storage
no real availability zones
good for learning broker failure and topic checks
```

Real production:

```text
brokers spread across zones/racks
storage backed by cloud disks or Ceph
rack awareness enabled
alerts for under-replicated partitions and consumer lag
planned partition reassignment before scaling down
backup and disaster recovery tested
```

The main difference is failure domain. In local Kubernetes, nodes may look separate, but they usually share the same machine. In production, brokers must be spread across real zones so one zone failure does not take Kafka down.

## Health Checks

```bash
kubectl get kafka -n kafka
kubectl get kafkatopic -n kafka
kubectl get pods -n kafka
kubectl get pvc -n kafka
```

Topic details:

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --describe
```

Look for:

```text
ReplicationFactor: 3
Isr has 2 or 3 brokers
no under-replicated partitions
```

## Broker Failure Test

Delete one broker pod:

```bash
kubectl delete pod platform-kafka-brokers-0 -n kafka
kubectl get pods -n kafka -w
```

Kafka should recover because Strimzi recreates the pod and the topic replicas still exist on PVC storage.

After recovery:

```bash
kubectl get kafka -n kafka
kubectl exec -n kafka -it platform-kafka-brokers-1 -- \
  /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --describe
```

## Scaling Brokers

Local learning command:

```bash
kubectl patch kafkanodepool brokers -n kafka --type=merge -p '{"spec":{"replicas":4}}'
```

Important: adding a broker does not automatically move old partitions to it. Kafka can have 4 brokers, but old topics may still use the first 3 brokers until a partition reassignment runs.

In real production, scaling means:

```text
add broker
wait for healthy broker
run partition reassignment
verify replication and lag
only then consider scaling down old brokers
```

For this learning project, keep 3 brokers unless we are specifically testing scaling.

## Rack Awareness

Rack awareness tells Kafka:

```text
do not put all replicas in the same failure zone
```

In real production, nodes have labels like:

```text
topology.kubernetes.io/zone=zone-a
topology.kubernetes.io/zone=zone-b
topology.kubernetes.io/zone=zone-c
```

Then Strimzi can use those labels to spread replicas.

In the local cluster, we do not enable rack awareness by default because local node labels do not represent real racks or cloud zones.

## Consumer Lag

Consumer lag means:

```text
messages are in Kafka
but the consumer has not processed them yet
```

Check consumer groups:

```bash
kubectl exec -n kafka -it platform-kafka-brokers-0 -- \
  /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server platform-kafka-kafka-bootstrap:9092 \
  --describe --all-groups
```

High lag means a consumer is slow, down, or failing.

## Apply

```bash
kubectl apply -f k8s/kafka/kafka-cluster.yaml
kubectl apply -f k8s/kafka/topics.yaml
```

