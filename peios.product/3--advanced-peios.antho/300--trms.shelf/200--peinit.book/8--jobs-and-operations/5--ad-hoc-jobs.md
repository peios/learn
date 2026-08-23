---
title: Ad-Hoc Jobs
description: An arbitrary supervised process submitted by a service on behalf of its client — the delegation problem it solves, and its identity and lifecycle.
---

An ad-hoc job is an arbitrary supervised process submitted by a service
on behalf of its own client. It has no persistent definition: it runs
once, reports, and is cleaned up.

## The delegation problem

A service — a privileged action broker, say — wants peinit to run a
process as one of its users. It has impersonated that user's token, but
KACS will not let it forward that token over IPC without
Delegation-level impersonation. Fork inheritance works, because the
kernel copies the token naturally, but then the service has to supervise
the process itself, which defeats the point of having a service manager.

JFS — the Job Forwarding Subsystem — is the kernel's answer. It captures
the caller's effective token and delivers it, with a job definition, to
whatever holds `/dev/jfs` open. peinit is the consumer, and JFS is a
generic primitive rather than something built for peinit.

peinit opens `/dev/jfs` during Phase 1 infrastructure setup and adds the
descriptor to its event loop. If nothing has the device open, a
submitter's syscall returns `ENODEV`.

## The shape of a request

```
handle_jfs_request(request):
    (job_definition, token_fd) = read from /dev/jfs
    validate the image path, arguments, working directory
    job = Job { id: new_guid(), service: null, type: AdHoc,
                state: Created, token_summary: summarise(token_fd), ... }
    write job.id back to /dev/jfs        // unblocks the caller
    fork, install token_fd on the child, exec
    emit job.created, job.started, job.ended
```

## The definition

A subset of the service definition's fields, arriving as structured data
rather than as registry values:

| Field | Required | Meaning |
|---|---|---|
| ImagePath | yes | The binary to execute. |
| Arguments | no | Its arguments. |
| Environment | no | Additional variables, as a map rather than `KEY=VALUE` strings. |
| Timeout | no | Maximum runtime in seconds. 0 means no limit. |
| WorkingDirectory | no | Defaults to `/`. |
| Description | no | For logs. |

The service-level fields deliberately absent are the policy ones:
`RestartPolicy` and its parameters, the four dependency fields,
`HealthCheck`, `WatchdogTimeout`, `ErrorControl`, `SafeMode` and
`Triggers`. Those belong to a persistent definition; an ad-hoc job runs
once.

## Identity

The job runs with the token JFS captured — the caller's effective
identity at the moment of the syscall. An impersonating caller produces
a job running as the impersonated user; a caller using its own primary
token produces a job running as itself.

**There is no identity field.** A submitter cannot name an arbitrary
identity, only pass through the one it already holds. That is what stops
the mechanism being an escalation: a service cannot create jobs as
principals it could not already act as.

## Lifecycle

1. Forked with the JFS-provided token.
2. Runs in its own cgroup under `/sys/fs/cgroup/peinit/`, the id derived
   from the job's GUID rather than from a service name.
3. Output routed to eventd, tagged with the job's GUID.
4. On exit: emit `job.ended`, clean up the cgroup, drop the job.
5. No restart, no dependencies, no health checks.

Exceeding `Timeout` sends SIGTERM, waits the schema default
`StopTimeout` of 10 seconds, then SIGKILL — the same escalation as a
service stop.

Ad-hoc jobs bypass the operations model entirely. A JFS request creates
a job directly, because there is no service to start and therefore no
state machine action to represent:

```
Admin --> start command --> Operation --> peinit forks --> Job
Broker --> JFS request  -->              peinit forks --> Job
Timer --> timerfd fires --> Operation --> peinit forks --> Job
```

## The current state of JFS

JFS does not exist in the kernel. There is no `/dev/jfs` device, no
request encoding, and no mechanism for delivering a captured token
descriptor across a device read.

peinit's side is built up to that boundary and stops there. Phase 1
opens `/dev/jfs` if it is present, and a failure to open is a warning
that does not affect the boot. The descriptor is registered with the
event loop, and on the first readable event peinit reads nothing,
unregisters the descriptor and permanently disables the source.

The job machinery for ad-hoc jobs exists as far as the record: the job
type, the GUID-derived cgroup id, and a constructor. There is no launch
path — an ad-hoc job cannot currently be started — and the definition
fields above have no decoder to arrive through, so `Timeout`,
`Environment` and `WorkingDirectory` have nowhere to come from.

The byte-level `/dev/jfs` interface belongs to JFS rather than to
peinit, and this chapter describes the shape of the consumption
protocol rather than its encoding.
