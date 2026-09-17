# bash

### disk
```
lsblk
df -h
```



### kubernetes
```
kubectl exec -n task-api task-service-db-0 -- \
  sh -c 'PGPASSWORD=postgres psql -U postgres -d task_db -c "select count(*) from tasks;"'

```

```
kubectl get storageclass
```

```
kubectl exec -it task-api-6bcfdff564-26rfr -n task-api -- bash

kubectl exec -it task-api-redis-7674d97f5d-dtc8h -n task-api -- redis-cli

kubectl exec -it task-api-548f94978d-clbsz -n task-api -- curl http://localhost:8000/health
```

```
kubectl exec -it task-api-6bcfdff564-m2rl5 -n task-api -- bash -c 'timeout 3 bash -c "echo > /dev/tcp/postgres/5432" && echo OPEN || echo CLOSED'
note:
/dev/tcp/HOST/PORT isn't a real file â€” it's a special bash feature (built into bash itself, not the filesystem). When bash sees a redirection involving a path matching /dev/tcp/host/port, instead of opening a file it opens a TCP socket to that host:port.
So echo > /dev/tcp/postgres/5432 literally means: "bash, open a TCP connection to host postgres on port 5432, and write the output of echo (just a newline) into that connection."

If the connection succeeds (TCP handshake completes), the redirection succeeds â†’ exit code 0 â†’ OPEN.
If the connection is refused or times out, the redirection fails â†’ exit code nonzero â†’ CLOSED.

```


### docker

```
docker exec -it task-api-task-api-db-1 psql -U postgres -d task_db -c "\dt"
```

```
docker service ps gnaf_log-filebeat8 --no-trunc
```

```
docker service update \
  --image registry.gitlab.shiveh.com/gnaf/devops/web-school-pwa:release \
  gnaf_web-school-pwa
```

```
docker service inspect gnaf_openresty --pretty
```
