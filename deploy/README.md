# Deploy

Runtime-specific deployment configuration that is not Kubernetes desired state.

- `compose/`: local Docker Compose support files.

Kubernetes remains under the root `k8s/` directory because it is the primary
GitOps deployment source.
