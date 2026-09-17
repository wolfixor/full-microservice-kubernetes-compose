# Docker Swarm Commands

Small local lab for PostgreSQL and pgAdmin.

## Init

```bash
docker swarm init
docker node ls
```

If Swarm is already enabled:

```bash
docker info | grep Swarm
```

## Deploy

```bash
docker stack deploy -c swarm/docker-stack.postgres-pgadmin.yml db-lab
```

Check:

```bash
docker stack ls
docker stack services db-lab
docker stack ps db-lab
docker service ls
```

## pgAdmin

Open:

```text
http://localhost:5051
```

Login:

```text
admin@local.dev
admin
```

Register server:

```text
host: postgres
port: 5432
database: task_db
user: postgres
password: postgres
```

Restore server:

```text
host: postgres-restore
port: 5432
database: task_db
user: postgres
password: postgres
```

## PostgreSQL Shell

Find task:

```bash
docker stack ps db-lab
```

Exec into the Postgres container:

```bash
docker ps --filter name=db-lab_postgres
docker exec -it <container_id> psql -U postgres -d task_db
```

Inside:

```sql
select now();
create table if not exists tasks (id text primary key, title text);
insert into tasks values ('swarm-1', 'hello swarm') on conflict (id) do nothing;
select * from tasks;
```

## Backup

Find the primary Postgres container:

```bash
docker ps --filter name=db-lab_postgres
```

Create a dump inside the shared backup volume:

```bash
docker exec -t <postgres_container_id> \
  pg_dump -U postgres -d task_db -Fc -f /backups/task_db.dump
```

Check backup file:

```bash
docker exec -it <postgres_container_id> ls -lh /backups
```

Do not `cat` a `-Fc` dump. It is a custom binary format.

Inspect dump contents:

```bash
docker exec -it <postgres_container_id> \
  pg_restore -l /backups/task_db.dump
```

Check the shared backup volume:

```bash
docker volume ls | grep postgres_backups
docker volume inspect db-lab_postgres_backups
```

## Restore To Side Database

Find restore container:

```bash
docker ps --filter name=db-lab_postgres-restore
```

Restore dump into side DB:

```bash
docker exec -it <restore_container_id> \
  pg_restore -U postgres -d task_db --clean --if-exists /backups/task_db.dump
```

Validate side DB:

```bash
docker exec -it <restore_container_id> \
  psql -U postgres -d task_db -c "select * from tasks;"
```

If the table does not exist after restore:

```text
Check that the source DB had the table before backup.
Check dump contents with pg_restore -l.
Check that you restored into the expected database.
```

Compare live DB:

```bash
docker exec -it <postgres_container_id> \
  psql -U postgres -d task_db -c "select * from tasks;"
```

Rule:

```text
Restore to postgres-restore first.
Validate.
Then decide repair or cutover.
Do not restore over live postgres first.
```

## WAL And PITR

Current Swarm lab:

```text
pg_dump
  -> no continuous WAL archive
  -> no point-in-time recovery
```

Production-style PITR needs PostgreSQL WAL archiving with Barman or pgBackRest.

Version rule:

```text
pg_dump/pg_restore can help move old -> new major versions.
Physical backup + WAL should restore to the same compatible PostgreSQL major version.
```

## Logs

```bash
docker service logs db-lab_postgres
docker service logs db-lab_pgadmin
```

## Scale

Do not scale PostgreSQL like a stateless service:

```text
docker service scale db-lab_postgres=3
```

This creates multiple independent PostgreSQL containers unless database-aware replication is configured. Do not use this as HA.

You can scale pgAdmin:

```bash
docker service scale db-lab_pgadmin=2
```

## Remove

```bash
docker stack rm db-lab
```

Leave Swarm mode if this is only a local lab:

```bash
docker swarm leave --force
```
