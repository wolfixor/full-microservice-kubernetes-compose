# Start Here

Use this page when you forgot the project or something is broken.

## Production Rules

- No downtime by default for anything already serving users.
- Raw YAML is for learning, bootstrap, local labs, debugging, and emergency drills.
- Production direction is Git commit -> CI validation -> Helm/Kustomize render -> Argo CD sync -> operators reconcile.
- Before changing data or live services: check health, back up, diff, roll out slowly, watch metrics/logs/events, verify behavior, keep rollback ready.

## Command Docs

- [Architecture Current State](architecture/current-state.md): what exists in the cluster now.
- [Apply Flow](architecture/apply-flow.md): what reacts after `kubectl apply`.
- [CRD Map](architecture/crd-map.md): custom resources and their operators.
- [Kubernetes Manifest Syntax](concepts/kubernetes-manifest-syntax.md): YAML syntax, selectors, RBAC, NetworkPolicy.
- [Production IaC](concepts/production-iac.md): Helm, Kustomize, GitOps, environments, migration rules.
- [PostgreSQL](commands/postgresql.md): backup, WAL, restore, slow queries, locks, replication.
- [Kafka](commands/kafka.md): missing topics, consumer lag, DLQ, broker health.
- [Redis](commands/redis.md): cluster health, cache failures, key checks.
- [Elasticsearch](commands/elasticsearch.md): ES pending, Kibana/search down.
- [Kibana](concepts/kibana.md): Kibana token, encryption keys, readiness flow.
- [Argo CD](commands/argocd.md): GitOps install, sync, health, drift, rollback.
- [Kubernetes](commands/kubernetes.md): pods pending, crashloop, services, events.
- [Network Policy](commands/network-policy.md): CNI checks, allowed/blocked traffic, rollback.
- [Alertmanager](commands/alertmanager.md): alert checks, runbooks, silences, drills.
- [Trivy Operator](commands/trivy-operator.md): vulnerability reports, config audit reports, remediation flow.
- [Kyverno](commands/kyverno.md): admission policies, audit/enforce mode, rejected deployment debugging.
- [Vault](commands/vault.md): Kubernetes auth, Vault policies, secret read flow.
- [External Secrets Operator](commands/external-secrets.md): sync Vault secrets into Kubernetes Secrets.
- [Production IaC Commands](commands/production-iac.md): render, diff, apply, rollback commands.

## Main Flow

```text
Concepts  -> understand the system
Commands  -> run/check/debug/config
```

## GitOps Direction

```text
Git commit
  -> Argo CD sees desired state
  -> Argo CD syncs Kubernetes manifests
  -> operators reconcile CRDs
  -> Argo Rollouts handles progressive app release
```
