# Trivy Operator

## What It Does

Trivy Operator scans Kubernetes workloads and writes findings back into Kubernetes CRs.

```text
workload runs in cluster
  -> Trivy Operator notices it
  -> scan job runs
  -> VulnerabilityReport / ConfigAuditReport is created
  -> DevOps reads finding and creates fix path
```

## Operator Vs CLI

Trivy CLI:

```text
run scan manually or in CI
```

Trivy Operator:

```text
keeps scanning what is actually running in Kubernetes
```

Production usually needs both:

- CI scan before image is deployed
- operator scan for runtime visibility and drift

## Report Types

`VulnerabilityReport`:

```text
image has vulnerable packages or libraries
```

`ConfigAuditReport`:

```text
Kubernetes manifest has unsafe config
```

Examples:

- privileged container
- missing resource limits
- running as root
- old image with known CVEs

## Severity Vs Exploitability

Severity means how bad the vulnerability can be.
Exploitability means whether it is realistically reachable in this app.

Do not blindly page on every CVE.

Production flow:

```text
critical exploitable finding -> urgent fix
critical not reachable       -> ticket with evidence
medium/low                   -> normal backlog or base image refresh
false positive               -> documented exception with expiry
```
