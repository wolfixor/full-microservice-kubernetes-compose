
```
| Component                                                        | What it Monitors         | Main Question                                      |
| ---------------------------------------------------------------- | ------------------------ | -------------------------------------------------- |
| **API Server**                                                   | Kubernetes Control Plane | **Is Kubernetes itself healthy?**                  |
| **Kubelet**                                                      | Node Agent               | **Is the node agent working correctly?**           |
| **cAdvisor**                                                     | Containers               | **Which container is using CPU/RAM/Disk/Network?** |
| **Node Exporter**                                                | Linux Host               | **Is the server healthy?**                         |
| **kube-state-metrics**                                           | Kubernetes Objects       | **What does Kubernetes think exists?**             |
| **Application Exporters** (Postgres, Redis, Elasticsearch, etc.) | Individual applications  | **Is my application/database healthy?**            |
| **Kong Gateway**                                                 | API Gateway              | **How is client traffic flowing?**                 |
```

```
Memory Map
                Kubernetes Cluster
                       │
        ┌──────────────┴──────────────┐
        │                             │
   API Server                    kube-state-metrics
   (K8s Brain)                    (K8s Objects)

                       │
                  Worker Node
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Kubelet         cAdvisor     Node Exporter
   (Agent)       (Containers)   (Linux Host)

                       │
              Running Applications
        ┌──────────────┼──────────────┐
        │              │              │
   Postgres       Redis        Elasticsearch
      │              │              │
 Postgres Exp.   Redis Exp.   Elasticsearch Exp.
      │              │              │
      └──────────────┼──────────────┘
                     │
               Application Metrics

                       │
                 Kong Gateway
                 (Client Traffic)
```

### One-line cheat sheet:
```
API Server → Kubernetes Brain
Kubelet → Node Agent
cAdvisor → Containers
Node Exporter → Linux Host
kube-state-metrics → Kubernetes Objects
Application Exporters → Application Internals (DB stats, cache hits, JVM metrics, etc.)
Kong → Traffic
```