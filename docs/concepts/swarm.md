# Docker Swarm

Docker Swarm is Docker's built-in orchestrator.

Core objects:

```text
Swarm cluster
  -> manager nodes
  -> worker nodes
  -> services
  -> tasks
  -> overlay networks
  -> volumes
```

Stack name:

```text
docker stack deploy ... db-lab
```

`db-lab` is the stack name, not the Swarm cluster name.

Swarm then creates services like:

```text
db-lab_postgres
db-lab_pgadmin
```

And tasks like:

```text
db-lab_postgres.1
db-lab_pgadmin.1
```

Kubernetes comparison:

```text
Kubernetes Deployment
  -> Swarm service

Kubernetes Pod
  -> Swarm task/container

Kubernetes Service
  -> Swarm service discovery / routing mesh

Kubernetes Namespace
  -> Swarm stack name separation

Kubernetes Operator / CRD
  -> no direct Swarm equivalent
```

Important PostgreSQL difference:

```text
Kubernetes with CNPG
  -> operator manages primary, replicas, failover, backups, PITR

Docker Swarm
  -> runs containers and services
  -> PostgreSQL HA/backup/failover must be designed separately
```

So Swarm is useful to learn:

```text
service scheduling
replicas
overlay networking
rolling updates
service logs
stack deploy
```

But for production PostgreSQL, Swarm alone is not equal to CNPG.

Production rule:

```text
Do not assume a replicated Swarm service makes PostgreSQL HA.
PostgreSQL needs database-aware replication, backup, failover, and restore.
```

## Swarm Backup Model

In this local Swarm lab, backup is simple:

```text
postgres service
  -> pg_dump
  -> file in postgres_backups volume
  -> restore into postgres-restore service
  -> validate data
```

This teaches backup and restore mechanics, but it is not the same as CNPG:

```text
CNPG
  -> base backup
  -> continuous WAL archive
  -> PITR
  -> operator-managed restore

Swarm lab
  -> pg_dump file
  -> manual restore
  -> no automatic PITR
```

The shared `/backups` path is a Docker named volume:

```text
postgres container
  -> writes /backups/task_db.dump

postgres-restore container
  -> reads /backups/task_db.dump
```

The file survives container restart, but it is still local Docker storage. It is not a real off-cluster backup.

## WAL In Swarm

Swarm does not automatically configure PostgreSQL WAL archive.

Current local Swarm flow:

```text
pg_dump
  -> restore dump
  -> no PITR
```

Production Swarm/PostgreSQL needs extra database-aware backup tooling:

```text
PostgreSQL archive_mode=on
  -> archive WAL with Barman or pgBackRest
  -> store backups in remote repository
  -> restore base backup + WAL
```

Production rule:

```text
For large live PostgreSQL, pg_dump alone is usually not enough.
Use database-aware tools such as Barman, pgBackRest, WAL archive, storage snapshots, or managed database backups.
```

Version rule:

```text
pg_dump/pg_restore
  -> useful for version migration

physical backup + WAL
  -> restore to compatible PostgreSQL major version
```
