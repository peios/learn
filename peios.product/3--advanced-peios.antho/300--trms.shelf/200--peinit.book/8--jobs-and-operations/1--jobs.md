---
title: Jobs
description: A job is one supervised process execution, and every fork peinit performs is one — its lifecycle, fields, retention and ownership.
---

A job is one supervised process execution. Every fork peinit performs is
a job: a service's main binary, a pre-exec hook, a post-exec hook, a
reload command, a health check invocation, an ad-hoc submission.

Jobs are the observable unit of *what actually ran*. Services are
definitions carrying identity, policy and configuration; jobs are
instances. A restart creates a new job.

## Lifecycle

```
Created --> Running --> Completed
   |           |
   |           +------> Failed
   |           |
   |           +------> Abandoned
   +------------------> Failed
```

| State | Meaning |
|---|---|
| Created | The job object exists but exec has not succeeded. The process may not have been forked, or it may be in pending post-fork setup with the error pipe unresolved. |
| Running | Exec succeeded and the process is alive. |
| Completed | The process exited successfully — code 0, or one in `SuccessExitCodes`. |
| Failed | The process failed, or peinit classified the job failed before the fork because parent setup failed. |
| Abandoned | The process survived SIGKILL. |

Job states are simpler than service states because they describe a
process rather than a policy. A service has Starting, Reloading and
Backoff because those are decisions; a job is running, or it finished,
or it is stuck.

## Fields

```
Job {
    id:                 GUID       // UUIDv7
    service:            string?    // null for ad-hoc
    job_type:           enum       // ServiceMain, PreExecHook, PostExecHook,
                                   // ReloadHook, HealthCheck, AdHoc
    state:              enum
    pid:                u32?
    pidfd:              fd?
    resolved_identity:  string     // the resolved service, hook or submitter identity
    token_summary:      object     // the resulting SID, groups, privileges
    image_path:         string
    arguments:          string[]
    created_at_ns:      u64
    started_at_ns:      u64?
    ended_at_ns:        u64?
    exit_code:          i32?
    exit_signal:        i32?
    failure_cause:      string?
    cgroup_id:          string
    cgroup_generation:  u32
    activation_generation: u32
    operation_id:       GUID?      // null for ad-hoc
    hook_index:         u32?
}
```

The rules that govern when the nullable fields are populated are what
make a job record trustworthy:

- `id` is assigned **before** the fork, so a job that never forks still
  has an identity.
- `pid` and `pidfd` land on the record only once exec success is
  confirmed by EOF on the error pipe. Until then they are held in
  pending setup state and the job is Created.
- A setup failure takes the job straight from Created to Failed.
  `ended_at_ns` records the **classification** time, `failure_cause`
  records what went wrong, and `pid`, `pidfd`, `started_at_ns`,
  `exit_code` and `exit_signal` all stay null. There was no process to
  have a PID or an exit status.
- `exit_code` and `exit_signal` are populated only when peinit observed
  an exit — never both, since a process either exits or is killed.
- For an Abandoned job, `ended_at_ns` records when peinit stopped
  supervising, and the exit fields stay null. Nothing exited.

`resolved_identity` is the identity *string* — `SYSTEM`,
`LocalService`, a SID — that was resolved for the execution.
`token_summary` is what the resulting token actually contains. They are
separate because they can differ, and the `identity` field exposed in
status views and job events is the former.

## Retention

peinit tracks active jobs in memory. When a job reaches a terminal state
it emits a structured event carrying the full record and then **drops**
the job. There is no job history in peinit, and no structure that could
hold one.

eventd is the historian. It consumes those events from the KMES kernel
ring buffer, and a query for a service's past jobs is a query to eventd.

## Ownership

| Concern | Owner |
|---|---|
| Restart policy, dependencies, health check schedule, `ErrorControl` | Service |
| Current state — Active, Failed, … | Service |
| PID, pidfd, exit code, exit signal | Job |
| Execution timestamps | Job |
| Identity and token | Job |
| cgroup assignment | Job |
| Log correlation | Job |

A service tracks its current main job's identifier, and a status query
returns it.
