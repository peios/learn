---
title: Understanding the Thread Model
type: concept
description: How threads share and isolate state on Peios — the security model implications of shared primary tokens, per-thread impersonation, and process-scoped security descriptors.
related:
  - peios/process-management/understanding-process-creation
  - peios/identity/primary-vs-impersonation-tokens
  - peios/linux-compatibility/credential-projection
---

A **thread** on Peios is a kernel task that shares its address space, file descriptors, and primary token with other threads in the same process. Threads are created by `clone()` with the `CLONE_THREAD` flag — the same primitive that creates processes, branched on a single bit.

The kernel's threading is one-to-one: each user-visible thread is a distinct kernel task with its own scheduling, signal mask, register state, and stack. Userspace threading libraries — NPTL and the rest — are thin wrappers around kernel tasks, not green-thread implementations layered on top.

The interesting question, from a security point of view, is what threads share with their siblings and what they hold independently.

## What threads share

All threads in a process share:

- **The primary token.** Identity, group memberships, privileges, integrity level — every thread sees the same token object. Adjusting privileges on the primary token is immediately visible to every sibling thread.
- **The address space.** A pointer is meaningful in any thread.
- **The file descriptor table** (subject to `CLONE_FILES` at clone time).
- **The process security descriptor.** Operations against the process — sending signals, reading memory, attaching a debugger — are gated by a single SD attached to the process. There is no per-thread SD. Permission to interact with one thread is permission to interact with all of them.
- **The process security block.** Integrity protection, mitigation flags, `no_child_process`, the process GUID. These are properties of the process as a unit, and threads cannot diverge.
- **The current working directory, root directory, and umask** (subject to `CLONE_FS`).

## What each thread holds independently

Each thread has its own:

- **Impersonation state.** Impersonation is fundamentally a per-thread concept. A service can have ten worker threads, each impersonating a different client at the same time, while the service's primary token remains undisturbed. When a thread reverts, only its own state changes.
- **Effective credential.** The thread's effective credential is the impersonation token if one is active, otherwise the primary token. This is what filesystem credential reads consult.
- **Signal mask.** Signals can be blocked on a per-thread basis. Process-directed signals are delivered to any unblocking thread; thread-directed signals are routed specifically.
- **CPU affinity.** Each thread can be pinned to its own subset of CPUs. The privileges required to pin to certain CPUs are covered alongside the rest of the scheduling model.
- **Thread-local storage.** Each thread has its own TLS region; threads do not see each other's TLS through pointer arithmetic on the same offset.
- **Stack.** Each thread has its own kernel and user stack.
- **Thread ID** (`gettid()`, `/proc/<pid>/task/<tid>`).

There is no "thread security descriptor" and no "thread identity" beyond impersonation state. Threads are not security principals. The principal is the process, identified by its primary token; threads are units of execution within that principal that can temporarily act on someone else's behalf via impersonation.

Threading libraries also use `set_tid_address()` to register a memory location the kernel will clear and futex-wake when the thread exits, paired with `CLONE_CHILD_CLEARTID` at clone time. This is the substrate mechanism behind robust pthread join — the joining thread can wait on the futex to know precisely when the child has fully unwound. Like other thread-setup state, the TID-clear address is per-thread and behaves identically to Linux on Peios.

## Thread identification

Three numbers identify a thread:

| Number | Meaning |
|---|---|
| `pid` | The kernel task ID. `gettid()` returns this. Globally unique within a PID namespace. |
| `tgid` | The thread group ID — the `pid` of the first thread in the process. `getpid()` returns this. All threads in a process share the same `tgid`. |
| `process_guid` | The kernel-generated UUID identifying the process. All threads share it. There is no per-thread GUID — audit and supervision treat the process as the unit. |

The `pid` / `tgid` distinction is a Linux substrate property. Peios neither hides nor extends it. Tools that already understand Linux thread identification work unchanged.

## Filesystem credentials

Linux threads can hold per-thread filesystem credentials (`fsuid`, `fsgid`) — historically used by NFS servers to per-thread-impersonate clients. On Peios, this is automatic and unconditional: filesystem credentials always reflect the effective token, which is the impersonation token if active and the primary token otherwise. The values change with `kacs_impersonate_*`, not with `setfsuid` / `setfsgid`, and they cannot be made to lie. See [Credential projection](../linux-compatibility/credential-projection) for the full rule.

## Special threads

Some threads have no userspace context and exist only inside the kernel:

| Thread class | Role |
|---|---|
| `kthreadd` (PID 2) | The parent of all kernel threads. Created during boot. |
| `kworker/*` | Workqueue workers. Run deferred kernel work — driver bottom halves, filesystem maintenance, RCU callbacks. |
| `irq/N-name` | Threaded interrupt handlers. Created when a driver requests a threaded IRQ. |
| Per-CPU swappers (PID 0 instances) | The idle task. One per CPU. |

All of these run under the SYSTEM token. They are not user-controllable and do not interact with the rest of the security model except as the kernel itself does.

## How threading affects access decisions

Every access decision evaluated by the kernel uses the calling thread's effective token, which is the thread's impersonation token if one is active and otherwise its process's primary token. This is the entire intersection between threading and access control: which token gets evaluated depends on which thread is calling, but the token, the SD, and the AccessCheck logic are otherwise identical.

This is why the security model scales naturally to multi-threaded servers. A request handler thread can impersonate the request's client, perform a stack of file and IPC operations as that client, and revert — all without affecting any sibling thread, and without the kernel needing any threading-specific access logic.
