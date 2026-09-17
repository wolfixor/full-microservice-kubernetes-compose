# Trivy Operator Commands

## Install

```bash
kubectl apply -f k8s/operators/raw/trivy-operator/namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/trivy-operator/main/deploy/static/trivy-operator.yaml
```

Check:

```bash
kubectl get pods -n trivy-system
kubectl api-resources | grep -E "vulnerabilityreports|configauditreports"
```

## Read Reports

```bash
kubectl get vulnerabilityreports -A
kubectl get configauditreports -A
```

Describe one report:

```bash
kubectl describe vulnerabilityreport -n <namespace> <name>
kubectl describe configauditreport -n <namespace> <name>
```

Raw summary:

```bash
kubectl get vulnerabilityreports -A -o wide
kubectl get configauditreports -A -o wide
```

## Config Audit Drill

Apply an intentionally bad pod:

```bash
kubectl apply -f k8s/security-drills/insecure-pod.yaml
```

Wait for reports:

```bash
kubectl get configauditreports -n task-api
kubectl describe configauditreport -n task-api <report-name>
```

Clean up:

```bash
kubectl delete -f k8s/security-drills/insecure-pod.yaml
```

Expected finding:

```text
privileged container
missing resource requests/limits
```

Fix path:

```text
remove privileged=true
set runAsNonRoot
drop capabilities
add CPU/memory requests and limits
```

## CI/CD Gate Rules

Later in CI/CD:

```text
Critical vulnerability with fix available -> block deployment
High vulnerability with fix available     -> block or require approval
Medium/Low                                -> ticket/backlog
Config critical                           -> block deployment
False positive                            -> documented exception with expiry
```

## False Positive Handling

Every exception needs:

- finding ID
- affected image/workload
- reason it is not exploitable
- owner
- expiry date
- follow-up ticket

Never ignore findings silently.
