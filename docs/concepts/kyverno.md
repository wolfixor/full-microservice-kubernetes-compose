# Kyverno

## What It Does

Kyverno is a Kubernetes policy engine.

```text
kubectl apply
  -> Kubernetes API server
  -> Kyverno admission webhook
  -> allow, warn/audit, or reject
```

It checks Kubernetes objects before or after they enter the cluster.

## Audit Vs Enforce

Audit:

```text
accept the object
record policy violation
teach teams what will break later
```

Enforce:

```text
reject the object immediately
```

Production should start with audit, fix noisy rules, then promote selected rules to enforce.

Real lab:

```text
bad pod apply
  -> API server calls Kyverno webhook
  -> audit policy finds 4 failures
  -> pod is still created
  -> PolicyReport and Events show the violations
```

Then:

```text
enforce no-privileged policy
  -> bad pod apply
  -> API server calls Kyverno webhook
  -> Kyverno rejects privileged=true
  -> pod is not created
```

That is the main difference:

```text
audit = teach and observe
enforce = block
```

## Kyverno Vs NetworkPolicy

NetworkPolicy controls runtime traffic:

```text
can pod A connect to pod B?
```

Kyverno controls Kubernetes object admission:

```text
is this manifest allowed into the cluster?
```

## Kyverno Vs Trivy

Trivy finds risk:

```text
this running workload has bad config or vulnerable packages
```

Kyverno prevents risk:

```text
do not allow this unsafe manifest to be created
```

## Policy Rollout Rule

Safe production flow:

```text
1. audit mode
2. read policy reports
3. fix real workloads
4. document exceptions
5. enforce only low-noise rules
6. monitor rejected deploys
```

Good production pattern:

```text
broad platform baseline
  -> audit first

dangerous low-noise rules
  -> enforce after testing
```

Example:

```text
labels/resources/probes
  -> audit until teams fix manifests

privileged containers
  -> enforce earlier because it is high risk
```

Every policy needs:

- owner
- reason
- severity
- exception process
- rollback path

## Install Note

Kyverno has large CRDs.

Normal client-side apply can fail because kubectl stores the full previous object in this annotation:

```text
kubectl.kubernetes.io/last-applied-configuration
```

For large CRDs, that annotation can become too big.

Use server-side apply for Kyverno:

```text
kubectl apply --server-side
```

Flow:

```text
server-side apply
  -> API server manages field ownership
  -> CRDs install cleanly
  -> Kyverno admission controller can start
```
