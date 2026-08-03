# CloudNativePG Install

CloudNativePG is the PostgreSQL operator.

It watches PostgreSQL custom resources and creates the real database pods, services, PVCs, replication, failover, and backups.

## Install Operator

```bash
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.30/releases/cnpg-1.30.0.yaml
kubectl wait deployment/cnpg-controller-manager -n cnpg-system --for=condition=Available --timeout=300s
```

## Apply Task Database

```bash
kubectl apply -f task-service/k8s/postgres-cnpg.yaml
kubectl wait cluster/task-db -n task-api --for=condition=Ready --timeout=600s

kubectl apply -f task-service/k8s/pooler.yaml
```

## Check

```bash
kubectl get cluster -n task-api
kubectl get pooler -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | grep task-db
```

## Important

Do not run the old `task-service/k8s/postgres-statefulset-manual.yaml` and the new `task-service/k8s/postgres-cnpg.yaml` for the same service at the same time.

Use one database path:

```text
manual StatefulSet
or
CloudNativePG Cluster
```

If `task-service-db` already contains important data, dump and restore that data into `task-db` before deploying the app against the new pooler service.
