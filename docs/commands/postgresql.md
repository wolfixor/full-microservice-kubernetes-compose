# PostgreSQL Commands

Short commands for `task-service` database operations.

## First 5 Minutes

```text
1. Confirm user impact.
2. Check app errors and latency.
3. Check primary, replicas, and pooler.
4. Check active queries and locks.
5. Check replication lag.
6. Check disk/PVC pressure.
7. Check backup and WAL archive health.
```

## Health

```bash
kubectl get cluster task-db -n task-api
kubectl get pooler task-db-pooler-rw -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | grep task-db
```

Primary:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select pg_is_in_recovery(), now();"
```

## pgAdmin

Kubernetes deploy:

```bash
kubectl apply -k k8s/apps/pgadmin/base
kubectl rollout status deployment/pgadmin -n task-api --timeout=300s
kubectl port-forward -n task-api svc/pgadmin 5050:80
```

Open:

```text
http://localhost:5050
```

Login:

```text
email: admin@local.dev
password: admin
```

Kubernetes DB connection:

```text
host: task-db-pooler-rw.task-api.svc.cluster.local
port: 5432
database: task_db
user: task_app
password: ${TASK_DB_PASSWORD}
```

Docker Compose deploy:

```bash
docker compose up -d pgadmin
```

Open:

```text
http://localhost:5050
```

Compose DB password:

```text
postgres
```

## Backups

List backups:

```bash
kubectl get backup -n task-api
```

Backup details:

```bash
kubectl describe backup task-db-manual -n task-api
```

Show backup id, phase, and WAL range:

```bash
kubectl get backup task-db-manual -n task-api \
  -o jsonpath="backupId={.status.backupId} phase={.status.phase} beginWal={.status.beginWal} endWal={.status.endWal}"
```

Create or rerun manual backup:

```bash
kubectl delete backup task-db-manual -n task-api --ignore-not-found
kubectl apply -f k8s/apps/task-service/operations/postgres-backup.yaml
kubectl get backup -n task-api
```

Check backup config:

```bash
kubectl get cluster task-db -n task-api -o yaml | grep -A30 "backup:"
```

Check PostgreSQL version:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select version();"
```

## WAL Archive

Force WAL switch:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select pg_switch_wal();"
```

Open MinIO debug shell:

```bash
kubectl run -n velero minio-debug --rm -it --restart=Never \
  --image=quay.io/minio/mc:RELEASE.2025-07-21T05-28-08Z \
  --command -- sh
```

Inside:

```sh
mc alias set local http://minio.velero.svc.cluster.local:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}
mc ls -r local/cnpg/task-db/task-db/base
mc ls -r local/cnpg/task-db/task-db/wals
exit
```

## Restore

Restore into separate namespace:

```bash
kubectl delete namespace task-api-restore --ignore-not-found
kubectl apply -f k8s/apps/task-service/operations/postgres-restore-example.yaml
kubectl wait cluster/task-db-restore -n task-api-restore --for=condition=Ready --timeout=600s
```

Check restore cluster:

```bash
kubectl get cluster -n task-api-restore
kubectl get pods -n task-api-restore
```

Compare row counts:

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "select count(*) from tasks;"

kubectl exec -n task-api-restore task-db-restore-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-restore-rw -U task_app -d task_db \
  -c "select count(*) from tasks;"
```

Rule:

```text
Physical restore must use a compatible PostgreSQL major version.
For cross-version migration, prefer pg_dump/pg_restore, pg_upgrade, or logical replication.
```

Dump and WAL rule:

```text
Do not plan "pg_dump restore + WAL replay".

pg_dump/pg_restore
  -> logical restore
  -> no WAL replay to latest

physical base backup + WAL
  -> PITR/latest recovery
```

## PITR Drill

Create a good row before the target time:

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "insert into tasks (id,title,description,status,user_id,created_at,updated_at) values ('pitr-good-1','PITR good row','created before bad write','pending','pitr-lab',now(),now()) on conflict (id) do nothing;"
```

Force WAL switch:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select pg_switch_wal();"
```

Record target time:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select now() as pitr_target_time;"
```

Create bad row after target time:

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "insert into tasks (id,title,description,status,user_id,created_at,updated_at) values ('pitr-bad-1','PITR bad row','created after target time','pending','pitr-lab',now(),now()) on conflict (id) do update set title=excluded.title, description=excluded.description, updated_at=now();"
```

Verify live DB has both:

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "select id,title,user_id,created_at from tasks where id in ('pitr-good-1','pitr-bad-1') order by created_at;"
```

Set `recoveryTarget.targetTime` in:

```text
k8s/apps/task-service/operations/postgres-restore-example.yaml
```

Example:

```yaml
bootstrap:
  recovery:
    source: task-db-backup
    recoveryTarget:
      targetTime: "2026-08-16 10:12:38.65514+00"
```

Restore:

```bash
kubectl delete namespace task-api-restore --ignore-not-found
kubectl apply -f k8s/apps/task-service/operations/postgres-restore-example.yaml
kubectl wait cluster/task-db-restore -n task-api-restore --for=condition=Ready --timeout=600s
```

Verify PITR:

```bash
kubectl exec -n task-api-restore task-db-restore-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-restore-rw -U task_app -d task_db \
  -c "select id,title,user_id,created_at from tasks where id in ('pitr-good-1','pitr-bad-1') order by created_at;"
```

Expected:

```text
pitr-good-1 exists
pitr-bad-1 does not exist
```

## Live Restore Pattern

Do not restore over the live database first.

Safe flow:

```text
1. restore backup/PITR into task-api-restore
2. validate row counts and sample records
3. decide repair or cutover
4. keep live task-db untouched until the decision
```

Compare specific records:

```bash
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "select id,title,updated_at from tasks where id='<id>';"

kubectl exec -n task-api-restore task-db-restore-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-restore-rw -U task_app -d task_db \
  -c "select id,title,updated_at from tasks where id='<id>';"
```

Repair path:

```text
Use when only some rows are bad or missing.
Restore side DB.
Export correct rows.
Review SQL.
Patch live DB.
Keep serving traffic.
```

Cutover path:

```text
Use when live DB is too damaged or migration is large.
Restore side DB.
Validate.
Pause/drain writes.
Switch app DB host/pooler/DNS.
Verify.
Resume writes.
Keep old DB for rollback window.
```

Repair example after validation:

```text
export only the missing/correct rows from restored DB
review SQL
apply small controlled patch to live DB
```

Cutover example after validation:

```text
pause/drain writes
change app DB host to restored DB or new pooler
roll app safely
verify
keep old DB for rollback window
```

Future live cutover drill:

```text
restore side DB
generate live writes
validate side DB
pause/drain writes
switch app DB endpoint
verify user requests
keep old DB for rollback
```

## Slow Query

Active queries:

```sql
select pid,state,wait_event_type,wait_event,now() - query_start as duration,left(query,120) as query
from pg_stat_activity
where state <> 'idle'
order by duration desc;
```

Query plan:

```sql
explain analyze select * from tasks where user_id='db-lab';
```

Safe live index:

```sql
create index concurrently if not exists idx_tasks_user_id on tasks(user_id);
```

## Connection Pressure

Check PgBouncer config:

```bash
kubectl describe pooler task-db-pooler-rw -n task-api
```

Check task-service pod count:

```bash
kubectl get pods -n task-api -l app=task-service
```

Check PostgreSQL sessions:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select usename,application_name,client_addr,state,count(*) from pg_stat_activity group by usename,application_name,client_addr,state order by count(*) desc;"
```

Check active and waiting sessions:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select pid,usename,client_addr,state,wait_event_type,wait_event,now() - query_start as duration,left(query,100) as query from pg_stat_activity where state <> 'idle' order by duration desc;"
```

Read the numbers:

```text
app-side connections
  -> task-service to PgBouncer

server-side connections
  -> PgBouncer to PostgreSQL

poolMode: transaction
  -> real PostgreSQL connection is held only during a transaction
```

Rule:

```text
app pods * app max DB connections must not create more pressure than PgBouncer and PostgreSQL can safely handle.
```

## Locks

Find blockers:

```sql
select blocked.pid as blocked_pid,
       blocking.pid as blocking_pid,
       now() - blocked.query_start as blocked_duration,
       blocked.wait_event_type,
       blocked.wait_event,
       blocked.query as blocked_query,
       blocking.query as blocking_query
from pg_stat_activity blocked
join pg_locks blocked_locks on blocked_locks.pid = blocked.pid
join pg_locks blocking_locks
  on blocking_locks.locktype = blocked_locks.locktype
 and blocking_locks.database is not distinct from blocked_locks.database
 and blocking_locks.relation is not distinct from blocked_locks.relation
 and blocking_locks.transactionid is not distinct from blocked_locks.transactionid
 and blocking_locks.pid <> blocked_locks.pid
join pg_stat_activity blocking on blocking.pid = blocking_locks.pid
where not blocked_locks.granted
  and blocking_locks.granted;
```

Cancel:

```sql
select pg_cancel_backend(<pid>);
```

Terminate only if needed:

```sql
select pg_terminate_backend(<pid>);
```

## Vacuum And Analyze

Check dead tuples and maintenance timestamps:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "select relname,n_live_tup,n_dead_tup,last_vacuum,last_autovacuum,last_analyze,last_autoanalyze from pg_stat_user_tables order by n_dead_tup desc;"
```

Check table sizes:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "select relname,pg_size_pretty(pg_total_relation_size(relid)) as total_size,pg_size_pretty(pg_relation_size(relid)) as table_size from pg_stat_user_tables order by pg_total_relation_size(relid) desc;"
```

Create lab rows:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "insert into tasks (id,title,description,status,user_id,created_at,updated_at) select 'vacuum-lab-' || g, 'vacuum lab', 'dead tuple lab', 'pending', 'vacuum-lab', now(), now() from generate_series(1,1000) g on conflict (id) do nothing;"
```

Create dead tuples:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "update tasks set title='vacuum lab updated 1', updated_at=now() where user_id='vacuum-lab'; update tasks set title='vacuum lab updated 2', updated_at=now() where user_id='vacuum-lab'; update tasks set title='vacuum lab updated 3', updated_at=now() where user_id='vacuum-lab';"
```

Check exact counts:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "select count(*) as exact_count from tasks; select count(*) as vacuum_lab_count from tasks where user_id='vacuum-lab';"
```

Clean and refresh stats:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "vacuum analyze tasks;"
```

Rules:

```text
n_live_tup and n_dead_tup are estimates.
count(*) is exact.
VACUUM cleans dead tuples for reuse.
ANALYZE refreshes planner statistics.
VACUUM FULL can block traffic; do not run it casually in production.
```

## Migration Safety

Add nullable column:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "alter table tasks add column if not exists priority text;"
```

Check table shape:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "\d+ tasks"
```

Check old rows missing the new value:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "select count(*) as missing_priority from tasks where priority is null;"
```

Backfill:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "update tasks set priority='normal' where priority is null;"
```

Verify:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "select priority,count(*) from tasks group by priority order by priority;"
```

Enforce:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "alter table tasks alter column priority set not null;"
```

Keep old app compatible:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d task_db \
  -c "alter table tasks alter column priority set default 'normal';"
```

Test through Kong:

```bash
curl -X POST http://localhost:8888/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"migration safe test","description":"default priority","user_id":"migration-lab"}'
```

Rule:

```text
Add nullable first.
Backfill.
Add default or deploy app support.
Then enforce NOT NULL.
```

## Replication

Primary-side lag:

```bash
kubectl exec -n task-api task-db-1 -- \
  psql -U postgres -d postgres \
  -c "select application_name,state,sync_state,sent_lsn,replay_lsn,pg_wal_lsn_diff(sent_lsn,replay_lsn) as bytes_lag from pg_stat_replication;"
```

Replica-side replay time:

```bash
kubectl exec -n task-api task-db-2 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h 127.0.0.1 -U task_app -d task_db \
  -c "select pg_is_in_recovery(), now() - pg_last_xact_replay_timestamp() as replay_delay;"
```

## Do Not Do First

```text
Do not restart the database without evidence.
Do not delete PVCs.
Do not restore over the live database.
Do not kill random queries.
Do not run blocking schema changes on large tables.
Do not only scale app pods if DB is the bottleneck.
```

## Safe Order

```text
symptom
  -> gather evidence
  -> identify bottleneck
  -> choose smallest safe action
  -> verify user behavior
  -> document root cause
```
