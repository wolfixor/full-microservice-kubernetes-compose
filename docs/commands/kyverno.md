# Kyverno Commands

## Install

```bash
kubectl apply -f k8s/operators/raw/kyverno/namespace.yaml
kubectl apply --server-side -f https://github.com/kyverno/kyverno/releases/download/v1.19.1/install.yaml
```

Check:

```bash
kubectl get pods -n kyverno
kubectl api-resources | grep -E "clusterpolicies|policyreports"
```

If `clusterpolicies` is missing, do not apply policy YAML yet. Install Kyverno CRDs first.

If CRD install fails with `metadata.annotations: Too long`, use server-side apply:

```bash
kubectl apply --server-side --force-conflicts -f https://github.com/kyverno/kyverno/releases/download/v1.19.1/install.yaml
kubectl rollout restart deployment/kyverno-admission-controller -n kyverno
```

## Apply Audit Policies

```bash
kubectl apply -f k8s/platform/policy/base/audit-baseline.yaml
```

Check:

```bash
kubectl get clusterpolicy
kubectl describe clusterpolicy platform-audit-baseline
```

Note: `kyverno.io/v1 ClusterPolicy` works for this lab, but newer Kyverno versions warn that it is deprecated. Production should later migrate policies to the newer `policies.kyverno.io` resources.

## Audit Drill

Apply a bad pod:

```bash
kubectl apply -f k8s/security-drills/kyverno-bad-pod.yaml
```

In audit mode, it should be accepted but reported.

Check:

```bash
kubectl get policyreports -A
kubectl get policyreports -n task-api | grep kyverno
kubectl get events -n task-api --sort-by=.lastTimestamp
```

Expected result:

```text
kyverno-bad-pod   PASS 0   FAIL 4
```

The bad pod is created, but Kyverno reports violations:

```text
missing team/version labels
privileged container
missing CPU/memory requests and limits
missing liveness/readiness probes
```

Clean up:

```bash
kubectl delete -f k8s/security-drills/kyverno-bad-pod.yaml
```

## Good Pod Drill

```bash
kubectl apply -f k8s/security-drills/kyverno-good-pod.yaml
kubectl get policyreports -n task-api | grep kyverno-good-pod
kubectl delete -f k8s/security-drills/kyverno-good-pod.yaml
```

Expected result:

```text
kyverno-good-pod   PASS 3   FAIL 0
```

## Enforce Drill

Only after audit behavior is understood:

```bash
kubectl apply -f k8s/platform/policy/base/enforce-no-privileged.yaml
kubectl apply -f k8s/security-drills/kyverno-bad-pod.yaml
```

Expected result:

```text
admission webhook "validate.kyverno.svc-fail" denied the request
Privileged containers are blocked in task-api.
```

Rollback:

```bash
kubectl delete -f k8s/platform/policy/base/enforce-no-privileged.yaml
```

This enforce policy is intentionally separate from the broad audit baseline. Keep broad standards in audit first, then enforce one low-noise dangerous rule at a time.

## Debug Rejected Deployments

```bash
kubectl describe clusterpolicy <policy-name>
kubectl get events -n <namespace> --sort-by=.lastTimestamp
kubectl logs -n kyverno -l app.kubernetes.io/part-of=kyverno --tail=120
```

For a rejected deploy, read the webhook error first. It usually tells you:

```text
policy name
rule name
failed field path
message
```

Fix path:

```text
read denied rule
fix manifest
or request documented exception
```

## Exception Process

Every exception needs:

- policy name
- workload and namespace
- owner/team
- reason
- expiry date
- safer long-term fix

## Client-Side Vs Server-Side Apply

Client-side apply:

```text
kubectl apply -f file.yaml
  -> kubectl stores last applied YAML in an annotation
  -> large CRDs can fail because annotation size is limited
```

Server-side apply:

```text
kubectl apply --server-side -f file.yaml
  -> Kubernetes API server manages field ownership
  -> safer for large CRDs like Kyverno
```

For Kyverno install and upgrade, use server-side apply.
