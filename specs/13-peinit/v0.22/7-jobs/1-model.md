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
                         |
                         +--> Failed
                         |
                         +--> Abandoned
```

| State | Meaning |
|---|---|
| Created | Job object exists but the process has not been forked yet (pre-exec hooks may be running). |
| Running | The main process is alive. |
| Completed | The process exited successfully (exit code 0 or configured success codes). |
| Failed | The process exited with a failure (non-zero exit, signal, timeout, health check failure). |
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
    pid:            pid_t?      // main process PID (null until forked)
    pidfd:          fd?         // pidfd for race-free tracking
    token_summary:  object      // identity (SID, groups, privileges)
    image_path:     string      // binary that was exec'd
    arguments:      string[]    // argv
    created_at:     timestamp   // when the job object was created
    started_at:     timestamp?  // when the process was forked
    ended_at:       timestamp?  // when the process exited
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
populated at fork time. The `ended_at`, `exit_code`, and
`exit_signal` are populated when the process exits.

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
  was already emitted to eventd.
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
structured event to eventd containing the full job record, then
drop the job from memory.

peinit does not maintain job history. eventd is the historian.

## eventd integration

peinit MUST emit structured events to eventd at each job lifecycle
transition:

**job.created** -- job object created. Includes job_id, service
name, type, image_path, identity, operation_id.

**job.started** -- process forked. Includes job_id, pid, cgroup
path.

**job.ended** -- process exited or was killed. Includes job_id,
final state, exit_code or exit_signal, duration, failure_cause.

All stdout/stderr from a job's process MUST be tagged with the job
GUID when forwarded to eventd. This allows queries like "show me
logs for job X" to return exactly the output from that execution,
not interleaved with previous or subsequent runs.
