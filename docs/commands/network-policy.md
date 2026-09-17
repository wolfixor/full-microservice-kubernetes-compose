# Network Policy Commands

## Check Current CNI

```bash
kubectl get pods -n kube-system
kubectl get daemonset -A | grep -Ei "calico|cilium|flannel|kindnet|weave|cni"
kubectl api-resources | grep -i networkpolicy
```

If no enforcing CNI exists, NetworkPolicy objects may not block traffic.

## Apply Pod Security Audit First

```bash
kubectl apply -f k8s/platform/policy/base/task-api-pod-security.yaml
kubectl get ns task-api --show-labels
```

This warns/audits only. It should not block pods.

## Dry Run Network Policies

```bash
kubectl apply --dry-run=client -f k8s/platform/networking/base/
```

## Safe Apply Order

Apply the allow bundle first, then the deny rule.
Even an allow policy isolates pods once it selects them, so avoid applying one allow file and then waiting.

```bash
kubectl apply \
  -f k8s/platform/networking/base/10-allow-dns-egress.yaml \
  -f k8s/platform/networking/base/20-allow-kong-to-services.yaml \
  -f k8s/platform/networking/base/30-allow-app-dependencies.yaml \
  -f k8s/platform/networking/base/40-allow-elasticsearch-and-logging.yaml \
  -f k8s/platform/networking/base/50-allow-prometheus-scrape.yaml \
  -f k8s/platform/networking/base/60-allow-local-tool-access.yaml

kubectl apply -f k8s/platform/networking/base/00-default-deny-app-workloads.yaml
```

## Check Policies

```bash
kubectl get networkpolicy -n task-api
kubectl describe networkpolicy -n task-api
```

## Test Main API Path

```bash
curl http://localhost:8888/tasks/
curl http://localhost:8888/search/
curl http://localhost:8888/comments/
```

## Debug Blocked Traffic

Check DNS:

```bash
kubectl exec -n task-api deploy/kong-gateway -- nslookup task-service.task-api.svc.cluster.local
```

Check Service and Endpoints:

```bash
kubectl get svc,endpoints -n task-api
kubectl describe svc task-service -n task-api
```

Check pod labels:

```bash
kubectl get pods -n task-api --show-labels
```

Check a dependency path with the same app label as the real workload:

```bash
kubectl run netpol-db-test -n task-api --rm -i --restart=Never \
  --image=busybox:1.36 \
  --labels=app=task-service \
  --command -- sh -c "nc -zvw 5 task-db-pooler-rw 5432"
```

CNPG PgBouncer pods use labels like:

```text
cnpg.io/poolerName=task-db-pooler-rw
```

So Postgres NetworkPolicies must allow that label, not a guessed label like:

```text
app=task-db-pooler
```

Check events:

```bash
kubectl get events -n task-api --sort-by=.lastTimestamp
```

## Intentional Break Drill

Break Kong to services:

```bash
kubectl delete -f k8s/platform/networking/base/20-allow-kong-to-services.yaml
curl http://localhost:8888/tasks/
```

Fix it:

```bash
kubectl apply -f k8s/platform/networking/base/20-allow-kong-to-services.yaml
curl http://localhost:8888/tasks/
```

## Local Kind CNI Recovery

If services randomly time out while their dependencies are healthy, inspect Kindnet:

```bash
kubectl logs -n kube-system -l app=kindnet --tail=100 --prefix=true
```

For local clusters only, rebuild its network rules:

```bash
kubectl rollout restart daemonset/kindnet -n kube-system
kubectl rollout status daemonset/kindnet -n kube-system --timeout=180s
```

In production, investigate the CNI and node networking before restarting it.

## Roll Back All Network Policies

```bash
kubectl delete -f k8s/platform/networking/base/ --ignore-not-found
```

## Production Difference

In production, Calico or Cilium enforces the rules.
On Docker Desktop or kind, enforcement depends on the CNI installed in the local cluster.
