---
title: Ad-Hoc Jobs
---

Ad-hoc jobs are arbitrary supervised processes submitted by
services on behalf of their clients. They are not associated with
a persistent service definition. They run once, report their
result, and are cleaned up.

## The delegation problem

When a service (e.g., PAC) wants peinit to run a process on behalf
of a user, it faces a delegation problem. The service has
impersonated the user's token, but KACS prevents forwarding that
token over IPC without Delegation-level impersonation. Fork
inheritance works (the kernel copies the token naturally), but then
the service must supervise the process itself -- defeating the
purpose of centralised job management.

## JFS consumption protocol

JFS (Job Forwarding Subsystem) solves this problem at the kernel
level. JFS is a PKM subsystem that captures the caller's effective
KACS token and delivers it to peinit via `/dev/jfs`.

peinit MUST open `/dev/jfs` during Phase 1 infrastructure setup
(after /dev is mounted) and add the fd to its event loop. When a JFS request
arrives:

```
handle_jfs_request(request):
    // Step 1: Read the request.
    (job_definition, token_fd) = read from /dev/jfs

    // Step 2: Validate the request.
    if job_definition.image_path does not exist:
        write error to /dev/jfs  // unblocks caller
        return
    // Validate arguments, working directory, etc.

    // Step 3: Create job object.
    job = Job {
        id: generate_guid(),
        service: null,   // ad-hoc, no parent service
        type: AdHoc,
        state: Created,
        token_summary: summarise(token_fd),
        image_path: job_definition.image_path,
        arguments: job_definition.arguments,
        created_at: now(),
        operation_id: null,
    }

    // Step 4: Respond to caller.
    write job.id to /dev/jfs  // unblocks caller's syscall

    // Step 5: Execute.
    fork, install token_fd on child, exec
    // Normal supervision: cgroup, log routing, exit tracking.

    // Step 6: Emit lifecycle events.
    emit job.created, job.started, job.ended to eventd
```

If nothing has `/dev/jfs` open, the caller's syscall returns
ENODEV. JFS is a generic secure forwarding primitive -- peinit
happens to be the consumer.

## Ad-hoc job definition

The JFS request contains a job definition with a subset of service
definition fields:

| Field | Type | Required | Description |
|---|---|---|---|
| ImagePath | string | yes | Binary to execute. |
| Arguments | string[] | no | Command-line arguments. |
| Environment | map (string -> string) | no | Additional environment variables as key-value pairs. Unlike the service definition's Environment field (registry multi_string of KEY=VALUE entries), ad-hoc job definitions arrive via JFS as structured data. |
| Timeout | dword | no | Maximum runtime in seconds. 0 = no limit. |
| WorkingDirectory | string | no | Working directory. Default: `/`. |
| Description | string | no | Human-readable description for logs. |

The following service-level fields are NOT available for ad-hoc
jobs. These are policy concerns that belong to persistent service
definitions:

- RestartPolicy, RestartDelay, RestartMaxRetries, RestartWindow
- Requires, Wants, BindsTo, Conflicts
- HealthCheck, WatchdogTimeout
- ErrorControl, SafeMode
- Triggers

## Identity

The job runs with the token captured by JFS -- the caller's
effective identity at the time of the syscall. If the caller is
impersonating a user, the job runs as that user. If the caller is
using its own primary token, the job runs as the caller.

No identity field is accepted in the ad-hoc job definition. The
caller MUST NOT name an arbitrary identity -- the caller can only
pass through its own (possibly impersonated) token. This prevents
escalation: a service cannot create jobs with identities it does
not already possess.

## Lifecycle

Ad-hoc jobs have a simpler lifecycle than service jobs:

1. Process is forked with the JFS-provided token.
2. Process runs in a dedicated cgroup under
   `/sys/fs/cgroup/peinit/` (cgroup-id derived from the job GUID).
3. stdout/stderr routed to eventd, tagged with job GUID.
4. On exit: emit job.ended event, clean up cgroup, drop job from
   memory.
5. No restart. No dependencies. No health checks.

If the process exceeds its Timeout, peinit MUST send SIGTERM, wait
the schema default StopTimeout (10 seconds), then SIGKILL. The
same escalation as service stops.

## Ad-hoc jobs and operations

Ad-hoc jobs bypass the operations model entirely. The JFS request
creates a job directly -- there is no "start" operation for an
ad-hoc job because there is no service to start. The job IS the
entire lifecycle.

```
Admin --> start command --> Operation --> peinit forks --> Job
PAC   --> JFS request   -->              peinit forks --> Job
Timer --> timerfd fires  --> Operation --> peinit forks --> Job
```
