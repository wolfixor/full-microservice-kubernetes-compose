# Services

Each directory is an independently buildable application and owns its source,
tests, dependency list, migrations, Dockerfile, and example environment file.

Kubernetes resources do not live here. They are owned by `k8s/apps` so image
builds and cluster delivery remain separate concerns.
