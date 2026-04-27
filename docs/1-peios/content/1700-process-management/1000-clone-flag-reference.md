---
title: CLONE Flag Reference
type: reference
description: Full enumeration of CLONE_* flags supported by Peios, what each controls, and any Peios-specific behaviour notes.
related:
  - peios/process-management/understanding-process-creation
  - peios/process-management/understanding-the-thread-model
  - peios/process-management/process-lifecycle
---

The kernel's `clone()` and `clone3()` accept a flag set that controls what is shared between parent and child, which namespaces the child enters, and a handful of bookkeeping behaviours used by threading libraries and process supervisors. This page enumerates every flag with its purpose and any Peios-specific note. For the conceptual model of what process creation looks like, see [Understanding Process Creation](understanding-process-creation).

## Resource sharing

Flags in this group control which kernel-state objects are shared between parent and child. They are the most frequently used flags and underpin the distinction between processes and threads.

| Flag | Purpose | Peios note |
|---|---|---|
| `CLONE_VM` | Share virtual address space. A pointer is meaningful in both the parent and the child. | Substrate-as-is. Required for `CLONE_THREAD`. |
| `CLONE_FS` | Share filesystem state — current working directory, root directory, umask. | Substrate-as-is. |
| `CLONE_FILES` | Share the file descriptor table. Closing an fd in either side is visible to the other. | Substrate-as-is. |
| `CLONE_SIGHAND` | Share signal handlers. Required when `CLONE_VM` is set. | Substrate-as-is. |
| `CLONE_THREAD` | The child joins the parent's thread group. Without this, the call creates a new process. | Branch point: shared primary token, independent impersonation per thread. See [Understanding the Thread Model](understanding-the-thread-model). |
| `CLONE_IO` | Share the I/O context. Affects how the I/O scheduler tracks competing requests. | Substrate-as-is. |
| `CLONE_SYSVSEM` | Share the System V semaphore undo list. | Substrate-as-is. |

## Namespace creation

Flags in this group create new namespaces, isolating the child from the parent in specific resource domains. They are the primitive on which container-style isolation is built. The full namespace model and its interaction with KACS confinement is documented in the **Containerisation** category; the entries here record their existence and the deferral.

| Flag | Purpose | Peios note |
|---|---|---|
| `CLONE_NEWNS` | New mount namespace — child has its own mount tree. | See Containerisation. |
| `CLONE_NEWPID` | New PID namespace — child becomes PID 1 in a fresh PID space. | See [PID Management](pid-management) for substrate behaviour; full model in Containerisation. |
| `CLONE_NEWNET` | New network namespace — child has its own network stack. | See Containerisation. |
| `CLONE_NEWUTS` | New UTS namespace — child has its own hostname/domainname. | See Containerisation. |
| `CLONE_NEWIPC` | New IPC namespace — child has its own System V / POSIX IPC space. | See Containerisation. |
| `CLONE_NEWUSER` | New user namespace — child has its own UID/GID mapping. | See Containerisation. UIDs have no security meaning on Peios; user namespaces are primarily a building block for the other namespace types. |
| `CLONE_NEWCGROUP` | New cgroup namespace — child has its own view of the cgroup hierarchy. | See Containerisation. |
| `CLONE_NEWTIME` | New time namespace — child has its own boottime/monotonic clock offsets. | See Containerisation. |

## Process and thread tracking

Flags in this group create handles or write back identifiers used by threading libraries and modern process-supervision code.

| Flag | Purpose | Peios note |
|---|---|---|
| `CLONE_PIDFD` | Return a pidfd for the child to the parent. | See [Process Lifecycle](process-lifecycle). The pidfd is issued without a separate AccessCheck — the parent always has authority over its newly-created child. |
| `CLONE_PARENT_SETTID` | Write the child's TID into the parent's address space at a given pointer. | Substrate-as-is. Used by threading libraries to record the new thread's TID synchronously with creation. |
| `CLONE_CHILD_SETTID` | Write the child's TID into the child's address space at a given pointer. | Substrate-as-is. |
| `CLONE_CHILD_CLEARTID` | Clear the TID at a given child pointer when the child exits, and wake any futex waiters there. | Substrate-as-is. The mechanism behind robust pthread thread-exit notification. |
| `CLONE_SETTLS` | Set the child's TLS register (`fs` on x86-64) to a given value. | Substrate-as-is. Used by threading libraries during thread setup. |

## Process structure

Flags in this group affect the parent-child relationship or the cgroup placement of the new process.

| Flag | Purpose | Peios note |
|---|---|---|
| `CLONE_PARENT` | The new process's parent becomes the calling process's parent (a sibling, not a child). `SIGCHLD` goes to the grandparent, not to the caller. | Substrate-as-is. The child's process SD governs all interactions regardless of who its parent is — choice of parent does not affect what is allowed. |
| `CLONE_INTO_CGROUP` (clone3 only) | Place the new process directly into a specified cgroup at creation, instead of inheriting the parent's. | See Resource Control for the cgroup model. The privilege required to choose the destination cgroup is part of the cgroup-membership story. |
| `CLONE_VFORK` | The parent is suspended until the child either exits or calls `execve()`. The traditional `vfork()` semantics. | Substrate-as-is. |

## Tracing — `CLONE_UNTRACED`

`CLONE_UNTRACED` is the only flag in this reference that warrants its own subsection because it is widely misread as an equivalent of PIP — "the child cannot be traced." It is not, and the distinction matters.

**What it actually does.** When a process under `ptrace` calls `clone()`, the kernel by default forks the trace relationship — the same tracer is auto-attached to the new child via `CLONE_PTRACE`, so the debugger continues to follow the child. `CLONE_UNTRACED` is the parent's opt-out from that auto-attachment. The child is born without a tracer attached, even though the parent has one.

**What it does not do.** It does not prevent any subsequent `PTRACE_ATTACH` from succeeding. A debugger that gets a handle to the child can still try to attach later. Whether the attach is allowed depends on the usual gates: PIP dominance against the child, the child's process SD (`PROCESS_VM_WRITE` etc.), and `SeDebugPrivilege` for the process-SD bypass.

`CLONE_UNTRACED` is an **inheritance flag**, not a protection mechanism. It controls the propagation of an existing tracer's authority across `clone()`. Actual protection of a process from being traced is the job of PIP and the process SD.

Substrate-as-is on Peios. KACS does not modify how `CLONE_UNTRACED` works; it modifies the gates that `PTRACE_ATTACH` itself goes through.

## Historical and ignored

| Flag | Purpose | Peios note |
|---|---|---|
| `CLONE_DETACHED` | Historical. Originally controlled whether the parent received `SIGCHLD`. Ignored by modern kernels. | Substrate-as-is — present in headers, no effect. |

## Default behaviour without flags

A `clone()` call with no flags creates a child process that copies (rather than shares) everything from the parent. This is equivalent to `fork()`. Specifically:

- Address space is copy-on-write
- File descriptors are duplicated
- Signal handlers are copied
- The child is a new thread group of its own (a new process)
- The child is in the parent's namespaces

Setting any sharing flag (`CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, `CLONE_SIGHAND`) causes the corresponding state to be shared rather than copied.

## See also

- [Understanding Process Creation](understanding-process-creation) for the conceptual model.
- [Understanding the Thread Model](understanding-the-thread-model) for what `CLONE_THREAD` produces and how threads share or diverge.
- [Process Lifecycle](process-lifecycle) for pidfds, waiting, and reparenting.
