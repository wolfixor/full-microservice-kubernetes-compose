use these:
```
kubectl create -f https://download.elastic.co/downloads/eck/3.1.0/crds.yaml
kubectl apply -f https://download.elastic.co/downloads/eck/3.1.0/operator.yaml
```

it need some image and if your server dont have internet you should manualy pull the images so just by this command you will know what images do you need:
`kubectl get deployment -n elastic-system elastic-operator -o yaml | grep image:`

after this pull the image in local and scp to server and after that do this to load the image to the cri of the cluster:
`sudo k3s  ctr -n k8s.io images import /root/elastic.tar`
and by this command check the list image of the cluster:
`k3s ctr images check  | grep elastic`

after that you apply this yml for deploy the elastic search:
`apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: elasticsearch
  namespace: task-api
spec:
  version: 9.4.2
  http:
    tls:
      selfSignedCertificate:
        disabled: true  # Disable TLS/HTTPS
  nodeSets:
  - name: default
    count: 1
    config:
      node.roles: ["master", "data", "ingest"]
      node.store.allow_mmap: false
      xpack.security.enabled: false  # Disable security completely
    podTemplate:
      spec:
        containers:
        - name: elasticsearch
          env:
          - name: ES_JAVA_OPTS
            value: "-Xms1g -Xmx1g"
          resources:
            requests:
              cpu: 500m
              memory: 2Gi
            limits:
              cpu: 1000m
              memory: 2Gi
    volumeClaimTemplates:
    - metadata:
        name: elasticsearch-data
      spec:
        accessModes:
        - ReadWriteOnce
        storageClassName: local-path
        resources:
          requests:
            storage: 10Gi`

you need this image:
`docker.elastic.co/elasticsearch/elasticsearch:9.4.2`