---
title: The Attack Surface
description: What the socket descriptors mean in practice, and what the autorun directory exposes.
---

| Surface | Reachable by | Controls | Protected by |
|---|---|---|---|
| Control socket | Anything that can connect | Service lifecycle, shutdown | The socket inode's descriptor, then the peer token and AccessCheck against the target's descriptor |
| Notification socket | Anything that can connect | Service readiness, watchdog, stored descriptors | The socket inode's descriptor, then PID matching verified through a pidfd, plus the start generation |
| Registry keys | Anything with registry access | Definitions, triggers, configuration | Registry key descriptors, enforced by LCS |
| `Machine\System\Init\EnvVars\` | Anything with registry access | The environment of every service | That key's descriptor, and nothing else — variable names are not filtered |
| Service cgroups | peinit | Process tracking and clean kill | Ownership of the hierarchy |
| Phase 1 mounts | peinit | Virtual filesystem availability | Hardcoded, no external input |
| `/lcl/policy/autorun.d` | Whatever can write it | Arbitrary code as SYSTEM in early boot | The directory's descriptor |
| Boot attempt counter | Whatever can write `/.peinit/` | Recovery mode entry | That file's descriptor |
| JFS device | Whatever holds the submission privilege | Ad-hoc job submission | A KACS privilege check, kernel-enforced |

## What the socket descriptors mean in practice

Both sockets inherit the single-entry descriptor peinit stamps on `/run`
in Phase 1 (§2.3), which grants `GENERIC_ALL` to SYSTEM and names no
other principal.

So both are reachable by SYSTEM alone. A connection from a
non-SYSTEM principal is refused at `connect()`, by the filesystem, before
peinit ever obtains a peer token — which means the `ACCESS_DENIED` path,
the audit event, and the Administrators entries in both default
descriptors (§4.6, §4.7) are unreachable for such a caller.

Since every service currently receives a SYSTEM token (§4.3), nothing
observes this today: every notifier and every client is SYSTEM. The two
have to move together, because a service correctly resolved to a
non-SYSTEM identity could not reach the notification socket to report
that it had started.

## The autorun directory

The Phase 1 autorun step (§2.3) executes every file in
`/lcl/policy/autorun.d` as SYSTEM, before path provisioning and before
any service. It is fail-open by design, so nothing about a script going
wrong stops the boot.

Its only protection is the descriptor on that directory. Anything that
can write there executes as SYSTEM at the earliest point in userspace
that exists.
