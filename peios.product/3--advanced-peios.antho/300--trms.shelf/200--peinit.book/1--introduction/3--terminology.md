---
title: Terminology
description: The terms this manual uses without redefining them, and where each is introduced.
---

Terms defined where they are introduced — activation generation, boot
generation, transition cause, cgroup generation, start generation — are
not repeated here.

**Service.** A named, supervised unit of execution: a definition in the
registry, a runtime state, a Security Descriptor, and at most one
running main process. Services are the primary unit of management and
the thing dependencies are expressed between.

**Job.** One supervised process execution. Every fork peinit performs
is a job — a service's main binary, a pre-exec hook, a health check
invocation, an ad-hoc submission — with a GUID, a lifecycle, a token
summary and a log correlation key. Jobs are the observable unit of what
actually ran.

**Operation.** A first-class object representing a requested state
machine action on a service. Control commands do not mutate state
directly; they create operations that are validated, queued, resolved
against whatever else is in flight, and executed by the event loop.

**Trigger.** A rule in a service definition saying when the service
starts automatically: at boot, once the boot set has settled, or on a
schedule. A service with no triggers starts only when something asks
for it.

**Phase 1.** The compiled-in bootstrap: root writability, the remaining
virtual filesystems, the persisted random seed, the local machine ID,
the clock, registryd, boot-time path provisioning, and infrastructure
setup. No registry access happens before registryd is serving.

**Phase 2.** The registry-driven boot: read the service definitions,
build and validate the dependency graph, and start the boot-triggered
services in dependency order.

**ErrorControl.** The per-service policy for an irrecoverable failure.
Normal leaves the service Failed; Critical syncs the filesystems and
reboots.

**Token.** The per-thread KACS identity object — a user SID, group SIDs,
a privilege bitmask, an integrity level, and metadata. Tokens are the
sole identity mechanism: peinit sets no UIDs, GIDs, or Linux
capabilities on service processes. Peios Kernel TRM §3.2.

**Security Descriptor** (SD). The KACS structure controlling access to
a securable object. peinit uses two: a **ServiceSecurity** descriptor
per service, controlling who may manage it, and its own **control**
descriptor, controlling system-level operations. Peios Kernel TRM §3
and PCDS §5.

**AccessCheck.** The KACS function that evaluates a token against a
descriptor to produce a decision. peinit calls it for every control
request. Peios Kernel TRM §3.8.

**Per-service SID.** A SID under authority `S-1-5-80` derived
deterministically from the service name, carried in the group list of
every service token. Two services running as the same principal are
still distinguishable to an access check. §4.4.

**registryd.** The userspace registry source daemon serving the
persistent hives. peinit starts it in Phase 1 from a compiled-in
definition and treats it as opaque thereafter. Its implementation is
loregd, a distinction visible only in recovery mode.

**Registry.** The configuration system LCS and its sources provide
together. peinit reads service definitions from
`Machine\System\Services\`, boot configuration from
`Machine\System\Boot\`, and its own parameters from
`Machine\System\Init\`.

**KMES.** The kernel-mediated event subsystem. peinit emits its
structured events — job and operation lifecycle, audit records — into
its ring buffer, where they survive eventd restarts and reboots. Peios
Kernel TRM §2.

**JFS.** The Job Forwarding Subsystem: the kernel bridge that captures a
caller's effective token and delivers it, with a job definition, to
whatever holds `/dev/jfs` open. peinit is the consumer. §8.5.

**pidfd.** A descriptor referring to one specific process, obtained
atomically at fork through `clone3(CLONE_PIDFD)`. Every process peinit
supervises is tracked by one, which is what makes supervision immune to
PID reuse.

**cgroup.** peinit uses cgroups v2 for process tracking and clean kill
only — not for resource accounting or limits. Every service gets its own
tree under `/sys/fs/cgroup/peinit/`. §5.1.

**sd_notify.** The datagram protocol services use to report readiness,
status, keepalives and stored descriptors, over the socket named by
`NOTIFY_SOCKET`. Specified in PSPU §4.

**TCB.** The Trusted Computing Base: the kernel, KACS, LCS, KMES,
peinit, registryd, authd, lpsd and eventd. A compromise of any of them
compromises the system.
