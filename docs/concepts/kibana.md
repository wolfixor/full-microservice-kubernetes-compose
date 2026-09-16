# Kibana Auth Flow

Kibana is only the UI. It does not store logs.

```text
Fluent Bit -> Elasticsearch -> Kibana
```

Kibana needs two things to start cleanly:

```text
Kibana -> Elasticsearch
  needs: ELASTICSEARCH_SERVICEACCOUNTTOKEN

Kibana internal features
  needs: stable encryption keys
```

## Why The Token Exists

`ELASTICSEARCH_SERVICEACCOUNTTOKEN` is used between Kibana and Elasticsearch.

Kibana uses it to call Elasticsearch APIs, create Kibana system indices, read cluster/version info, and manage saved objects.

It is not for Fleet talking to Elasticsearch directly. Fleet runs inside Kibana, so first Kibana itself must be authenticated to Elasticsearch.

## Why The Encryption Keys Exist

Kibana stores sessions, reporting data, alerts, Fleet objects, and saved object secrets.

These need stable keys:

```text
XPACK_SECURITY_ENCRYPTIONKEY
XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY
XPACK_REPORTING_ENCRYPTIONKEY
```

Without them, Kibana may start but `/api/status` can stay unhealthy or Fleet can fail setup.

## Final YAML

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: kibana-encryption-keys
  namespace: task-api
spec:
  secretStoreRef:
    name: vault-task-api
    kind: SecretStore
  target:
    name: kibana-encryption-keys
    creationPolicy: Owner
  data:
  - secretKey: securityEncryptionKey
    remoteRef:
      key: kibana/encryption-keys
      property: securityEncryptionKey
  - secretKey: savedObjectsEncryptionKey
    remoteRef:
      key: kibana/encryption-keys
      property: savedObjectsEncryptionKey
  - secretKey: reportingEncryptionKey
    remoteRef:
      key: kibana/encryption-keys
      property: reportingEncryptionKey

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  namespace: task-api
  labels:
    app: kibana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.arvancloud.ir/kibana:9.4.2
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 5601
        env:
        - name: ELASTICSEARCH_HOSTS
          value: "http://elasticsearch-es-http:9200"
        - name: ELASTICSEARCH_SERVICEACCOUNTTOKEN
          valueFrom:
            secretKeyRef:
              name: kibana-service-token
              key: token
        - name: XPACK_SECURITY_ENCRYPTIONKEY
          valueFrom:
            secretKeyRef:
              name: kibana-encryption-keys
              key: securityEncryptionKey
        - name: XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY
          valueFrom:
            secretKeyRef:
              name: kibana-encryption-keys
              key: savedObjectsEncryptionKey
        - name: XPACK_REPORTING_ENCRYPTIONKEY
          valueFrom:
            secretKeyRef:
              name: kibana-encryption-keys
              key: reportingEncryptionKey
        readinessProbe:
          httpGet:
            path: /api/status
            port: 5601
          initialDelaySeconds: 240
          periodSeconds: 10
```

The real values live in Vault:

```text
secret/kibana/encryption-keys
```

## Check

```bash
kubectl get pod -n task-api -l app=kibana
kubectl logs -n task-api -l app=kibana --tail=50
kubectl get endpoints kibana -n task-api
```

Healthy signs:

```text
Kibana is now available
Fleet setup completed
kibana pod 1/1 Running
```

## If Logs Do Not Show

First check Elasticsearch:

```bash
kubectl exec -n task-api elasticsearch-es-default-0 -- \
  curl -s -u '<elastic-user>:<elastic-password>' http://127.0.0.1:9200/_cat/indices?v
```

If `kubernetes-logs-YYYY.MM.DD` exists, ingestion works.

Then check Kibana data views:

```bash
kubectl exec -n task-api deploy/kibana -- \
  curl -s -u '<elastic-user>:<elastic-password>' -H "kbn-xsrf: true" \
  http://127.0.0.1:5601/api/data_views
```

If it is empty, create:

```text
kubernetes-logs-*
time field: @timestamp
```

Our actual issue was:

```text
Fluent Bit used an old hardcoded elastic password
  -> Elasticsearch rejected _bulk with 401
  -> no log index appeared

After fixing Fluent Bit credentials:
  -> kubernetes-logs-2026.09.13 appeared
  -> Kibana still had no data view
  -> create kubernetes-logs-* data view
```
