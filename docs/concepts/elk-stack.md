# Kong, Fluent Bit, and Elasticsearch Log Flow

## Mental Model

Kong does not send logs directly to Elasticsearch.

Everything first becomes container stdout or stderr. Fluent Bit reads those node log files, enriches them, and sends them to Elasticsearch. Kibana only reads from Elasticsearch.

```text
container stdout/stderr
  -> /var/log/containers/*.log
  -> Fluent Bit
  -> Elasticsearch
  -> Kibana
```

## Request Path

```text
Client
  -> NodePort 30085
  -> Kong
  -> app service
```

Example:

```text
Client -> Kong -> user-service
```

## Log Path

For the same request, logs can come from multiple containers:

```text
Kong stdout
app service stdout
kong-log-receiver stdout
```

Fluent Bit reads all of them from:

```text
/var/log/containers/*.log
```

## Why kong-log-receiver Exists

Kong already writes normal access logs to stdout. Fluent Bit can read those.

The `http-log` plugin is extra. It sends a richer request event to:

```text
http://kong-log-endpoint:8001/
```

That endpoint is the `kong-log-receiver` service. The receiver converts Kong's HTTP log event into clean JSON and prints it to stdout.

So the second Kong log path is:

```text
Kong http-log plugin
  -> kong-log-receiver
  -> receiver stdout
  -> Fluent Bit
  -> Elasticsearch
```

The receiver is not replacing Fluent Bit. It only creates better structured stdout logs for Kong requests.

## Fluent Bit Pipeline

Fluent Bit runs this flow:

```text
INPUT tail
  -> kubernetes filter
  -> lua filter
  -> modify filter
  -> Elasticsearch output
```

## Kubernetes Filter

This happens inside Fluent Bit after it reads a log line.

It adds Kubernetes metadata:

```text
pod_name
namespace
container_name
host
```

It also merges JSON logs into fields when `merge_log on` is enabled.

## Lua Filter

This also happens inside Fluent Bit.

It does custom cleanup:

```text
container_name: user-service -> service: user-service
container_name: kong-gateway -> service: kong
container_name: postgres -> service: postgresql
```

It also tries to parse non-JSON logs, like Kong access logs, PostgreSQL logs, and Redis logs.

## Modify Filter

This copies useful Kubernetes metadata to top-level fields and removes the nested Kubernetes object.

Example:

```text
kubernetes.pod_name -> pod_name
kubernetes.namespace -> namespace
```

## Elasticsearch Output

Fluent Bit sends the final documents to:

```text
elasticsearch-es-http:9200
```

The index name is daily:

```text
kubernetes-logs-YYYY.MM.DD
```

In Kibana, use:

```text
kubernetes-logs-*
```

## One Request, One Search

Kong creates a request ID:

```text
Kong-Request-ID
```

The app services include that ID in their logs.

In Kibana, search:

```text
request_id: "<id>"
```

That should show the related Kong and app logs for the same request.

