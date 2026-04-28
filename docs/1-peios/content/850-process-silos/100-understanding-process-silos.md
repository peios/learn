---
title: Understanding Process Silos
type: concept
description: Process Silos are process-bound confinement combined with namespace isolation — the kernel primitive Peios uses to give a process group a unified identity, a declared capability set, and an isolated view of the system.
related:
  - peios/confinement/understanding-confinement
  - peios/process-silos/namespaces
  - peios/access-control/how-accesscheck-works
---

A **Process Silo** is process-bound confinement combined with namespace isolation. Where Confinement is token-level and travels with impersonation, Silos are process-level and stay attached to the process group. Where Confinement restricts access by intersecting it with capability grants, Silos do exactly the same — but for the process, not the thread.

## Why silos exist

Workload isolation is a recurring need on a server. A multi-tenant host runs services that should not see each other's processes, network state, or filesystems. A defence-in-depth deployment confines a workload's view of the system to limit blast radius if it is compromised. A migration strategy runs a workload with its own filesystem layout, network identity, and process tree without affecting the host.

Process Silos provide the kernel-tracked **identity layer** for these scenarios. A silo gives a process group:

- A shared identity (the **silo SID**) that participates in access control
- A shared **capability declaration** (what the silo is permitted to do)
- A shared set of **namespaces** (isolated views of system state)

The other layers of typical workload isolation — resource limits, syscall filtering, filesystem layout — are independent primitives. Userspace orchestrators compose silos with these to build "containers" or other workload-isolation patterns. The kernel only commits to silos and namespaces.

## What a silo is

A silo is **two PSB fields plus the namespaces of the processes inside it**:

| Element | Purpose |
|---|---|
| **Silo SID** | A unique SID identifying this silo. When present on a process's PSB, the silo intersection is active for AccessCheck involving that process. |
| **Capability SIDs** | A set of declared capabilities — what processes inside this silo are permitted to do. Drawn from the same vocabulary used by Confinement. |

Silos are **process-bound**, never travelling with impersonation. A service thread impersonating a client adopts the client's token (and any confinement on it) but does not adopt the client's silo. The thread remains in its process's silo — visibility and process-group membership are facts about the process, not about the identity it is currently acting as.

Namespaces themselves are not "fields on the silo." They are independent kernel objects that the silo's processes are members of (see [Namespaces](namespaces) for the full model). A silo is created with a chosen set of namespace types; the kernel allocates new namespaces for those types and the silo's processes become members. The silo is the identity that holds the group together; namespaces are the visibility implementation.

## How silos affect access

AccessCheck gains a **silo pass** that runs alongside the existing confinement pass. The pass evaluates the same DACL but matches only against:

- The process's silo SID
- The process's silo capability SIDs
- The well-known `ALL_APPLICATION_PACKAGES` SID (unless the silo is strict)

The result is intersected with the rest of the AccessCheck output. Like confinement, this is a final mask: rights survive only if both the normal evaluation and the silo evaluation independently grant them.

This is the same shape as confinement's intersection. The difference is purely where the SIDs come from — confinement reads them from the effective token, silos read them from the PSB.

A process can be both confined (token level) and siloed (process level) simultaneously. AccessCheck then runs a normal pass, a confinement pass, and a silo pass — three intersections. A process must satisfy all of them to gain a right.

## What silos block

Silos inherit the same absolute-boundary properties as confinement:

- **Privileges do not bypass silos.** A process inside a silo holding `SeBackupPrivilege` does not gain backup access through the silo intersection.
- **Owner implicit rights are skipped** in the silo pass.
- **SACL access is unreachable** to siloed processes (privilege bypass would be required, which silos forbid).

The user identity inside the process — even SYSTEM — is irrelevant to the silo boundary. A SYSTEM process inside a silo is bound by the silo just as a regular user is.

> [!WARNING]
> The process's user identity — which might be SYSTEM, an administrator, or any other powerful principal — is irrelevant inside the silo boundary. No privilege bypasses silos.

## How objects opt in

For a process inside a silo to access an object, the object's DACL must contain an ACE granting access to one of:

- The silo's **silo SID** — grants access to this specific silo
- One of the silo's **capability SIDs** — grants access to any silo (or confined process) with this capability
- The well-known **`ALL_APPLICATION_PACKAGES`** SID — grants access to all non-strict siloed and confined processes

The capability vocabulary is shared with Confinement. A capability ACE for `internetClient` grants the same thing whether the matching process is confined, siloed, or both. Peios accumulates one rich vocabulary of capability ACEs across the system that Confinement, Silos, and Positive Confinement can all reuse.

## Silo creation

A silo is created by a privileged caller via `kacs_create_silo(silo_sid, capabilities, namespace_types)`:

- `silo_sid` — the SID identifying the silo. Allocated by the caller (typically a service orchestrator) under `S-1-5-1515-1-*`.
- `capabilities` — the set of capability SIDs the silo declares. Default profiles include `ALL_APPLICATION_PACKAGES`; strict profiles omit it.
- `namespace_types` — which kinds of namespace the silo isolates. Each requested type causes the kernel to allocate a new namespace of that kind and place the calling process into it.

The privilege required is `SeCreateSiloPrivilege`. Default-grant policy is restrictive — only TCB components, service orchestrators, and explicitly-permitted runtime daemons hold it.

After creation, the calling process and its descendants are in the silo. Fork copies the silo identity to the child; exec preserves it. Threads share the silo with the rest of the process. Once set, the silo identity on a PSB cannot be cleared at runtime — leaving a silo is by exit, not by clearing.

## What silos are not

- **Silos are not resource boundaries.** A process in a silo can still consume host CPU and memory if no resource limits are applied. Resource control is a separate primitive.
- **Silos are not syscall filters.** Restricting which syscalls a process may issue is a separate primitive.
- **Silos are not filesystem layouts.** A silo with a mount namespace has an independent filesystem view, but constructing a particular tree (a "rootfs") inside that view is the orchestrator's job, not the silo's.

What people typically call a "container" is a userspace composition of: a silo, resource limits, syscall filtering, and a constrained filesystem view. The kernel commits to silos and namespaces. The rest is composition.

## Strict silos

Like confinement, silos can be created with `ALL_APPLICATION_PACKAGES` omitted from their capabilities. A **strict silo** matches only `ALL_RESTRICTED_APPLICATION_PACKAGES` and the silo's own specific capability SIDs, drastically narrowing the access surface against system objects that broadly opt in.

Strict silos are not a separate kernel mechanism. They are a policy choice at silo creation — which well-known SIDs are present in the capability set.

## When to use silos

Silos are appropriate for:

- **Workload isolation** — running an application or service inside a clearly-bounded process group with its own namespaces and identity
- **Multi-tenant separation** — running multiple workloads on the same host without giving them visibility into each other
- **Defence in depth** — adding a process-level boundary on top of identity-based access control

If a process just needs reduced access without process-group separation, [Confinement](../confinement/understanding-confinement) is the right tool. Silos are for the case where you also want a kernel-tracked identity for the whole process group, and namespace-level visibility isolation.
