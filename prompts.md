## Prompt 1

I want to build a production-style learning project that will gradually evolve into a distributed microservices system deployed on Kubernetes.

Status:

- completed as the first learning foundation
- later replaced by FastAPI microservices and the wider platform stack
- keep as historical context, not the current runtime architecture

IMPORTANT:

- Start with the simplest possible architecture.
- Do not introduce microservices yet.
- Do not introduce PostgreSQL, Redis, Kafka, authentication, messaging, caching, or event-driven architecture yet.
- Keep everything intentionally simple.
- The goal is to learn infrastructure incrementally.

Create a Go application named task-api.

Requirements:

- REST API
- In-memory storage only
- CRUD operations for tasks
- Clean architecture
- Dockerfile
- Health endpoint (/health)
- Readiness endpoint (/ready)
- Structured logging
- Configuration through environment variables
- Graceful shutdown

Project structure should be suitable for future growth into microservices.

After generating the application, also generate:

- Kubernetes Deployment manifest
- Kubernetes Service manifest
- Namespace manifest

Do not generate Helm charts yet.

Explain every folder and design decision.

## Prompt 2

Refactor the task-api application.

Status:

- completed as the first PostgreSQL learning step
- later replaced by per-service PostgreSQL databases
- production-grade PostgreSQL work continues in prompt 15 and prompt 19

Replace in-memory storage with PostgreSQL.

Requirements:

- Repository pattern
- Database migrations
- Connection pooling
- Health checks for PostgreSQL
- Kubernetes Secret for credentials
- PersistentVolumeClaim
- PostgreSQL deployment

Keep everything else unchanged.

## Prompt 3

Add Redis caching to the task-api.

Status:

- completed as the first Redis learning step
- later evolved into shared Redis and Redis Cluster usage
- production Redis hardening continues from prompt 16 onward

Requirements:

- Cache task lookups
- Cache invalidation on updates
- Redis health checks
- Kubernetes manifests
- Docker configuration

Keep architecture simple.

## Prompt 4

Refactor the current FastAPI application into 3 independent microservices:

Status:

- completed and became the main application shape
- current platform also includes search, activity, and notification services
- service boundaries remain valid for the current architecture

1. user-service
2. task-service
3. comment-service

IMPORTANT RULES:
- Keep business logic extremely simple (CRUD only)
- No Kafka yet
- No Elasticsearch yet
- No inter-service communication yet
- Each service must be independently deployable
- Each service must have its own Kubernetes Deployment + Service
- Each service must have its own PostgreSQL database (separate instance or schema per service)

Each service must include:
- FastAPI
- Dockerfile
- /health endpoint
- /ready endpoint
- structured logging
- environment-based configuration

Keep architecture minimal but production-structured.

## Prompt 5

Introduce Kong API Gateway in front of all services.

Status:

- implemented and currently used as the external entry point
- paths were cleaned so services work through /users, /tasks, /comments, /search, /activities, and /notifications
- production follow-up later: auth, TLS, stricter rate limits, and better traffic policy

Requirements:

- Route /users -> user-service
- Route /tasks -> task-service
- Route /comments -> comment-service

Kubernetes setup:
- Kong deployed as ingress gateway
- Services must NOT be publicly exposed anymore
- Only Kong is exposed externally

Add:
- request routing
- basic rate limiting plugin
- request logging plugin

Do NOT add authentication yet.
Keep it simple.

## Prompt 6

Refactor each microservice to use its own dedicated PostgreSQL database.

Status:

- implemented with separate service databases for local learning
- task-service has started moving toward CloudNativePG
- production follow-up: migrate the remaining databases to operator-managed HA PostgreSQL when needed

Requirements:

- user-service -> user_db
- task-service -> task_db
- comment-service -> comment_db

Each service must:
- use connection pooling
- use migrations
- store secrets in Kubernetes Secrets
- have persistent volume claims

Ensure:
- no shared database between services
- full data isolation per service

## Prompt 7

Create a new microservice called search-service.

Status:

- implemented
- first ingestion used HTTP, then Kafka consumer flow was added later
- current search path is event-driven for task/comment events where implemented

Purpose:
- Provide full-text search across tasks and comments

Requirements:

- Use Elasticsearch as storage backend
- Index data from task-service and comment-service
- Provide REST API:
  GET /search?q=...

Data ingestion:
- subscribe to events (no Kafka yet, simulate ingestion via HTTP calls for now)

Infrastructure:
- Elasticsearch deployment in Kubernetes
- Kibana optional

Keep service simple and focused only on search.

## Prompt 8

Add Prometheus monitoring to the platform.

Status:

- implemented with Prometheus Operator, Prometheus CRs, ServiceMonitors, exporters, and rules
- previous manual Prometheus setup was cleaned up in favor of CRD/operator style
- production follow-up: improve SLOs, alert routing, retention, and HA Prometheus later

Current services:

- user-service
- task-service
- comment-service
- search-service
- Kong Gateway
- PostgreSQL databases
- Redis
- Elasticsearch

Requirements:

- Deploy Prometheus in Kubernetes
- Scrape all application metrics
- Scrape Kong metrics
- Scrape PostgreSQL metrics
- Scrape Redis metrics
- Scrape Elasticsearch metrics

Application metrics:

- HTTP request count
- HTTP request duration
- HTTP error count
- Database query count
- Cache hit/miss count

Generate:

- Prometheus manifests
- ServiceMonitor resources
- scrape configurations
- metric instrumentation for FastAPI services

Use production-oriented Kubernetes patterns.

## Prompt 9

Add Grafana to the platform.

Status:

- implemented for local platform visibility
- dashboards exist as Kubernetes config/manifests
- production follow-up: dashboard provisioning, alert panels, datasource security, and long-term metrics storage

Requirements:

Create dashboards for:

1. API Dashboard
   - Request rate
   - Error rate
   - Latency

2. PostgreSQL Dashboard
   - Connections
   - Query throughput
   - Replication readiness

3. Redis Dashboard
   - Memory usage
   - Cache hit ratio
   - Command rate

4. Elasticsearch Dashboard
   - Query rate
   - Index size
   - Cluster health

5. Kong Dashboard
   - Requests
   - Upstream latency
   - Error responses

Generate:

- Grafana deployment
- Dashboard JSON files
- Datasource configuration

## Prompt 10

Add centralized logging using ELK.

Status:

- implemented with Elasticsearch, Kibana, and Fluent Bit
- Kong HTTP logs and pod stdout logs are collected into Elasticsearch
- production follow-up: retention policies, index lifecycle management, security, and scaling

Requirements:

Deploy:

- Elasticsearch
- Kibana
- Fluent Bit

Collect logs from:

- user-service
- task-service
- comment-service
- search-service
- Kong
- PostgreSQL
- Redis

Every log entry must include:

- timestamp
- service name
- log level
- request id
- pod name

Generate:

- Kubernetes manifests
- Fluent Bit configuration
- Kibana dashboards

Explain the complete log flow.

## Prompt 11

Introduce Kafka as the platform event backbone.

Status:

- implemented with Strimzi, Kafka cluster manifests, topics, producers, consumers, retries, and DLQ topics
- task/comment events are used by search/activity/notification flows where implemented
- production follow-up: stronger observability, broker operations, rebalancing, rack awareness, and recovery drills

Requirements:

Deploy Kafka using Strimzi Operator.

Cluster:

- 3 brokers
- persistent storage
- replication factor 3

Create topics:

- user.created
- user.updated
- task.created
- task.updated
- task.deleted
- comment.created
- comment.deleted

Refactor services:

- publish events to Kafka
- use asynchronous event publishing
- add retries and dead-letter handling

Generate:

- Kubernetes manifests
- topic definitions
- producer implementation

Keep existing APIs unchanged.

## Prompt 12

Create activity-service.

Status:

- implemented
- consumes business events from Kafka and stores an audit/event history in PostgreSQL
- production follow-up: retention, idempotency checks, replay strategy, and schema/versioning rules

Purpose:

Maintain an immutable audit log of all business events.

Consume:

- user.*
- task.*
- comment.*

Store events in PostgreSQL.

Schema should contain:

- event id
- event type
- timestamp
- aggregate id
- payload

Expose:

GET /activities

Requirements:

- FastAPI
- Kafka consumer
- PostgreSQL
- Kubernetes deployment
- health checks
- structured logging

## Prompt 13

Create notification-service.

Status:

- implemented for local learning
- consumes selected Kafka events and stores notification records in PostgreSQL
- production follow-up: real delivery providers, retries, templates, idempotency, and delivery status tracking

Purpose:

React to business events.

Consume:

- task.created
- comment.created
- user.created

For now:

- store notifications in PostgreSQL
- expose GET /notifications

Future-ready design:

- email
- sms
- push notifications

Requirements:

- Kafka consumer
- FastAPI
- Kubernetes deployment
- health checks

## Prompt 14

Replace Kubernetes Deployments with Argo Rollouts.

Status:

- implemented for task-service with basic canary rollout
- current canary percentages are pod-ratio based, not exact request-level traffic routing
- production follow-up: add Istio/Gateway API/NGINX traffic routing for exact traffic percentages

Requirements:

Implement canary deployments.

Traffic progression:

- 10%
- 25%
- 50%
- 100%

Rollback automatically if:

- error rate exceeds threshold
- latency exceeds threshold

Integrate with Prometheus metrics.

Generate:

- Rollout resources
- Analysis templates
- Basic canary rollout using pod ratio

Explain clearly:

- basic canary means 10%, 25%, and 50% are based on pod count
- this is not exact request-level traffic splitting
- exact traffic splitting needs a traffic router

## Prompt 15

Migrate PostgreSQL to a highly available architecture.

Status:

- implemented for task-service with CloudNativePG cluster and PgBouncer pooler
- old single-pod PostgreSQL manifests are kept as manual/local learning references
- production follow-up: full backup, WAL archiving, PITR, restore drills, and migration cutover practice

Requirements:

Use CloudNativePG.

Topology:

- 1 primary
- 2 replicas

Features:

- automatic failover
- WAL archiving
- backups
- connection pooling

Generate all Kubernetes manifests.

Explain failover procedures.

## Prompt 16

Migrate Redis to Redis Cluster.

Status:

- implemented as a local StatefulSet-based Redis Cluster
- current setup is useful for learning sharding/failover behavior
- production follow-up: use a Redis Operator or managed Redis, stronger persistence, backups, and failover drills

Requirements:

- sharding
- automatic failover
- persistent storage

Update applications if necessary.

Generate:

- cluster manifests
- health checks
- monitoring configuration

## Prompt 17

Upgrade Kafka deployment toward production-grade operation.

Status:

- partially completed for local-friendly production learning
- Strimzi Kafka, replicated topics, and operational docs exist
- real production work remains for rack awareness, capacity planning, broker scaling, rebalancing, and disaster recovery

Requirements:

- document broker scaling flow
- document partition rebalancing flow
- document rack awareness and why local cluster cannot fully prove it
- topic replication validation

Add monitoring and operational runbooks.

Generate Kubernetes manifests and documentation.

## Prompt 18

Implement platform backup strategy with Velero.

Status:

- local-learning implementation is done with YAML manifests
- Velero backs up Kubernetes resources into local MinIO
- PVC snapshots are intentionally disabled on the local cluster
- production storage snapshots and database-aware backups are handled later

Current state:

- local cluster storage is still Kubernetes default storage
- Velero, MinIO, BackupStorageLocation, Backup, Schedule, and Restore manifests exist
- namespace restore has a test manifest

Goal:

Use Velero to learn Kubernetes resource backup and restore.

Requirements:

- deploy Velero with plain Kubernetes YAML
- configure local-friendly S3-compatible object storage with MinIO
- create backup schedules for important namespaces
- test backup and restore of one namespace
- document full restore commands
- explain what Velero backs up and what it does not back up
- keep PVC snapshots disabled locally with `snapshotVolumes: false`

Explain:

- resource backup vs PVC snapshot
- backup vs disaster recovery
- local backup target vs production backup target
- why restore tests matter more than backup creation
- why PostgreSQL, Kafka, Redis, and Elasticsearch need workload-aware backups in production

Production continuation:

- move backup storage from local MinIO to real S3/Ceph RGW
- enable CSI snapshots when storage supports it
- add CNPG WAL/PITR backup flow
- add Elasticsearch snapshot repository
- document Redis and Kafka restore procedures

---

## Operations, Debugging, Recovery, and Hardening Loop

> From prompt 19 onward, do not only install tools. Every major component must be learned as an operator would run it in production.

For each step, include this loop:

```text
1. understand the concept
2. make the component observable
3. generate realistic load or live writes
4. break one thing on purpose
5. detect the issue with metrics/logs/events/alerts
6. debug the root cause
7. recover safely
8. document local limits and real production differences
9. create a 5-minute review note with flash questions
```

The goal is not only to know Kubernetes YAML. The goal is to practice production behavior: failure, backup, restore, rollback, scaling, alerting, and fast debugging.

Every completed prompt should leave two docs when useful:

```text
docs/concepts/<topic>.md -> understand the idea
docs/commands/<topic>.md -> run, check, debug, configure, and recover
```

## Production Change and Repository Rule

Raw YAML is allowed for first-time learning, local labs, bootstrap, debugging, and emergency drills. For production direction, the repo should move toward Helm/Kustomize/GitOps plus operators.

Default rule for anything already serving users: no downtime.

Production change flow:

```text
1. check current health
2. back up or snapshot when data is involved
3. make a backward-compatible change
4. render/diff manifests before apply
5. roll out progressively
6. watch metrics, logs, events, and alerts
7. verify user-facing behavior
8. keep rollback ready
9. clean up only after confidence
```

Production repo direction:

```text
Git commit
  -> CI validation
  -> Helm/Kustomize render
  -> GitOps sync with Argo CD
  -> operators reconcile runtime resources
```

Manual `kubectl apply` is fine in this local learning project, but the production habit must be GitOps-driven changes with reviewed diffs and rollback paths.

## Prompt 19

Harden PostgreSQL backup, live recovery, and migration safety.

Current state:

- task-service uses CloudNativePG
- migrations run as Kubernetes Jobs
- CNPG backup and restore manifests exist for local drills
- full PITR and rollback flow still need hands-on practice in the cluster
- current local database is small, but the learning target must model a live large database

Goal:

Learn how production PostgreSQL is backed up, restored, migrated, and debugged while writes are happening.

Requirements:

- generate continuous write load against task-service during backup tests
- document migration apply, verify, and rollback flow
- add a pre-migration backup step where practical
- add CNPG Backup CR examples for task-service
- configure or document WAL archiving/PITR flow for task-service
- restore backup into a separate namespace or cluster target
- verify restored data with row counts and sample record checks
- test recovery to a specific point in time after a controlled bad write
- test primary failover behavior
- document RTO and RPO for the task database
- document what changes for a 5TB live production database
- document backup health checks and alerts
- future return drill: practice production-form live database cutover with live writes, validation, write drain, app endpoint switch, verification, and rollback window

Explain:

- backup vs WAL archiving
- primary failover vs restore
- why zero-downtime database migration usually needs expand-and-contract changes
- why `pg_dump` is not enough for very large live databases
- base backup + WAL replay + PITR
- RPO/RTO tradeoffs

## Prompt 20

Eat PostgreSQL operations and emergency debugging.

Current state:

- task-service uses CloudNativePG with primary and replicas
- backup and restore drill works with base backup plus WAL archive
- the project still needs deep PostgreSQL operational practice
- the goal is to become fast during real production incidents

Goal:

Become comfortable operating PostgreSQL when it is slow, blocked, lagging, overloaded, or at risk.

Learning rule:

Do not only read commands. For every scenario:

```text
create the problem
observe the symptom
find the root cause
fix or recover
write the runbook
write a 5-minute review
```

Scenarios:

1. Slow queries
   - create a slow query against tasks
   - inspect `pg_stat_activity`
   - run `EXPLAIN ANALYZE`
   - add the right index
   - compare before and after

2. Missing indexes
   - query by `user_id`, `status`, and `created_at`
   - identify sequential scans
   - create indexes with `CREATE INDEX CONCURRENTLY`
   - document when not to add an index

3. Locks and blocking sessions
   - open a transaction that blocks another query
   - find blocker and blocked session
   - decide when to cancel vs terminate
   - document safe emergency commands

4. Connection pressure
   - create many concurrent connections
   - observe PgBouncer and PostgreSQL connection limits
   - identify connection exhaustion symptoms
   - document app pool vs PgBouncer vs PostgreSQL max connections

5. Replication lag
   - inspect `pg_stat_replication`
   - understand sent/write/flush/replay LSN
   - create pressure where possible
   - detect lag and document recovery actions

6. Vacuum, analyze, and bloat
   - inspect dead tuples
   - understand autovacuum
   - run `VACUUM ANALYZE`
   - document when manual vacuum is useful or dangerous

7. Backup, WAL, and PITR
   - repeat backup and restore manually
   - create a controlled bad write
   - restore to a time before the bad write
   - validate restored data

8. Migration safety
   - create a safe expand-and-contract migration example
   - document bad migration rollback
   - explain why large-table migrations need special care

9. Monitoring and alerting
   - define alerts for slow queries, replication lag, failed backup, WAL archive failure, connection saturation, and disk pressure
   - document first commands to run for each alert

10. PostgreSQL manifest cleanup
   - organize task-service PostgreSQL YAML into a clear production-style structure
   - separate always-applied resources from manual/emergency resources
   - keep Cluster, Pooler, ScheduledBackup, manual Backup, restore template, migration job, secrets, and monitoring ownership clear
   - document which files are applied normally and which files are used only for restore or drills
   - keep this as raw YAML for learning now, then move it into Helm/Kustomize/GitOps later in prompt 34

Generate:

- `docs/concepts/postgresql-operations.md`
- `docs/commands/postgresql.md`
- optional Kubernetes Jobs or scripts for safe local drills

Explain:

- how PostgreSQL writes data
- how WAL protects data
- how indexes speed reads but slow writes
- how locks happen
- how replication lag happens
- how to debug under pressure
- how local learning differs from a 5TB production database

## Prompt 21

Implement RBAC, service account hardening, and access debugging.

Current state:

- services mostly use default Kubernetes access behavior
- human access is not separated by role

Goal:

Create a least-privilege access model for people and workloads.

Requirements:

- define developer, operator, and admin access
- create Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings
- create ServiceAccounts per microservice where needed
- disable automountServiceAccountToken when a pod does not need Kubernetes API access
- document a manual temporary-access runbook
- create denied-access tests to prove least privilege works
- document how to debug `Forbidden` errors safely
- document emergency access and audit requirements

Explain:

- Role vs ClusterRole
- RoleBinding vs ClusterRoleBinding
- human access vs workload access
- least privilege
- break-glass access
- why access changes must be auditable

## Prompt 22

Implement NetworkPolicy, Pod Security Standards, and blocked-traffic debugging.

Current state:

- RBAC is restricted for humans and app service accounts
- app workloads still need network restrictions
- Pod Security Standards are added in audit/warn mode first
- NetworkPolicy YAML is staged in k8s/network-policies
- local Docker Desktop/kind may not enforce NetworkPolicy unless the CNI supports it

Goal:

Restrict traffic and pod permissions in a production-like way.

Requirements:

- create a traffic matrix first
- add default deny NetworkPolicies
- allow only required traffic: Kong to services, services to their dependencies, Prometheus scraping, Fluent Bit to Elasticsearch
- add Pod Security Standard namespace labels in audit mode first
- document validation commands for allowed and blocked traffic
- intentionally block one required path, observe the failure, then fix it
- document how to debug DNS, Service, NetworkPolicy, and CNI-related failures
- document what changes when using Calico/Cilium in production

Explain:

- ingress vs egress NetworkPolicy
- how the CNI enforces NetworkPolicy
- NetworkPolicy vs Kyverno policy
- why audit mode is useful before enforcement
- why local Docker Desktop networking is not the same as real production CNI behavior

## Prompt 23

Add Alertmanager, alert runbooks, and failure detection drills.

Priority:

- deferred until the cluster is stable enough to operate as a platform
- keep the current basic Alertmanager/rules/runbooks, but do not spend deep drill time here yet
- return after the migration-critical platform pieces are ready: GitOps, repo structure, real cluster, ingress HA, Ceph, backup, and DR

Current state:

- Prometheus collects metrics through the Prometheus Operator
- Alertmanager is added with a local placeholder receiver
- production-style alert rules and short runbooks are applied
- service, HTTP, Redis, PostgreSQL, search-service Kafka consumer, and PVC alerts exist
- Kafka broker/consumer lag is still manual until a Kafka exporter or Strimzi metrics pipeline is added
- kube-state-metrics must be healthy for Deployment/StatefulSet/PVC alerts to be reliable
- real Slack/email/PagerDuty routing is intentionally deferred until CI/CD/production identity is ready

Goal:

Turn monitoring into actionable alerts that catch issues before users report them.

For now, keep this as a future operations phase.
When the platform is closer to the real 20-node migration target, continue the drills.

Requirements:

- deploy or configure Alertmanager with Prometheus Operator
- create alert rules for service down, high 5xx rate, high latency, Kafka consumer lag, Redis memory, PostgreSQL replication lag, PVC pressure, and certificate expiry later
- add short runbooks for each alert
- document how to silence alerts during planned work
- create controlled failures to trigger at least three alerts
- document the exact Prometheus query, expected symptom, first debug command, and recovery action for each alert
- add "too noisy / not useful" review notes for bad alerts
- document alert severity: page, ticket, or dashboard-only

Explain:

- alert rule vs alert notification
- how Alertmanager groups, routes, deduplicates, and silences alerts
- why every alert needs an owner and a runbook
- symptom alert vs cause alert
- why a passing backup job still needs restore validation

Migration priority note:

```text
Do not block the Swarm -> Kubernetes migration learning path here.
Basic monitoring exists.
Deep alert drills come back later when the cluster is real enough to control.
```

## Prompt 24

Add security scanning with Trivy Operator and remediation workflow.

Current state:

- local Trivy Operator install commands are documented
- concept and command docs exist
- controlled bad manifest exists for ConfigAuditReport drill
- actual operator apply/test still depends on image/network availability in the local cluster
- CI/CD blocking rules are documented as future gates

Goal:

See vulnerability and configuration risk directly inside Kubernetes.

Requirements:

- deploy Trivy Operator
- inspect VulnerabilityReport and ConfigAuditReport CRs
- document how to read scan results
- define which severities should block deployment later in CI/CD
- pick one real finding or controlled bad manifest and document the fix path
- document how security findings become tickets or CI/CD gates
- document false positive handling

Explain:

- Trivy Operator vs Trivy CLI
- vulnerability report vs config audit report
- why runtime visibility and CI scanning are both useful
- finding severity vs exploitability

## Prompt 25

Add policy enforcement with Kyverno and admission debugging.

Current state:

- local Kyverno install commands are documented
- audit-mode baseline policies exist
- enforce-mode no-privileged example exists but is intentionally separate
- bad and good pod drill manifests exist
- actual operator apply/test depends on local image/network availability

Goal:

Use policy to prevent unsafe workloads from entering the cluster.

Requirements:

- deploy Kyverno
- start policies in audit mode
- require resource requests and limits
- require readiness and liveness probes where appropriate
- require app, version, and team labels
- disallow privileged containers
- later move selected policies from audit to enforce
- apply one intentionally bad manifest and observe audit/enforce behavior
- document how developers debug a rejected deployment
- document policy exception process

Explain:

- audit mode vs enforce mode
- admission control
- why policy should be introduced gradually
- why production policy needs exceptions, ownership, and review

## Prompt 26

Introduce Argo CD and prepare for full CI/CD.

Status:

- foundation added with Argo CD namespace, AppProject, and conservative autosync Applications
- concept and command docs exist
- current Applications are intentionally conservative while the repo is still being cleaned
- production follow-up: convert raw folders into Helm/Kustomize overlays and use app-of-apps/ApplicationSets

Important:

- full CI/CD is part of the target platform
- this step adds GitOps foundation only
- do not implement pipeline automation in this step

Goal:

Deploy and reconcile Kubernetes manifests from Git using Argo CD.

Requirements:

- install Argo CD
- create Applications for platform manifests
- explain sync, health, drift, reconciliation, and rollback
- keep Argo Rollouts responsible for progressive delivery
- keep Prometheus responsible for rollout health checks

Explain:

- Argo CD answers what should be deployed from Git
- Argo Rollouts answers how a new version should be released
- CI/CD will later build, test, scan, push images, and update manifests

## Prompt 27

Implement a production-level CI/CD pipeline.

Current state:

- Argo CD syncs manifests from Git
- Argo Rollouts handles progressive delivery
- security scanning and policies exist

Goal:

Build an automated path from code commit to production deployment.

Requirements:

- build only changed service images
- tag images with immutable git SHA tags
- run tests
- run Trivy CLI image scanning
- push images to a registry
- update manifests or Helm values with the new image tag
- let Argo CD sync the change
- wait for Argo Rollouts to finish
- document rollback by image tag and rollout undo

Explain:

- push-based CI vs pull-based CD
- mutable tag vs immutable tag
- how GitOps rollback works
- how Argo CD and Argo Rollouts work together

## Prompt 28

Add Sentry for application error tracking and faster bug triage.

Current state:

- Prometheus shows metrics
- ELK shows logs
- application exceptions are still found mostly by reading pod logs

Goal:

Capture application errors with stack traces, request context, and release versions.

Requirements:

- choose hosted Sentry or local self-hosted Sentry for learning
- add Sentry SDK configuration to one FastAPI service first
- capture unhandled exceptions
- capture service name, environment, release version, and request path
- add a test endpoint or controlled failure to verify Sentry receives errors
- document how Sentry connects errors to a deployment version
- connect Sentry issue data to logs and metrics for the same request where possible
- document the triage flow: alert/error -> trace/log -> commit/release -> rollback/fix

Explain:

- Sentry vs logs
- error tracking vs metrics
- why release/version tags help rollback and debugging
- what changes later when CI/CD creates immutable image tags
- why stack traces catch bugs faster than raw pod logs

## Prompt 29

Implement SRE practices with simulated incidents.

Current state:

- monitoring and alerts exist
- reliability targets are not formalized

Goal:

Define how reliable the platform should be and how incidents are handled.

Requirements:

- define SLIs for availability, latency, error rate, and Kafka lag
- define SLOs per service
- create an error budget policy
- add burn-rate alert examples
- create a postmortem template
- write one sample postmortem from a simulated incident
- run at least one controlled incident drill end to end
- measure detection time, mitigation time, and recovery time
- document which alert or dashboard found the issue first

Explain:

- SLI vs SLO vs SLA
- error budget
- burn-rate alerting
- blameless postmortems
- MTTD, MTTR, RTO, and RPO

## Prompt 30

Implement resource management, autoscaling, and load/failure tests.

Current state:

- some workloads have basic resources
- scaling behavior is not fully production-like

Goal:

Make workloads safer under load and during node failures.

Requirements:

- set requests and limits for all services
- add HPA for stateless services
- use VPA recommendation mode where useful
- add PodDisruptionBudgets for critical workloads
- add ResourceQuota and LimitRange per namespace
- document graceful shutdown behavior
- generate load and observe HPA scaling behavior
- test what happens when a pod is killed during requests
- document OOMKilled, throttling, pending pod, and eviction debugging

Explain:

- requests vs limits
- HPA vs VPA
- PDB and voluntary disruption
- why databases are scaled differently than stateless APIs
- why local laptop capacity does not prove production capacity

## Prompt 31

Implement TLS with cert-manager.

Current state:

- internal traffic is mostly plain HTTP
- certificates are not managed automatically

Goal:

Learn certificate automation and prepare the platform for TLS.

Requirements:

- deploy cert-manager
- create an internal CA issuer
- issue a certificate for Kong or one internal service first
- add certificate expiry monitoring
- document rotation behavior

Explain:

- Issuer vs ClusterIssuer
- Certificate CR
- self-signed/internal CA vs public CA
- one-way TLS vs mTLS

## Prompt 32

Replace manual Kubernetes Secrets with Vault and External Secrets Operator.

Current state:

- secrets are Kubernetes Secrets, often manually created
- rotation is not clean
- local Vault learning lab is staged early because interview preparation needs it now
- direct Vault Kubernetes auth flow is documented before External Secrets Operator

Goal:

Move secret ownership outside Kubernetes manifests.

Requirements:

- deploy Vault in a local-friendly mode for learning
- configure Kubernetes auth
- deploy External Secrets Operator
- create SecretStore and ExternalSecret for one service secret
- document secret rotation flow

Explain:

- why base64 is not encryption
- Vault static secrets vs dynamic secrets
- ExternalSecret sync flow
- what changes in real production Vault setup

## Prompt 33

Introduce private registry and image signing.

Current state:

- images are pushed manually or pulled from public registries
- image signature verification is not enforced

Goal:

Prepare for trusted image delivery.

Requirements:

- explain Harbor, GHCR, and Docker Hub tradeoffs
- deploy Harbor only if local resources allow it
- add Cosign signing design for CI/CD
- add Kyverno verifyImages policy in audit mode
- document rollback using immutable image tags

Explain:

- private registry
- image signing
- provenance
- why immutable tags matter for rollback

## Prompt 34

Refactor manifests into production repo style with Helm, Kustomize, and GitOps.

Current state:

- manifests are mostly raw YAML
- environment differences are manual
- platform installation still depends on many kubectl apply commands
- raw YAML helped us learn the components, but it is not the final production workflow
- first safe slice started: production IaC docs and target folders added
- first low-risk component started: RBAC converted to `k8s/platform/rbac/base` Kustomize path
- second low-risk component started: External Secrets converted to `k8s/platform/secrets/base` Kustomize path

Goal:

Move from lab-style YAML to production-style infrastructure as code with reviewed diffs, repeatable environments, GitOps sync, and no-downtime changes by default.

Requirements:

- decide what stays raw YAML, what becomes Kustomize overlays, and what becomes Helm releases
- create Helm charts or chart wrappers for platform components and microservices where useful
- manage many Helm releases with Helmfile or Helmsman when it adds value
- create local, dev, staging, and prod values files
- keep secrets managed by External Secrets
- keep CRD installation order clear for operators like Strimzi, CNPG, Prometheus Operator, and cert-manager
- document helm template, kustomize build, helm diff, helmfile diff, and helmfile apply commands
- prepare Argo CD to sync app-of-apps or application sets
- migrate one component at a time without downtime
- keep rollback path clear for each converted component

Explain:

- Helm chart
- values files
- Kustomize overlays
- Helmfile vs Helmsman
- release ordering
- environment drift
- GitOps reconciliation
- why Helm/Kustomize/GitOps are production infrastructure as code

## Prompt 35

Practice rollout strategies and production release drills.

Current state:

- task-service uses Argo Rollouts with a basic canary
- current canary is mostly pod-ratio based
- the platform does not yet compare rollout strategies side by side

Goal:

Understand how production teams release changes safely, when each strategy is useful, and how rollback behaves under pressure.

Requirements:

- document and test RollingUpdate
- document and test Recreate, including why it causes downtime
- document and test Blue/Green release flow
- document and test Canary release flow
- document A/B testing and how it differs from canary
- document shadow traffic and when it is useful
- document feature flags and how they reduce release risk
- compare Kubernetes Deployment strategy with Argo Rollouts strategy
- test rollback for each practical local strategy
- test one release while requests are hitting Kong
- document what metrics, logs, events, and alerts prove a rollout is healthy
- document how database migrations affect each strategy
- document what changes later with Istio, Gateway API, or NGINX exact traffic routing

Explain:

- RollingUpdate vs Recreate
- Blue/Green vs Canary
- Canary vs A/B testing
- shadow traffic
- feature flags
- rollback vs roll-forward
- why zero-downtime release needs backward-compatible app and database changes

## Prompt 36

Upgrade Argo Rollouts to exact traffic splitting.

Current state:

- current canary uses pod ratio
- exact request percentage is not implemented

Goal:

Use a real traffic router for exact 10%, 25%, 50%, and 100% canary traffic.

Requirements:

- choose Gateway API, NGINX, or Istio as the traffic router
- add stable and canary Services
- configure Argo Rollouts trafficRouting
- keep Prometheus AnalysisTemplate checks
- keep public Kong API paths unchanged

Explain:

- pod-ratio canary vs request-level traffic split
- why a traffic router is required
- how rollback works when traffic routing is involved

## Prompt 37

Deploy Istio service mesh for mTLS, resilience, and tracing.

Current state:

- service-to-service traffic is not managed by a mesh
- mTLS and tracing are not platform-wide

Goal:

Learn what a service mesh adds after the platform basics are stable.

Requirements:

- deploy Istio in a local-friendly profile
- enable sidecar injection for one namespace first
- validate traffic before enforcing STRICT mTLS
- add basic retry and circuit breaker policy
- expose mesh metrics to Prometheus
- add tracing integration if resources allow

Explain:

- sidecar proxy
- mTLS in a mesh
- DestinationRule and VirtualService
- when a mesh is useful and when it is too much

## Prompt 38

Implement Kubernetes audit logging and multi-environment strategy.

Current state:

- cluster-level audit events are not reviewed
- environment promotion rules are not formalized

Goal:

Prepare for real production governance.

Requirements:

- document Kubernetes audit logging concepts
- capture important events: secret access, RBAC changes, exec into pods, deployment changes
- forward audit logs to the log stack where possible
- define dev, staging, and production promotion rules
- require manual production approval in the final CI/CD design

Explain:

- audit log vs application log
- why production access must be traceable
- why environments need promotion rules

---

## Real Server Steps

> Complete prompts 1-38 on the local learning cluster first, then move to real servers.

## Prompt 39

Provision production-grade Kubernetes with Kubespray.

Goal:

Move from local learning cluster to real servers.

Requirements:

- prepare 3 real Linux servers
- install Kubernetes with Kubespray
- use containerd
- choose and document CNI
- decide stacked etcd vs external etcd
- configure etcd snapshots
- validate node, DNS, storage, and networking health

Explain:

- what changes from local cluster to real servers
- control plane HA
- etcd backup and restore
- why node preparation matters

## Prompt 40

Deploy HAProxy and Keepalived for bare-metal ingress HA.

Goal:

Expose Kong through a highly available virtual IP.

Requirements:

- deploy HAProxy on edge nodes
- deploy Keepalived with VRRP
- configure VIP failover
- route external traffic to Kong NodePorts or LoadBalancer replacement
- test failover by stopping one edge node

Explain:

- VIP
- VRRP
- HAProxy health checks
- how traffic reaches Kong on bare metal

## Prompt 41

Add Zabbix for real-server and network monitoring.

Current state:

- Kubernetes metrics are covered by Prometheus
- application logs are covered by ELK
- application errors are covered by Sentry
- physical or VM infrastructure monitoring is not covered clearly

Goal:

Use Zabbix to monitor the real servers and infrastructure around Kubernetes.

Requirements:

- explain where Zabbix is useful and where Prometheus is better
- deploy or prepare Zabbix Server for the real-server environment
- install Zabbix agents on Kubernetes nodes
- monitor CPU, memory, disk, network, process health, and node availability
- add checks for HAProxy, Keepalived VIP, disk pressure, and node reachability
- document how Zabbix alerts complement Prometheus alerts

Explain:

- Zabbix agent
- SNMP monitoring
- host monitoring vs Kubernetes-native monitoring
- why Zabbix is common for servers, VMs, switches, routers, and firewalls

## Prompt 42

Deploy production Rook-Ceph on real nodes.

Goal:

Run Ceph with real disks and production-like failure behavior.

Requirements:

- prepare dedicated raw block devices for OSDs
- deploy Rook-Ceph with 3 nodes
- configure MON, MGR, and OSDs
- create CephBlockPool and StorageClass
- create RGW object storage for backups
- test OSD failure and recovery
- document adding and replacing an OSD

Explain:

- OSD failure
- replication factor
- failure domain
- ceph status and health warnings

## Prompt 43

Move production backups to Ceph object storage with Velero.

Goal:

Store cluster backups in Ceph RGW and practice restore.

Requirements:

- configure Velero with Ceph RGW S3 endpoint
- configure CSI snapshots where supported
- create backup schedules
- include CNPG backup and WAL/PITR flow
- run a namespace restore drill
- document full-cluster restore order
- restore PostgreSQL into a separate namespace and validate data
- restore Elasticsearch indexes from snapshot repository where applicable
- document Kafka and Redis backup/recovery limits separately from Velero

Explain:

- Velero backup location
- CSI snapshot
- why PostgreSQL needs database-aware backup in addition to PVC snapshots
- why object backup exists in a different failure domain than the workload

## Prompt 44

Design full disaster recovery procedures for the real cluster.

Goal:

Know what to do when production breaks badly.

Requirements:

- document recovery for node failure, PostgreSQL primary failure, Redis master failure, Kafka broker failure, Elasticsearch data loss, etcd quorum loss, and full cluster loss
- define RTO and RPO per scenario
- create step-by-step restore commands
- define validation checks after restore
- create a DR drill checklist
- run at least one partial DR drill on real nodes
- document what data can be lost in each scenario
- document who decides failover, restore, rollback, and user communication

Explain:

- HA vs DR
- restore order during multi-component failure
- how to validate data integrity after recovery
- why untested backups are not backups

## Prompt 45

Add OpenTelemetry Collector and distributed tracing.

Priority:

- later, after the Kubernetes platform is stable and core migration work is under control
- do not do this before GitOps, real cluster, ingress HA, Ceph, backups, and DR
- tracing is useful, but it is not the first blocker for moving a 20-node Swarm platform to Kubernetes

Current state:

- Prometheus gives metrics
- ELK/Fluent Bit gives logs
- Sentry is planned for application exceptions
- service-to-service traces are not collected in a standard way

Goal:

Understand request flow across services and make debugging multi-service latency/errors faster.

Requirements:

- deploy OpenTelemetry Collector
- instrument one FastAPI service first
- emit traces with service name, route, status, latency, and request id
- choose a tracing backend for learning: Tempo or Jaeger
- connect traces to logs using request id where possible
- document what changes when Istio/service mesh is later added
- document sampling, retention, and storage cost tradeoffs
- keep the first implementation small and do not instrument every service at once

Explain:

- trace vs metric vs log
- span and trace id
- OpenTelemetry SDK vs OpenTelemetry Collector
- Tempo vs Jaeger
- why tracing helps after metrics tell you there is a problem
- why tracing every request forever can be expensive

## Prompt 46

Add SIEM/security event correlation.

Priority:

- later, after Kubernetes audit logging and production access model are clearer
- do not do this before real cluster basics, backup, DR, and stable observability
- learn this as security monitoring and governance, not as the first migration task

Current state:

- Kubernetes RBAC and policy docs exist
- Kyverno and Trivy provide policy/security visibility inside Kubernetes
- Kubernetes audit logging is planned
- logs are collected, but security correlation is not designed

Goal:

Understand how production teams detect suspicious platform activity and correlate security-relevant events.

Requirements:

- define which events should be security-relevant:
  - secret access
  - RBAC changes
  - exec into pods
  - port-forward usage
  - image policy failures
  - denied admission events
  - unusual login/access patterns
- choose a SIEM direction for learning:
  - Elastic Security / Wazuh / Splunk / enterprise SIEM
- document how Kubernetes audit logs reach the SIEM
- document alert ownership and response flow
- document what remains in Prometheus/Alertmanager vs what belongs in SIEM
- create a small local-friendly example if resources allow

Explain:

- SIEM vs log stack
- security event vs application log
- Kubernetes audit log vs pod log
- correlation rule
- why access to production must be traceable
- why SIEM comes after clean identity, RBAC, audit logs, and log collection

---
## Platform Tooling Reference

| Tool | Role |
|---|---|
| Harbor | Private container registry, image scanning, and image signing |
| Cosign | Image signing and verification |
| Vault | Secrets management, dynamic credentials, audit logging |
| External Secrets Operator | Syncs Vault secrets into Kubernetes Secrets |
| Istio | Service mesh, mTLS, circuit breaker, distributed tracing |
| cert-manager | Automatic TLS certificate issuance and renewal |
| k9s | Terminal UI for navigating Kubernetes clusters, inspecting pods, logs, and resources |
| stern | Multi-pod log tailing with filtering by namespace, label, and container |
| Prometheus | Metrics collection and storage |
| Grafana | Metrics dashboards and visualization |
| Alertmanager | Alert routing, deduplication, and notification |
| Sentry | Application error tracking, stack traces, traces, and release-aware debugging |
| OpenTelemetry Collector | Receives, processes, and exports traces, metrics, and logs |
| Jaeger | Distributed tracing backend for viewing request traces |
| Tempo | Grafana-native distributed tracing backend, often paired with Loki/Grafana |
| SIEM | Security event correlation, audit review, and incident investigation |
| Zabbix | Real server, VM, network device, and infrastructure monitoring |
| Elasticsearch + Kibana | Log storage and exploration (ELK stack) |
| Fluent Bit | Kubernetes log collection and forwarding |
| Argo CD | GitOps continuous delivery, manifest reconciliation |
| Argo Rollouts | Progressive delivery, canary releases, automated rollback |
| Helm | Kubernetes package manager and templating system |
| Helmfile / Helmsman | Declarative management for many Helm releases |
| Velero | Kubernetes resource and PVC backup and restore |
| Trivy | Container image vulnerability scanning and policy auditing |
| Kyverno | Kubernetes-native policy engine for admission control |
| HAProxy + Keepalived | External load balancer and VIP for bare-metal HA |
| Kubespray | Ansible-based Kubernetes cluster provisioning |
| CloudNativePG | Operator-managed PostgreSQL with HA and PITR |
| Strimzi | Operator-managed Kafka |
| Rook-Ceph | Cloud-native distributed storage (block + object) |

## CRDs and Custom Resources Reference

| CR Kind | API Group | Introduced In | Purpose |
|---|---|---|---|
| Certificate | cert-manager.io | prompt 31 | TLS certificate issued by internal CA |
| ClusterIssuer | cert-manager.io | prompt 31 | Certificate authority definition |
| OpenTelemetryCollector | opentelemetry.io | prompt 45 | OpenTelemetry Collector deployment/configuration |
| ExternalSecret | external-secrets.io | prompt 32 | Pulls secret from Vault into Kubernetes |
| SecretStore | external-secrets.io | prompt 32 | Vault connection configuration |
| PeerAuthentication | security.istio.io | prompt 37 | Istio mTLS mode per namespace |
| DestinationRule | networking.istio.io | prompt 37 | Circuit breaker and connection pool |
| VirtualService | networking.istio.io | prompt 36 / prompt 37 | Traffic routing, retries, and mesh rules |
| KafkaTopic | kafka.strimzi.io | prompt 11 | Kafka topic definition |
| Kafka | kafka.strimzi.io | prompt 11 | Kafka cluster definition |
| Cluster | postgresql.cnpg.io | prompt 15 | CloudNativePG PostgreSQL cluster |
| Pooler | postgresql.cnpg.io | prompt 15 | PgBouncer connection pooler |
| Backup | postgresql.cnpg.io | prompt 19 | Scheduled CNPG backup |
| Prometheus | monitoring.coreos.com | prompt 8 | Prometheus instance managed by operator |
| ServiceMonitor | monitoring.coreos.com | prompt 8 | Declarative scrape target |
| PrometheusRule | monitoring.coreos.com | prompt 23 / prompt 29 | Alerting, recording rules, and SLO burn rate alerts |
| Rollout | argoproj.io | prompt 14 | Argo Rollouts progressive delivery |
| AnalysisTemplate | argoproj.io | prompt 14 | Prometheus-based rollout health check |
| Application | argoproj.io | prompt 26 | Argo CD application sync definition |
| VulnerabilityReport | aquasecurity.github.io | prompt 24 | Trivy image scan result |
| ConfigAuditReport | aquasecurity.github.io | prompt 24 | Trivy config audit result |
| ClusterPolicy | kyverno.io | prompt 25 | Kyverno admission policy |
| CephBlockPool | ceph.rook.io | prompt 42 | Ceph RBD block storage pool |
| CephCluster | ceph.rook.io | prompt 42 | Rook-managed Ceph cluster |
| ObjectBucketClaim | objectbucket.io | prompt 43 | S3-compatible bucket request for backups |

---
