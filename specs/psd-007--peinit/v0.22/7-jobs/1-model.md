---
title: Job Model
---

A job is a single supervised process execution. Every time peinit
forks a process -- starting a service's main binary, running a
pre-exec hook, executing a health check, or handling an ad-hoc run
request -- that execution is a job with a GUID, lifecycle tracking,
and log correlation.

Jobs are the observable unit of "what actually ran." Services are
definitions that encode identity, policy, and configuration. Jobs
are execution instances. A service restart creates a new job. Job
history is visible via eventd.

## Lifecycle

```
Created --> Running --> Completed
   |                     |
   +--> Failed          +--> Failed
                         |
                         +--> Abandoned
```

| State | Meaning |
|---|---|
| Created | Job object exists but exec has not yet succeeded. The process may not have been forked yet, or it may be in pending post-fork setup while the error pipe is unresolved. |
| Running | Exec has succeeded and the job process is alive. |
| Completed | The process exited successfully (exit code 0 or configured success codes). |
| Failed | The process failed, or peinit classified the job as failed before fork because parent setup failed. |
| Abandoned | The process survived SIGKILL (D-state). |

Job states are simpler than service states. A service has Starting,
Active, Stopping, Reloading, etc. because those represent policy.
A job tracks a process: it is running, or it finished, or it is
stuck.

## Fields

```
Job {
    id:             GUID        // unique identifier
    service:        string?     // parent service name (null for ad-hoc)
    type:           enum        // ServiceMain, PreExecHook,
                                // PostExecHook, HealthCheck, AdHoc
    state:          enum        // Created, Running, Completed,
                                // Failed, Abandoned
    pid:            pid_t?      // main process PID (null until exec succeeds)
    pidfd:          fd?         // pidfd for race-free tracking
    resolved_identity:
                    string      // resolved service, hook, or submitter
                                // identity string
    token_summary:  object      // identity (SID, groups, privileges)
    image_path:     string      // binary that was exec'd
    arguments:      string[]    // argv
    created_at:     timestamp   // when the job object was created
    started_at:     timestamp?  // when exec success was confirmed
    ended_at:       timestamp?  // when the process exited, or when
                                // peinit classified the job terminal
    exit_code:      int?        // exit code (null if signal death)
    exit_signal:    int?        // signal (null if clean exit)
    failure_cause:  string?     // structured cause
    cgroup_id:      string      // cgroup path
    cgroup_gen:     int         // cgroup generation number
    operation_id:   GUID?       // the operation that created this
                                // job (null for ad-hoc jobs)
}
```

The `id` MUST be assigned before fork. The `pid` and `pidfd` are
held in pending setup state after fork and are populated on the job
record only after exec success is confirmed by EOF on the error
pipe. If parent setup fails before fork, or child setup fails before
exec, the job transitions directly from Created to Failed; `ended_at`
records the classification time, `failure_cause` records the setup
failure cause, and `pid`, `pidfd`, `started_at`, `exit_code`, and
`exit_signal` remain null. The `ended_at` field is otherwise
populated when the process exits, or when peinit classifies the job
as terminal without observing process exit. The `exit_code` and
`exit_signal` fields are populated only when the process exits. For
Abandoned jobs, `ended_at` records the time peinit ended supervision
and classified the job as terminal; `exit_code` and `exit_signal`
remain null.

The `resolved_identity` field records the resolved identity string used
for the execution. It is distinct from `token_summary`, which records
the resulting SID, groups, and privileges. Status views and job-created
payloads that expose `identity` use this resolved identity string.

## Job types

### ServiceMain

The main process of a service. Created when a start operation
executes the fork/exec sequence. The service tracks its current
ServiceMain job GUID. On restart, a new job is created and the
service's job GUID updates.

### PreExecHook

A pre-exec hook command (ExecStartPre). Each hook invocation is a
separate job. Hook jobs run in the `hooks/` sub-cgroup.

### PostExecHook

A post-exec hook command (ExecStartPost). Each hook invocation is
a separate job. Hook jobs run in the `hooks/` sub-cgroup.

### HealthCheck

A periodic health check invocation. Each health check run is a
separate job. Health check jobs run in the `health/` sub-cgroup.

### AdHoc

An arbitrary process submitted via JFS. Not associated with a
persistent service definition. Runs once, reports result. See the
Ad-Hoc Jobs section.

## Relationship to services

A service is a long-lived definition with policy. A job is a
short-lived process execution.

- A service tracks its **current job GUID**. Status queries include
  it.
- When a service restarts, a new job is created. The old job's data
  was already emitted as a KMES event.
- Job history for a service is queryable via eventd.

### Ownership

| Concern | Owner |
|---|---|
| Restart policy | Service |
| Dependencies | Service |
| Health check schedule | Service |
| ErrorControl | Service |
| Current state (Active, Failed, etc.) | Service |
| Process PID / pidfd | Job |
| Exit code / signal | Job |
| Execution timestamps | Job |
| Log correlation | Job |
| Identity / token | Job |
| cgroup assignment | Job |

## Retention

peinit tracks active jobs in memory. When a job reaches a terminal
state (Completed, Failed, Abandoned), peinit MUST emit a
structured event via KMES (`kmes_emit`) containing the full job
record, then drop the job from memory.

peinit does not maintain job history. eventd is the historian --
it consumes these events from the KMES kernel ring buffer.

## Event emission

peinit MUST emit structured events via KMES (`kmes_emit` /
`kmes_emit_batch`; eventd consumes them from the kernel ring
buffer, not over any socket from peinit -- see §11.1) at each job
lifecycle transition:

**job.created** -- job object created. Includes job_id, service
name, type, image_path, identity, operation_id.

**job.started** -- process forked. Includes job_id, pid, cgroup
path.

**job.ended** -- process exited or was killed. Includes job_id,
final state, exit_code or exit_signal, duration, failure_cause.

The event `type` is the dotted string above (`job.created`, …); the
listed per-event fields form the event **payload**, encoded as
msgpack per the KMES event-record format (PSD-003). The same
encoding applies to the operation events in §8.1.

All stdout/stderr from a job's process MUST be forwarded to
eventd's log socket with the job's GUID in the log record's
`job_id` field (PSD-008 §4.2) -- this is the log path, distinct
from the KMES event path above. It allows queries like "show me
logs for job X" to return exactly the output from that execution,
not interleaved with previous or subsequent runs.
