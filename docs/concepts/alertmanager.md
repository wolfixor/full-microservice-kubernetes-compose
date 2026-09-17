# Alertmanager

## What It Does

Prometheus detects problems.
Alertmanager decides what to do with those alerts.

```text
metrics
  -> Prometheus alert rule fires
  -> Alertmanager groups / deduplicates / routes / silences
  -> human or system gets notified
```

## Rule Vs Notification

Alert rule:

```text
condition is bad for enough time
```

Alert notification:

```text
send that alert somewhere useful
```

Flow:

```text
PrometheusRule
  -> Prometheus evaluates query
  -> alert becomes pending
  -> alert becomes firing after "for" duration
  -> Alertmanager receives firing alert
  -> Alertmanager groups / deduplicates / routes / silences
  -> receiver gets notification
```

If an alert appears in Prometheus but not in Alertmanager, check Prometheus `alerting.alertmanagers`.
If it appears in Alertmanager but nobody gets notified, check Alertmanager routes, labels, receivers, and silences.

## Routing

Alertmanager can route by labels:

```text
severity=page       -> wake someone
severity=ticket     -> create work
severity=dashboard  -> visible only
```

Every useful alert needs:

- owner
- severity
- runbook
- first debug command
- recovery action

## Grouping And Deduplication

Grouping prevents alert storms.

```text
10 pods down for same service
  -> one grouped alert
```

Deduplication prevents repeated identical notifications.

## Silences

A silence temporarily mutes known alerts during planned work.
It should always have a reason and an end time.

## Good Alert Shape

Good alert:

```text
users are impacted or impact is near
operator has a clear action
runbook explains first move
```

Bad alert:

```text
fires often
has no owner
has no action
is only interesting noise
```

## Symptom Vs Cause

Symptom alert:

```text
service is returning 5xx
```

Cause alert:

```text
database is unavailable
```

Production needs both, but pages should usually start from user impact or near-certain impact.

## Local Vs Production

Local receiver:

```text
local-dev-null
```

It proves routing works but does not notify anyone.

Production receiver:

```text
Slack / email / PagerDuty / Opsgenie / webhook
```

Production alerts must have:

- owner
- severity
- runbook
- clear action
- noise review after drills or incidents
