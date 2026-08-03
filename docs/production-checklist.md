# Production Checklist

Use this checklist when starting or reviewing another production project.

## Kubernetes

- Use namespaces for ownership boundaries.
- Use Secrets and ConfigMaps, not hardcoded config.
- Add requests, limits, readiness probes, and liveness probes.
- Prefer operators for complex stateful systems.
- Keep Kubernetes manifests repeatable with `kubectl apply`.

## Database

- Use database-per-service where possible.
- Use an operator for PostgreSQL in Kubernetes.
- Run at least 3 instances for HA databases.
- Use persistent storage.
- Connect apps through a pooler like PgBouncer.
- Run migrations as Kubernetes Jobs.
- Plan backups before production traffic.

## Traffic

- Put one gateway in front of services.
- Keep public paths simple.
- Make Swagger/OpenAPI work through the gateway.
- Add rate limiting and request IDs.

## Events

- Use Kafka topics for business events.
- Keep APIs synchronous and events asynchronous.
- Add retries on producers.
- Add DLQ handling on consumers.
- Store audit activity for important events.

## Observability

- Use structured stdout logs.
- Collect logs with Fluent Bit.
- Store logs in Elasticsearch or another log backend.
- Use Prometheus Operator and ServiceMonitor CRs.
- Add Grafana dashboards for apps and infrastructure.
- Alert on errors, latency, restarts, storage, and Kafka lag.

## Delivery

- Use canary or blue-green rollout for important services.
- Use Prometheus analysis before promotion.
- Use GitOps with Argo CD.
- Build full CI/CD after the runtime platform is clean.
