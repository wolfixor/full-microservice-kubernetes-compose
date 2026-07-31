# Argo Rollouts Task Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the normal `task-service` Deployment path with an Argo Rollouts canary release path.

**Architecture:** Argo Rollouts manages `task-service` ReplicaSets through a `Rollout` CR. Prometheus is queried through an `AnalysisTemplate` after each canary step to stop bad releases automatically.

**Tech Stack:** Kubernetes, Argo Rollouts v1.9.0, Prometheus Operator, FastAPI metrics.

## Global Constraints

- Keep existing APIs unchanged.
- Keep Kong routing pointed at `task-service.task-api.svc`.
- Start with `task-service` only before copying the pattern to other services.
- Use Prometheus metrics for automatic rollout checks.

---

### Task 1: Add Argo Rollouts Controller Docs

**Files:**
- Create: `k8s/argo-rollouts/install.md`

**Interfaces:**
- Consumes: Kubernetes cluster access.
- Produces: documented controller install command for Argo Rollouts CRDs.

- [x] **Step 1: Add install commands**

Use pinned Argo Rollouts v1.9.0 install URL.

- [x] **Step 2: Add verification commands**

Show `kubectl get pods -n argo-rollouts` and CRD checks.

### Task 2: Add Prometheus AnalysisTemplate

**Files:**
- Create: `task-service/k8s/analysis-template.yaml`

**Interfaces:**
- Consumes: `http_requests_total` and `http_request_duration_seconds_bucket` from task-service metrics.
- Produces: `task-service-success-rate` AnalysisTemplate.

- [x] **Step 1: Add error-rate check**

Fail when 5xx rate is 5% or higher.

- [x] **Step 2: Add latency check**

Fail when p95 latency is 500ms or higher.

### Task 3: Add Task Service Rollout

**Files:**
- Create: `task-service/k8s/rollout.yaml`

**Interfaces:**
- Consumes: existing task-service environment variables, probes, image, and Service contract.
- Produces: `Rollout/task-service` with 10%, 25%, 50%, 100% canary steps.

- [x] **Step 1: Copy current Deployment pod template**

Keep database, Redis, Kafka, probe, and image settings unchanged.

- [x] **Step 2: Add canary strategy**

Use `setWeight`, `pause`, and Prometheus analysis between steps.

- [x] **Step 3: Preserve service name**

Keep `Service/task-service` so Kong does not need to change.

### Task 4: Add Learning Doc

**Files:**
- Create: `docs/argo-rollouts.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: rollout and analysis manifests.
- Produces: short explanation and deploy commands.

- [x] **Step 1: Explain the rollout flow**

Document new image -> canary -> Prometheus checks -> promotion/rollback.

- [x] **Step 2: Add commands**

Document install, apply, watch, and verify commands.
