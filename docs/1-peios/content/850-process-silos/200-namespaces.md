---
title: Namespaces
type: concept
description: Namespaces are Peios kernel objects that isolate specific kinds of system view — process tree, network stack, filesystem mounts, and more. Each namespace is a first-class principal with its own SID, participates in AccessCheck, and forms the visibility substrate that Process Silos build on.
related:
  - peios/process-silos/understanding-process-silos
  - peios/identity/understanding-identity
  - peios/access-control/how-accesscheck-works
---

A **namespace** is a Peios kernel object that holds the state of an isolated view of part of the system. Multiple processes can be members of the same namespace and share the view it provides; a process in a different namespace of the same type sees an entirely separate state.

Each namespace is a first-class principal in the access control model: it has a SID, it appears in DACLs as a grantable identity, and processes carry namespace memberships that participate in AccessCheck.

## The seven namespace types

Peios provides seven types of namespace. Each type isolates a specific kind of system state.

| Type | Isolates |
|---|---|
| **PID namespace** | The process tree. Members see processes in their own PID namespace and its descendants; processes in other PID namespaces are invisible. PIDs are scoped per-namespace, so the same PID number can refer to different processes in different namespaces. |
| **Network namespace** | The network stack. Each network namespace has its own interfaces, routing tables, firewall state, sockets, and protocol state. A process in one network namespace cannot see or affect another's network state. |
| **Mount namespace** | The filesystem mount table. Each mount namespace has its own view of which filesystems are mounted at which paths. Mounts performed in one namespace are invisible to others. |
| **IPC namespace** | Inter-process communication objects — message queues, semaphores, shared memory segments. Members see only IPC objects created within the same namespace. |
| **Hostname namespace** | The system's hostname and domain name. Members see the namespace's hostname; changes inside the namespace do not affect other namespaces. |
| **Cgroup namespace** | The view of cgroup hierarchy paths. The cgroup namespace's root is the cgroup the process was in at namespace creation, hiding ancestors from the inside view. |
| **Time namespace** | Per-namespace offsets to monotonic and boot clocks. Members see clocks adjusted by the namespace's offset. The wall clock is unaffected — time namespaces only retime monotonic-style clocks. |

Each type is independent. A process can be in a private PID namespace but share the host's network namespace, or vice versa. Namespace memberships are tracked per-type per-process.

## PID namespace specifics

PID namespaces have substantially more nuance than the other types because they reshape the kernel's view of process identity itself.

**Hierarchy.** PID namespaces form a tree. A new PID namespace is always created as a descendant of the creating process's current PID namespace. Processes in a descendant namespace are visible to processes in any ancestor namespace; the reverse is not true.

**PID translation.** A process has a distinct PID in each PID namespace it is visible in. A process inside its own PID namespace might be PID 1; viewed from its parent namespace, it has whatever PID was allocated there (e.g., 31200); viewed from the root namespace, another value entirely. The same kernel object carries multiple PID identifiers, one per ancestor namespace.

**The init process.** The first process placed in a PID namespace becomes its **init process** — its PID inside the namespace is 1. Init has two special responsibilities:

- It **receives orphans.** When any process inside the namespace exits while its descendants are still running, the descendants are reparented to init.
- The namespace is **bound to its life.** When init exits, the kernel terminates every other process in the namespace via SIGKILL and destroys the namespace.

Init cannot be replaced at runtime. The only way to "reset" a PID namespace is to destroy it (by exiting init) and create a new one.

**Signal direction.** A process in an ancestor PID namespace can signal a process in a descendant namespace, subject to the normal process-access checks (process SD, PIP). A process in a descendant namespace cannot signal a process in an ancestor namespace — the target is invisible from the descendant's view, so signal delivery has no path.

**Process listing.** Process-listing interfaces inside a PID namespace see only the namespace's own processes — init and its descendants. Processes in ancestor or sibling namespaces are not enumerable.

## Namespace SIDs

Every namespace has a SID, allocated when the namespace is created. The SID is the canonical Peios identifier for the namespace and is what appears in DACLs, audit records, and any tool that shows namespace identity.

The SID format places each namespace under the Peios kernel runtime authority `S-1-5-1515-*`, with the first sub-authority identifying the namespace type:

| SID prefix | Namespace type |
|---|---|
| `S-1-5-1515-2-*` | PID namespaces |
| `S-1-5-1515-3-*` | Network namespaces |
| `S-1-5-1515-4-*` | Mount namespaces |
| `S-1-5-1515-5-*` | IPC namespaces |
| `S-1-5-1515-6-*` | Hostname namespaces |
| `S-1-5-1515-7-*` | Cgroup namespaces |
| `S-1-5-1515-8-*` | Time namespaces |

(The sub-authority `S-1-5-1515-1-*` is reserved for [silo SIDs](understanding-process-silos), which share the same authority as namespaces because they are kernel runtime objects in the same family.)

The remainder of the SID is derived from the namespace's GUID, generated at allocation time. The 128-bit GUID is split into four 32-bit sub-authorities:

```
S-1-5-1515-{type}-{guid_dword_0}-{guid_dword_1}-{guid_dword_2}-{guid_dword_3}
```

The result is a globally unique SID stable across the namespace's lifetime.

**Stability across the namespace's lifetime:** the SID does not change once allocated. As long as the namespace exists (at least one member or a held handle keeps it alive), its SID is fixed.

**Stability across reboots:** namespace SIDs are not stable across reboots. Each boot generates new GUIDs for the host's initial namespaces; namespaces created at runtime get fresh GUIDs per boot. ACLs that reference specific namespace SIDs survive within a boot but not across reboots. For policy that should outlive reboots, refer to identity that does — user SIDs, group SIDs, capability SIDs, or silo SIDs allocated with deterministic identifiers.

## Process membership

Every process is a member of exactly one namespace of each type. The kernel tracks these memberships in the process's PSB-adjacent namespace state.

Membership in a namespace is the **only** way a process gains the namespace's view. Two processes in the same network namespace share its routing tables and sockets; two processes in different network namespaces have entirely separate network stacks.

When a process **forks**, the child inherits the parent's namespace memberships — the child becomes a member of every namespace the parent was a member of. When a process **execs**, namespace memberships persist (unlike PIP, namespaces are a property of the process, not the binary). When a process **exits**, its memberships are dropped; if it was the last member of a namespace and no handles are held to it, the namespace is destroyed.

## Namespace memberships in AccessCheck

A process's namespace SIDs participate in AccessCheck as positive grants. When the kernel evaluates a DACL on behalf of a process, it includes all the process's namespace SIDs in the SID set used for matching:

- The process's PID namespace SID
- Network namespace SID
- Mount namespace SID
- IPC, hostname, cgroup, time namespace SIDs

A DACL ACE granting access to any of these matches the process. This is in addition to the user SID, group SIDs, and silo SID (if any).

This is purely additive — namespace SIDs grant access via the normal DACL walk. They do not interact with the silo or confinement intersection passes; those use silo and confinement-specific SID sets exclusively.

The effect is that an administrator can grant access to "any process in this network namespace" or "any process in this mount namespace" with a single ACE, without having to enumerate the processes that happen to be members at the time. As processes enter and leave namespaces, their access to such ACEs follows automatically.

## Namespace lifetime

Namespaces are reference-counted. A namespace exists as long as at least one of:

- A process is a member of the namespace
- A handle is held to the namespace (file descriptors that reference namespaces, retained for tooling that wants to enter or query a namespace later)

When the last reference is released, the namespace is destroyed and its SID becomes invalid. A subsequent namespace of the same type would receive a new SID — namespace SIDs are not reused.

Initial namespaces (the boot-time host namespaces) are always referenced by at least one host process during normal operation, so they persist for the boot's lifetime.

## Initial namespaces

At boot, the kernel creates one namespace of each type — the **initial namespaces** (commonly called the host namespaces). All processes start as members of these unless explicitly placed elsewhere.

Initial namespaces are allocated like any other: the kernel generates GUIDs and projects them as SIDs. The host's initial namespaces have SIDs that are fixed for the boot but vary across boots. Tools that need to refer to "the host" should use the running boot's initial namespace SIDs (queryable via `idn`), not assume any well-known value.

## Namespace operations

The privileged operations on namespaces are:

- **Create** — allocate a new namespace of a chosen type. The calling process becomes a member of the new namespace. Gated by `SeCreateSiloPrivilege`.
- **Enter** — make the calling process a member of an existing namespace, replacing its current membership of that type. Gated by `SeCreateSiloPrivilege`.
- **Query** — inspect a namespace's metadata (SID, type, member processes, creation time). Available to processes that can see the namespace via membership or held handle.

Within a silo, processes may enter further nested namespaces (creating sub-namespaces still inside the silo's visibility envelope). They cannot enter namespaces outside the silo — that operation is denied as a silo escape.

## Nesting limits

Namespace creation is gated by `SeCreateSiloPrivilege`. There is no implicit cap on nesting depth — a privilege-holder may create namespaces inside namespaces inside namespaces.

The registry knob `\System\Namespaces\MaxDepth` (per type) imposes an explicit nesting-depth limit, primarily to bound resource consumption from runaway scripts. Default values are conservative — typical workloads never reach them. The privilege gate is the primary constraint; the depth limit is a secondary safety net.

## Audit

Namespace creation, entry, and destruction are audited. Each event records the namespace SID, type, and the actor's token. The audit knob is `\System\Audit\Namespaces` with the standard quartet (enabled / success-only / failure-only / disabled).

The default is `failure-only`. Namespace creations during normal operation are high-volume and uninteresting; failures (denied creations, attempted entries to forbidden namespaces, escape attempts from silos) are the security-relevant events.
