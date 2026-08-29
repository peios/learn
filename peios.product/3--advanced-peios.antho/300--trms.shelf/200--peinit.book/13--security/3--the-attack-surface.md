---
title: The Attack Surface
description: What the socket descriptors mean in practice, and what the autorun directory exposes.
---

| Surface | Reachable by | Controls | Protected by |
|---|---|---|---|
| Control socket | Anything that can connect | Service lifecycle, shutdown, observing and stopping jobs | The socket inode's descriptor, then the peer token and AccessCheck against the target's descriptor |
| Jobs socket | Every authenticated principal, by default | Running a program under supervision as an identity the submitter holds; managing the jobs it submitted | The socket inode's descriptor, which is the whole of the submission permission; the kernel's gating of the attached token; the job's own descriptor for every later command; a per-submitter quota |
| Notification socket | Anything that can connect | Service readiness, watchdog, stored descriptors | The socket inode's descriptor, then PID matching verified through a pidfd, plus the start generation |
| Registry keys | Anything with registry access | Definitions, triggers, configuration | Registry key descriptors, enforced by LCS |
| `Machine\System\Init\EnvVars\` | Anything with registry access | The environment of every service | That key's descriptor, and nothing else — variable names are not filtered |
| Service cgroups | peinit | Process tracking and clean kill | Ownership of the hierarchy |
| Phase 1 mounts | peinit | Virtual filesystem availability | Hardcoded, no external input |
| `/lcl/policy/autorun.d` | Whatever can write it | Arbitrary code as SYSTEM in early boot | The directory's descriptor |
| Boot attempt counter | Whatever can write `/.peinit/` | Recovery mode entry | That file's descriptor |

## What the socket descriptors mean in practice

The control socket is stamped for SYSTEM and Administrators (§10.1);
the notification socket inherits the `/run` seed, which grants the same
two. A connection from any other principal is refused at `connect()`,
by the filesystem, before peinit ever obtains a peer token — which
means the `ACCESS_DENIED` path and the audit event are unreachable for
such a caller on those two sockets.

The jobs socket is deliberately wider: `FILE_WRITE_DATA` for
Authenticated Users, full control for SYSTEM and Administrators
(§10.7). Connecting is the submission permission, and peinit adds no
check of its own behind it. What bounds the population that can reach
it is that descriptor, and what bounds what any one submitter can do
is the quota and the rule that a job runs only as an identity the
kernel verified the submitter held. The `ACCESS_DENIED` path *is*
reachable here — it is how a submitter learns it may not touch another
submitter's job — and every such denial is a `job.access_denied` event.

Since every service currently receives a SYSTEM token (§4.3), the
narrower two sockets are not yet observed by anything non-SYSTEM:
every notifier and every client is SYSTEM. The two have to move
together, because a service correctly resolved to a non-SYSTEM identity
could not reach the notification socket to report that it had started.
A submitted job running as a user is already in that position.

## The autorun directory

The Phase 1 autorun step (§2.3) executes every file in
`/lcl/policy/autorun.d` as SYSTEM, before path provisioning and before
any service. It is fail-open by design, so nothing about a script going
wrong stops the boot.

Its only protection is the descriptor on that directory. Anything that
can write there executes as SYSTEM at the earliest point in userspace
that exists.
