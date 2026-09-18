# PostgreSQL Operations

This is the request-to-database flow for `task-service`.

## Request Flow

```text
user
  -> Kong /tasks
  -> task-service Service
  -> task-service pod
  -> FastAPI endpoint
  -> CachedTaskRepository
  -> SQLAlchemy AsyncSession
  -> PgBouncer task-db-pooler-rw
  -> task-db-rw Service
  -> PostgreSQL primary
  -> tasks table
  -> WAL
  -> replicas replay WAL
  -> response returns to user
```

## Code Flow

Create task:

```text
POST /tasks
  -> services/task-service/app/api/endpoints/tasks.py
  -> create_task()
  -> CachedTaskRepository.create()
  -> SQLAlchemy adds Task model
  -> commit()
  -> PostgreSQL writes row
  -> background Kafka event is published after DB commit
```

Read task:

```text
GET /tasks/{id}
  -> CachedTaskRepository.get_by_id()
  -> Redis cache check
  -> cache hit: return cached task
  -> cache miss: query PostgreSQL
  -> store result in Redis
```

The database model is `tasks`:

```text
id
title
description
status
user_id
created_at
updated_at
```

## Kubernetes Database Parts

```text
CloudNativePG Operator
  -> watches Cluster/task-db
  -> creates PostgreSQL pods
  -> creates task-db-rw, task-db-ro, task-db-r Services
  -> handles replication and failover
  -> handles backup and WAL archive config
```

Current task database:

```text
task-db
  -> 3 PostgreSQL pods
  -> 1 primary
  -> 2 replicas
```

Services:

```text
task-db-rw
  -> points to current primary

task-db-ro
  -> points to replicas for reads

task-db-r
  -> points to all instances

task-db-pooler-rw
  -> PgBouncer pooler in front of task-db-rw
```

## PgBouncer

`task-service` connects to:

```text
POSTGRES_HOST=task-db-pooler-rw
```

PgBouncer protects PostgreSQL from too many direct app connections.

Current pooler mode:

```text
poolMode: transaction
max_client_conn: 100
default_pool_size: 20
instances: 2
```

Meaning:

```text
many app connections
  -> PgBouncer keeps fewer real PostgreSQL connections
  -> each transaction borrows a DB connection
  -> connection returns to pool after transaction
```

Terms:

```text
connection
  -> open conversation between app and database

pool
  -> reusable group of connections

transaction
  -> all-or-nothing unit of database work
  -> commit saves changes
  -> rollback cancels changes
```

In this project there can be two pool layers:

```text
task-service SQLAlchemy pool
  -> app-side reusable connections

PgBouncer pool
  -> fewer real PostgreSQL server connections
```

Transaction pool mode:

```text
app request starts DB work
  -> transaction begins
  -> PgBouncer gives real PostgreSQL connection
  -> SQL runs
  -> commit or rollback
  -> real PostgreSQL connection returns to PgBouncer pool
```

Current pooler config:

```text
poolMode: transaction
max_client_conn: 100
default_pool_size: 20
instances: 2
```

Meaning:

```text
each PgBouncer pod accepts up to 100 app-side client connections
each PgBouncer pod keeps about 20 real PostgreSQL connections per pool
2 PgBouncer pods means roughly 200 app-side connections can be compressed into about 40 real DB connections
```

Sizing rule:

```text
app pods * app max DB connections
  -> must fit safely behind PgBouncer

PgBouncer real server connections
  -> must fit safely inside PostgreSQL max_connections
```

Example:

```text
10 task-service pods
15 possible DB connections per pod
  -> 150 app-side connections

2 PgBouncer pods
20 server connections each
  -> about 40 real PostgreSQL connections
```

## pgAdmin

pgAdmin is a UI for inspecting PostgreSQL.

Use it for learning and debugging:

```text
schemas
tables
rows
indexes
query plans
sessions
backup metadata checks
```

In Kubernetes, pgAdmin connects to:

```text
task-db-pooler-rw.task-api.svc.cluster.local:5432
database: task_db
user: task_app
```

In Docker Compose, pgAdmin connects to service names like:

```text
task-service-db:5432
user-service-db:5432
comment-service-db:5432
```

Production note:

```text
Do not expose pgAdmin publicly without strong auth, TLS, network restrictions, and audit rules.
Prefer temporary/internal access for production debugging.
```

## WAL

WAL means Write-Ahead Log.

Before PostgreSQL considers data durable, it writes the change to WAL. WAL is used for:

```text
crash recovery
replication
point-in-time recovery
backup consistency
```

Flow:

```text
INSERT task
  -> write WAL record
  -> write table/index pages
  -> stream WAL to replicas
  -> archive WAL to object storage
```

## Backup Flow

This project uses CloudNativePG backup config:

```text
task-db primary
  -> base backup
  -> WAL archive
  -> MinIO bucket s3://cnpg/task-db
```

Base backup is a full starting point.

WAL archive stores changes after that starting point.

Restore uses both:

```text
base backup
  -> replay WAL
  -> database becomes consistent
  -> optional PITR stops before a bad write
```

Important time rule:

```text
If a base backup starts at 11:50 and finishes at 12:00,
it is not simply "the database at 12:00".

PostgreSQL still needs WAL from during the backup
to make the copied files consistent.
```

To restore exactly to 12:00:

```text
choose a valid base backup before 12:00
  -> replay WAL
  -> stop at 12:00
```

So WAL is not only for "after backup". WAL is also what makes a physical backup consistent and precise.

## Barman And pgBackRest

Barman and pgBackRest are PostgreSQL-aware backup tools.

They manage:

```text
base backups
continuous WAL archive
retention
restore
PITR
backup validation
```

Common shape:

```text
PostgreSQL
  -> Barman or pgBackRest
  -> object storage / backup repository
  -> restore into side DB
```

In this project, CNPG uses a Barman-style object-store flow.

Production note:

```text
pg_dump is logical backup.
Barman/pgBackRest are usually used for physical backup + WAL.
They solve different problems and can both exist in one company.
```

Important rule:

```text
pg_dump + WAL is not a normal restore chain.
```

Why:

```text
pg_dump
  -> exports logical schema and rows
  -> restore creates new PostgreSQL data files

WAL
  -> belongs to PostgreSQL physical data files
  -> can be replayed only on a compatible physical base backup
```

So this works:

```text
physical base backup
  -> replay WAL
  -> recover to latest time or PITR target
```

This does not work:

```text
pg_dump
  -> pg_restore
  -> replay old WAL on top of restored dump
```

## PITR Lesson

PITR means Point-In-Time Recovery.

Use it when:

```text
bad delete
bad update
bad migration
data corruption
```

The idea:

```text
base backup
  -> replay WAL
  -> stop at targetTime before the bad change
```

Example from our drill:

```text
10:12:18 pitr-good-1 created
10:12:38 target time recorded
afterward pitr-bad-1 created
restore stopped at 10:12:38
```

Result:

```text
pitr-good-1 exists
pitr-bad-1 does not exist
```

The restore YAML controls this with:

```yaml
bootstrap:
  recovery:
    source: task-db-backup
    recoveryTarget:
      targetTime: "2026-08-16 10:12:38.65514+00"
```

`source: task-db-backup` is not a Kubernetes object. It is an alias inside the same YAML under `externalClusters`.

```text
task-db-backup
  -> MinIO endpoint
  -> s3://cnpg/task-db
  -> serverName: task-db
```

Production rule:

```text
Restore into a separate namespace or cluster first.
Validate data.
Then decide repair or cutover.
Never restore over live production blindly.
```

## No-Downtime Restore Pattern

Do not restore a backup directly over the live primary.

Safer production flow:

```text
live DB keeps running
  -> restore backup/PITR into side DB
  -> validate data
  -> choose repair or cutover
```

Repair path:

```text
side restored DB
  -> extract missing/correct rows
  -> apply controlled SQL patch to live DB
  -> avoid full app cutover
```

Cutover path:

```text
side restored DB
  -> stop or drain writes briefly
  -> switch app connection/pooler/DNS/service
  -> verify
  -> keep old DB for rollback window
```

Production note:

```text
True zero-downtime restore usually needs app-level design: backward-compatible schema, write pause/drain, CDC, dual-write, or repair scripts.
```

Future drill:

```text
Come back and practice live cutover in production form:
  -> live DB keeps serving writes
  -> restore side DB
  -> validate side DB
  -> drain or pause writes
  -> switch app connection/pooler/DNS
  -> verify
  -> keep old DB for rollback window
```

## Migration Safety

Database migrations must be safe while old and new app versions may both be running.

Risky migration:

```sql
alter table tasks add column priority text not null;
```

Problem:

```text
old rows do not have priority
old app does not send priority
new NOT NULL rule can break writes
```

Safer expand-and-contract flow:

```text
1. add nullable column
2. let app start writing the new column or add DB default
3. backfill old rows
4. verify no missing values
5. add NOT NULL constraint
6. later remove old schema only after old app versions are gone
```

Our lab:

```sql
alter table tasks add column if not exists priority text;
update tasks set priority='normal' where priority is null;
alter table tasks alter column priority set not null;
alter table tasks alter column priority set default 'normal';
```

Why the default mattered:

```text
task-service did not send priority yet
  -> NOT NULL alone broke old app writes
  -> default 'normal' kept old app compatible
```

Production rule:

```text
Schema migrations and app rollouts are one change plan.
Do not design them separately.
```

## Version Restore Rules

Logical backup:

```text
pg_dump from old version
  -> pg_restore into same or newer major version
```

Best practice:

```text
Use the newer PostgreSQL client tools when dumping for an upgrade.
Example: use pg_dump 17 when migrating PostgreSQL 15 -> 17.
```

Physical backup:

```text
base backup + WAL from PostgreSQL 15
  -> restore into PostgreSQL 15
```

Do not treat physical backups as normal cross-major-version migration files.

For major version upgrade, use:

```text
pg_dump / pg_restore
pg_upgrade
logical replication
managed database upgrade workflow
```

## Operator View

In this project, you do not manually create PostgreSQL pods.

You apply:

```text
Cluster/task-db
Pooler/task-db-pooler-rw
Backup/task-db-manual
ScheduledBackup/task-db-daily
```

CloudNativePG turns those custom resources into real pods, services, replication, failover, and backup jobs.

## Production Mindset

When database is slow or unsafe, ask in this order:

```text
1. Is the app healthy?
2. Is the pooler full?
3. Are queries slow?
4. Are queries blocked by locks?
5. Is replication lagging?
6. Is disk, CPU, or memory saturated?
7. Are backups and WAL archives healthy?
8. Can I restore from backup?
```

## Index Lesson

An index is not a label on the row. It is a separate lookup structure beside the table.

Table:

```text
tasks
------------------------------------------------
row address | id      | user_id | title
------------------------------------------------
page 8/1    | aaa     | u1      | task A
page 8/2    | bbb     | u2      | task B
page 9/1    | ccc     | db-lab  | task C
page 9/2    | ddd     | u3      | task D
```

Primary key index:

```text
tasks_pkey on id
------------------------------------------------
id  | row address
------------------------------------------------
aaa | page 8/1
bbb | page 8/2
ccc | page 9/1
ddd | page 9/2
```

When the query is:

```sql
select * from tasks where id = 'ccc';
```

PostgreSQL can use `tasks_pkey`:

```text
look in id index
  -> find ccc
  -> index returns page 9/1
  -> PostgreSQL reads that table row
```

Before we added a `user_id` index, this query had no shortcut:

```sql
select * from tasks where user_id = 'db-lab';
```

PostgreSQL did:

```text
Seq Scan
  -> read each row
  -> check user_id
  -> reject rows that do not match
```

The evidence was:

```text
Seq Scan on tasks
Rows Removed by Filter: 342
```

Then we created:

```sql
create index concurrently if not exists idx_tasks_user_id on tasks(user_id);
```

After that, the same query used:

```text
Index Scan using idx_tasks_user_id
Index Cond: user_id = 'db-lab'
```

Important rules:

```text
PostgreSQL chooses the index automatically when it thinks the index is cheaper.
Primary key creates an index automatically.
Indexes help reads but add storage and write cost.
Use create index concurrently for live production tables.
Do not index every column.
```

## Explain Analyze

`EXPLAIN ANALYZE` shows how PostgreSQL actually executed a query.

Common words:

```text
Seq Scan
  -> PostgreSQL scanned table rows

Index Scan
  -> PostgreSQL used an index to find row addresses

Rows Removed by Filter
  -> rows checked but rejected

Planning Time
  -> time spent choosing the plan

Execution Time
  -> time spent running the query
```

## Lock Lesson

A lock problem can make the app look broken even when PostgreSQL is alive.

The lab shape:

```text
terminal 1
  -> begin
  -> update row
  -> keep transaction open
  -> row stays locked

terminal 2
  -> update same row
  -> waits

terminal 3
  -> pg_stat_activity + pg_locks
  -> finds blocked and blocking query
```

Real production shapes:

```text
admin panel update
  -> opens transaction
  -> updates row
  -> waits on external API before commit
  -> row stays locked

unsafe migration
  -> ALTER TABLE locks table
  -> normal writes wait

background worker
  -> updates same rows as API
  -> API and worker block each other

forgotten psql transaction
  -> begin
  -> update
  -> terminal left open
  -> locks stay alive
```

Important states:

```text
active
  -> query is running

idle
  -> connection is open but not doing work

idle in transaction
  -> transaction is open but not doing work
  -> dangerous because locks can still be held

wait_event_type = Lock
  -> query is waiting for a lock
```

Core rule:

```text
Transactions must be short.
Do not hold DB transactions while waiting for network, user input, files, or external APIs.
```

## Vacuum, Analyze, And Bloat

PostgreSQL keeps old row versions when rows are updated or deleted.

Example:

```text
1000 rows inserted
  -> 1000 live tuples

1000 rows updated 3 times
  -> 1000 live tuples
  -> about 3000 dead tuples
```

Terms:

```text
live tuple
  -> current visible row version

dead tuple
  -> old row version left behind by update/delete

VACUUM
  -> cleans dead tuples so space can be reused

ANALYZE
  -> refreshes planner statistics

bloat
  -> table/index storage has grown with dead/reusable space
```

Stats are estimates:

```text
pg_stat_user_tables.n_live_tup
pg_stat_user_tables.n_dead_tup
```

Use `count(*)` when you need exact row count.

Our lab:

```text
exact tasks count: 1349
vacuum-lab rows: 1000
dead tuples after 3 updates: 3000
dead tuples after VACUUM ANALYZE: 0
```

Autovacuum:

```text
PostgreSQL can run VACUUM and ANALYZE automatically
when enough rows change.
```

Manual maintenance:

```sql
vacuum analyze tasks;
```

Important:

```text
VACUUM usually does not shrink the table file on disk.
It marks space as reusable for future writes.
```

`VACUUM FULL` can shrink files, but it takes stronger locks and can block production traffic.

Rule:

```text
VACUUM ANALYZE
  -> normal safe maintenance

VACUUM FULL
  -> planned/emergency maintenance only
```

## Replication Lag Lesson

PostgreSQL replicas receive and replay WAL from the primary.

Flow:

```text
primary accepts write
  -> primary creates WAL
  -> WAL streams to replicas
  -> replicas write/flush/replay WAL
  -> replicas eventually show same data
```

In this project:

```text
task-db-1
  -> primary

task-db-2
task-db-3
  -> replicas
```

A replica returns:

```sql
select pg_is_in_recovery();
```

Meaning:

```text
false -> primary
true  -> replica
```

Primary-side replication check:

```sql
select application_name,
       state,
       sync_state,
       sent_lsn,
       write_lsn,
       flush_lsn,
       replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) as bytes_lag
from pg_stat_replication;
```

How to read:

```text
state = streaming
  -> replica is connected and receiving WAL

sync_state = async
  -> primary does not wait for replica before confirming write

bytes_lag = 0
  -> replica replay position is caught up with sent WAL
```

Replica-side timestamp check:

```sql
select pg_is_in_recovery(),
       now() - pg_last_xact_replay_timestamp() as replay_delay;
```

Important:

```text
replay_delay means time since the last replayed transaction.
If the database is idle, this value can grow even when the replica is not behind.
For real lag, prefer primary-side LSN difference.
```

Async replication tradeoff:

```text
async
  -> faster writes
  -> small risk of losing the newest acknowledged writes if primary dies before replicas receive WAL

sync
  -> safer writes
  -> slower writes because primary waits for replica confirmation
```

Production terms:

```text
RPO
  -> how much data loss is acceptable

RTO
  -> how long recovery can take
```




### Important warning:
```
Replicas can be behind primary by milliseconds or seconds:
user creates task
  -> primary has it immediately
  -> replica may receive it slightly later
So not every read should go to replica.
```
`Rule:`
```
Need fresh data right after write? read from primary.
Can tolerate small delay? read from replica/cache.
```


# scalibility

```
1. Scale app pods
   -> more task-service pods handle HTTP/API work

2. Use PgBouncer
   -> protects primary from too many connections

3. Optimize queries and indexes
   -> primary does less work per request

4. Move read traffic to replicas
   -> GET/list/search/report queries can use task-db-ro

5. Cache hot reads in Redis
   -> avoid hitting PostgreSQL for repeated reads

6. Use async events
   -> Kafka moves non-request work outside user request path

7. Partition / shard when one primary is not enough
   -> split data across multiple primaries/databases

8. Use separate systems for heavy search/analytics
   -> Elasticsearch, ClickHouse, data warehouse, etc.
```

note:
`Only one primary accepts writes. Replicas do not normally accept writes.`
