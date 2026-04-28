---
title: Linux Compatibility
type: concept
description: How Process Silos and Namespaces appear to unmodified Linux applications — the legacy syscall surface, the inode-based namespace identity Linux apps see, and the rejection of Linux user namespaces.
related:
  - peios/process-silos/understanding-process-silos
  - peios/process-silos/namespaces
  - peios/linux-compatibility/credential-projection
---

Peios is built on a Linux kernel base. Linux applications that have not been ported to Peios-native APIs make Linux-shaped syscalls — `unshare()`, `setns()`, `clone()` with `CLONE_NEW*` flags, `/proc/<pid>/ns/<type>` reads. Peios honours these so unmodified Linux container runtimes and namespace-touching Linux apps run, while keeping KACS authoritative for access control.

This page documents the legacy compatibility surface for Process Silos and Namespaces. Native Peios applications should use the Peios APIs documented elsewhere; the Linux surface exists for unmodified Linux software.

## The Linux syscall surface

### Namespace creation: unshare and clone

`unshare(flags)` unshares the calling process from one or more namespaces, allocating new ones. `clone(flags)` does the same for a newly-created child. Each `CLONE_NEW*` flag corresponds to a Peios namespace type:

| Linux flag | Peios namespace type |
|---|---|
| `CLONE_NEWPID` | PID namespace |
| `CLONE_NEWNET` | Network namespace |
| `CLONE_NEWNS` | Mount namespace |
| `CLONE_NEWIPC` | IPC namespace |
| `CLONE_NEWUTS` | Hostname namespace |
| `CLONE_NEWCGROUP` | Cgroup namespace |
| `CLONE_NEWTIME` | Time namespace |
| `CLONE_NEWUSER` | **REJECTED** — returns `EPERM` |

A successful call allocates new namespace objects, generates GUIDs, projects them as SIDs (under `S-1-5-1515-{type}-*`), and updates the calling process's namespace memberships.

The privilege required is `SeCreateSiloPrivilege`. Linux processes that expect `unshare` to succeed because they hold `CAP_SYS_ADMIN` cosmetically will find the call rejected unless the underlying Peios privilege is also held. The Peios privilege is authoritative; the Linux capability is a cosmetic translation.

### Namespace entry: setns

`setns(fd, type)` moves the calling process into the namespace identified by the fd. Same privilege requirement as creation.

Two restrictions beyond Linux semantics:

- `setns` to a user namespace fd fails (user namespaces do not exist on Peios)
- `setns` to a namespace **outside the current silo** fails — silo escape via `setns` is denied. A process in a silo can only enter namespaces inside the silo or its descendants.

### What the Linux capability gates look like

`CAP_SYS_ADMIN` historically gates a wide range of operations including namespace creation. Under Peios's [credential projection](../linux-compatibility/credential-projection) model, Linux capabilities translate to KACS privileges:

| Linux capability | Peios privilege |
|---|---|
| `CAP_SYS_ADMIN` (general) | `SeTcbPrivilege` |
| `CAP_SYS_ADMIN` (namespace ops) | `SeCreateSiloPrivilege` |
| `CAP_SYS_NICE` | `SeIncreaseBasePriorityPrivilege` |
| `CAP_NET_ADMIN` | `SeTcbPrivilege` |

A process that holds `CAP_SYS_ADMIN` cosmetically but does not hold `SeCreateSiloPrivilege` cannot create namespaces. The Peios privilege is what the kernel actually checks.

## The Linux-side namespace identifier

Each namespace exposes a Linux-style identifier through the `/proc/<pid>/ns/<type>` symlink. The symlink target has the form `<type>:[<inode>]`, where the inode number is allocated by the kernel at namespace creation.

This is the **cosmetic Linux identifier**. It exists for compatibility with Linux tools and APIs that compare namespace identity by inode (`nsenter` opens the symlink as an fd and uses `setns`; some monitoring tools compare inode numbers across processes to determine if they share a namespace).

The **canonical Peios identifier** for a namespace is its SID. KACS-aware tooling, audit records, DACLs, and access control all use the SID. The inode is a parallel identity carried for Linux compatibility.

Both identifiers refer to the same underlying kernel object. A namespace's inode and SID are both stable for the namespace's lifetime — neither changes between creation and destruction.

### Mapping between identifiers

Tooling can map between SIDs and Linux inode-style identifiers:

```bash
$ idn ns inode-to-sid network 4026531840
S-1-5-1515-3-849273-23847-12384-99381

$ idn ns sid-to-inode S-1-5-1515-3-849273-23847-12384-99381
network:[4026531840]
```

Audit records always use the SID. Tools that consume audit data and need to correlate with Linux-side state use these mappings.

## User namespaces

`CLONE_NEWUSER` is rejected unconditionally. `unshare(CLONE_NEWUSER)` returns `EPERM`, audit-loud. `setns()` to a user namespace fd fails. There is no Peios analogue.

User namespaces under Linux serve four purposes:

| Purpose | Status on Peios |
|---|---|
| Rootless containers | Not supported on v1 — see below |
| Unprivileged namespace creation | Impossible by design — namespace creation is privilege-gated, not capability-gated |
| UID isolation between containers | Provided by silo SIDs; UID maps are unnecessary |
| subuid/subgid delegation | Meaningless under KACS — UIDs project from SIDs, not delegated through subuid files |

**Rootless containers** depend on `CLONE_NEWUSER` to bootstrap: an unprivileged user creates a user namespace, becomes "root inside it," then bootstraps other namespaces. Without `CLONE_NEWUSER`, this path does not exist. Server workloads use **rooted container runtimes** (a privileged daemon creates containers and runs them as non-privileged inside) which work without user namespaces.

This may change in future versions if a Peios-native rootless model is designed. Such a model would not depend on Linux user namespaces — it would extend the silo and projection mechanisms to handle the unprivileged-launch case.

## Container runtime compatibility

Linux container runtimes that work without modification:

- **Docker rootful** — privileged daemon creates containers, runs them as non-root inside
- **Podman rootful** — same model
- **containerd**
- **runc**
- **CRI-O**

These runtimes call `unshare`/`clone` with `SeCreateSiloPrivilege` granted to the daemon, set up resource limits and syscall filters separately, pivot the root filesystem inside a mount namespace, and run the workload inside.

Linux container runtimes that **do not work**:

- **Rootless Docker** — depends on `CLONE_NEWUSER`
- **Rootless podman** — same
- **buildah --userns** — same
- Any runtime that requires `setns` to a namespace outside its current silo

## Inheritance of cosmetic namespace state

Linux apps that read `/proc/<pid>/ns/<type>` expect the inode to remain stable across the namespace's lifetime. Peios preserves this — the inode is allocated once at namespace creation and is stable until the namespace is destroyed. The SID and the inode are two views of the same kernel object.

Linux apps that compare inodes to detect "are these two processes in the same namespace?" continue to work as expected. The comparison is equivalent to comparing the namespace SIDs, just with different identifiers.

## Persisting a namespace beyond its last process

Linux convention pins a namespace past its last member process by bind-mounting `/proc/<pid>/ns/<type>` to a stable filesystem path. As long as the bind mount exists, the namespace is held alive — the bind mount counts as a held handle.

Peios honours this. A bind mount of a namespace symlink keeps the namespace alive; the namespace's SID remains valid as long as the bind mount exists. When the bind mount is unmounted and no other references remain, the namespace is destroyed.

Native Peios applications can hold namespace handles directly via fd reference without using the bind-mount mechanism.

## Namespace introspection: `ioctl_ns(2)`

`ioctl_ns(2)` operations on a namespace fd query relationships:

| Operation | Behaviour on Peios |
|---|---|
| `NS_GET_NSTYPE` | Returns the namespace type (one of the `CLONE_NEW*` constants). Works as on Linux. |
| `NS_GET_PARENT` | Returns an fd referring to the parent namespace, for types that nest (PID namespace). Works as on Linux. |
| `NS_GET_USERNS` | **Fails** with `EINVAL` — there is no owning user namespace because user namespaces do not exist on Peios. |
| `NS_GET_OWNER_UID` | **Fails** with `EINVAL` for the same reason. |

For SID-based introspection, native tooling (`idn ns`) returns the same information in Peios identifier form, plus the namespace's SID and capability metadata.

## `nsenter`

The `nsenter(1)` userspace tool uses `setns()` to enter a target's namespaces and execute a command. It works on Peios with the standard semantics, subject to:

- The `SeCreateSiloPrivilege` requirement on the calling token
- The silo escape gate — `nsenter` invocations that try to enter namespaces outside the caller's silo fail

## `/proc` inside a PID namespace

Linux convention is to remount `procfs` inside a PID namespace so the new mount reflects only the namespace's processes. Peios preserves this — a `procfs` mount made from inside a PID namespace shows only that namespace's processes.

A `procfs` mount made from outside (in an ancestor namespace) can show processes from outer namespaces too, subject to the standard process-access checks.

## `/proc/<pid>/cgroup` virtualisation

The cgroup namespace virtualises `/proc/<pid>/cgroup`. From inside the namespace, the file shows paths relative to the namespace's cgroup root — ancestors of the namespace root are hidden, making the inside view appear to start at `/`.

Peios preserves this Linux behaviour for compatibility with cgroup-aware Linux applications that introspect their own placement.

## `/proc/<pid>/timens_offsets`

The time namespace's monotonic and boot-clock offsets are configured by writing to `/proc/<pid>/timens_offsets` before the namespace is entered. The format is one line per clock:

```
monotonic <secs> <nsecs>
boottime  <secs> <nsecs>
```

Once any process becomes a member of the namespace, the offsets are sealed and cannot be changed. Native Peios applications can pass offsets directly when creating the namespace via the silo creation API; the `/proc` interface exists for unmodified Linux applications.

## Audit visibility

Audit records emitted by Peios use SIDs, not inodes. Linux audit consumers (e.g., bridge tooling that translates KACS audit events to `auditd` format) translate the SID-shaped events into inode-shaped events for downstream Linux tools that expect them. The translation goes through the `idn ns` mapping commands or equivalent kernel queries.

## What changes for Linux applications

The summary, for unmodified Linux applications:

- **Namespace creation requires a Peios privilege**, not just a Linux capability. Most service-management workflows already run with the necessary privilege; ad-hoc unprivileged calls fail.
- **User namespaces do not exist.** Apps that detect their absence should fall back to non-user-namespace paths or report unsupported.
- **Within a silo, escape via `setns` is denied.** Container runtimes that move themselves into and out of namespaces during setup must complete the moves before the silo entry, not after.
- **Linux capabilities are cosmetic.** The actual access decision uses the Peios privilege model. Apps that strip capabilities to "drop privileges" do so cosmetically; the underlying token's privileges are what matter.

Native Peios applications should use the Peios APIs (`kacs_create_silo`, KACS-aware namespace queries) directly. The Linux compatibility surface is a translation layer for software not yet ported to Peios.
