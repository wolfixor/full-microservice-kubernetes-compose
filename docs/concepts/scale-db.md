# PostgreSQL Architecture and Scaling

###Run these:
```
kubectl get cluster -n task-api
kubectl get pooler -n task-api
kubectl get pods -n task-api -l cnpg.io/cluster=task-db
kubectl get svc -n task-api | Select-String task-db
```
```
Ã¢Å¾Å“  ~ kubectl get cluster -n task-api

NAME      AGE     INSTANCES   READY   STATUS                     PRIMARY
task-db   2d22h   3           3       Cluster in healthy state   task-db-1
```
```
Ã¢Å¾Å“  ~ kubectl get pooler -n task-api

NAME                AGE     CLUSTER   TYPE   PHASE
task-db-pooler-rw   2d22h   task-db   rw     active
```
```
Ã¢Å¾Å“  ~ kubectl get pods -n task-api -l cnpg.io/cluster=task-db

NAME                                 READY   STATUS    RESTARTS       AGE
task-db-1                            1/1     Running   2 (2d3h ago)   2d22h
task-db-2                            1/1     Running   2 (2d3h ago)   2d22h
task-db-3                            1/1     Running   2 (2d3h ago)   2d22h
task-db-pooler-rw-549564465f-6pn29   1/1     Running   4 (2d3h ago)   2d22h
task-db-pooler-rw-549564465f-q9rgw   1/1     Running   4 (2d3h ago)   2d22h
```
```
Ã¢Å¾Å“  ~ kubectl get svc -n task-api | grep task-db
task-db-pooler-rw                ClusterIP   10.96.94.184    <none>        5432/TCP                      2d22h
task-db-r                        ClusterIP   10.96.248.122   <none>        5432/TCP                      2d22h
task-db-ro                       ClusterIP   10.96.185.19    <none>        5432/TCP                      2d22h
task-db-rw                       ClusterIP   10.96.141.70    <none>        5432/TCP                      2d22h
```



### CloudNativePG CR:
```
task-db
  -> desired PostgreSQL cluster
  -> 3 instances
  -> primary is task-db-1
```
### Real pods:
```
task-db-1  -> PostgreSQL primary right now
task-db-2  -> replica
task-db-3  -> replica
```
### Pooler pods:
```
task-db-pooler-rw-... -> PgBouncer pod 1
task-db-pooler-rw-... -> PgBouncer pod 2
```
### Services:
```
task-db-pooler-rw
  -> service used by task-service
  -> points to PgBouncer pods
```
### task-db-rw
```
  -> write service
  -> points to current primary: task-db-1
```
### task-db-ro
```
  -> read-only service
  -> points to replicas
```

### task-db-r
```
  -> all database instances
```
### So the real app DB path is:
```
task-service pod
  -> task-db-pooler-rw
  -> PgBouncer pod
  -> task-db-rw
  -> task-db-1 primary
```
`Important:`
```
 task-db-1 is primary now, but in failover it can change. The app does not care because it talks to task-db-pooler-rw / task-db-rw, not a fixed pod name.
```

`prove primary vs replica from inside PostgreSQL:`
```
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h task-db-rw -U task_app -d task_db \
  -c "select inet_server_addr(), pg_is_in_recovery();"
```

### What this checks:
```
cluster -> CloudNativePG PostgreSQL cluster object
pooler  -> PgBouncer object
pods    -> real PostgreSQL pods
svc     -> database access points
```
### You should expect something like:
```
task-db              Cluster in healthy state
task-db-pooler-rw    active
task-db-1/2/3         Running
task-db-rw           primary write service
task-db-ro           replica read service
task-db-r            all instances service
task-db-pooler-rw    PgBouncer service used by task-service
```
### The key idea:
```
task-service does NOT connect directly to task-db-1
task-service connects to task-db-pooler-rw
PgBouncer connects to task-db-rw
task-db-rw points to the current primary
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


### For "Instagram-size" traffic, one PostgreSQL primary for everything is not enough. They use combinations of:
```
sharding
read replicas
caches
queues
denormalized read models
separate search/index systems
partitioning
massive observability
careful schema changes
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


check the primary db by hand:
```
kubectl exec -n task-api task-db-1 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h 127.0.0.1 -U task_app -d task_db \
  -c "select inet_server_addr(), pg_is_in_recovery();"

kubectl exec -n task-api task-db-2 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h 127.0.0.1 -U task_app -d task_db \
  -c "select inet_server_addr(), pg_is_in_recovery();"

kubectl exec -n task-api task-db-3 -- \
  env PGPASSWORD=${TASK_DB_PASSWORD} \
  psql -h 127.0.0.1 -U task_app -d task_db \
  -c "select inet_server_addr(), pg_is_in_recovery();"
```

```
pg_is_in_recovery = false -> primary
pg_is_in_recovery = true  -> replica
```


### About pg_is_in_recovery():
`PostgreSQL has two roles:`
```
primary
  -> accepts writes
  -> not replaying WAL from another server
```

`replica`
```
  -> receives WAL from primary
  -> replays those changes
  -> is "in recovery" mode
```
`So:`
```
pg_is_in_recovery() = false
  -> this PostgreSQL is primary
  -> it can accept writes
```
```
pg_is_in_recovery() = true
  -> this PostgreSQL is replica
  -> it is replaying WAL from primary
  -> normally read-only
```
