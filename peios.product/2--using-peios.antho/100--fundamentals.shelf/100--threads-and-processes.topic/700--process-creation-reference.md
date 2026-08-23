---
title: Process creation reference
type: reference
description: The precise contract for fork, vfork, clone and clone3, the clone sharing flags, the exec family, posix_spawn, and the pidfd calls.
related:
  - peios/threads-and-processes/creating-processes
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/security-fundamentals/tokens/lifecycle
---

This is the detailed counterpart to
[Creating processes](~peios/threads-and-processes/creating-processes). That page
explains the ideas; this one gives the exact contract — what each call does, what a
new process inherits, and what each `clone` sharing flag controls.

## fork

`fork()` creates a new process by duplicating the caller. The child is a
near-identical copy that runs independently from the point of the call.

The child **inherits**:

- a private copy of the parent's memory, made lazily (copy-on-write), so the
  duplication is cheap and changes on either side stay invisible to the other
- copies of the parent's open file descriptors — each refers to the same open file
  description, so file offset, status flags, and signal-driven-I/O settings are
  shared between parent and child
- open directory streams and open message-queue descriptors
- open-file-description locks (`flock`, OFD locks) through those shared descriptors
- the parent's signal dispositions (the handler set for each signal)
- the file-creation mask (umask), the current directory, and the root directory
- resource limits and the timer-slack value
- the parent's identity — it begins acting on the same token (see
  [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle))
- the parent's mitigations and protection, carried on its
  [PSB](~peios/threads-and-processes/the-process-security-block)

The child does **not** inherit:

- the parent's PID — it receives a new PID and a new Process GUID
- memory locks (`mlock`, `mlockall`)
- memory regions marked `MADV_DONTFORK` (absent in the child) or `MADV_WIPEONFORK`
  (present but zeroed)
- process resource usage and CPU-time counters — reset to zero
- pending signals — the child's set starts empty
- semaphore adjustments (semadj)
- process-associated record locks (POSIX `fcntl` locks — distinct from the OFD and
  `flock` locks above, which are shared through the inherited descriptors)
- timers (`setitimer`, `alarm`, `timer_create`)
- outstanding asynchronous I/O
- directory-change notifications (`dnotify`)
- the `PR_SET_PDEATHSIG` parent-death-signal setting (reset)
- I/O-port access permissions (`ioperm`)

The child's termination signal — what its parent is notified with when it ends —
is `SIGCHLD`.

The child is created with a **single thread** — the one that called `fork()`. If
the parent had other threads, they do not exist in the child.

## vfork

`vfork()` is a lightweight variant of `fork()` for the one case where the child
will immediately replace itself with another program. It differs in two ways:

- the caller is **suspended** from the call until the child either `exec`s or exits;
- the child runs in the **parent's memory** — no copy is made — until that point.

Because the two share memory and the parent is frozen, the child must do almost
nothing first. The contract: the child must not return from the function that
called `vfork()`, must not modify any variable other than the one holding the
return value, and must not call any other function before a successful `exec` or
`_exit`. Doing otherwise is undefined behaviour.

`vfork` is an optimisation for the create-then-replace pattern. Ordinary code
should use `posix_spawn` (below) rather than reach for it directly.

## clone and clone3

`clone()` is the general creation call. `fork` and thread creation are both
`clone` with particular flag sets; `clone` exposes the choice directly. The caller
gives a set of **flags** controlling what the new task shares with the creator, a
stack for the new task, and locations for thread-ID and thread-local-storage
bookkeeping.

`clone3()` is the modern form, taking a structure instead of positional arguments
so it can grow new fields over time without changing the call:

| Field | Purpose |
|---|---|
| `flags` | The sharing flags (below). |
| `pidfd` | Where to store a pidfd for the new child. |
| `child_tid` / `parent_tid` | Where to record the new thread's ID, in the child's and the parent's memory. |
| `exit_signal` | The signal delivered to the parent when the child ends. |
| `stack` / `stack_size` | The new task's stack and its size. |
| `tls` | The new task's thread-local-storage area. |
| `set_tid` / `set_tid_size` | Request specific thread IDs for the new task — a privileged operation (see below). |
| `cgroup` | Place the child directly into a resource group at creation (see resource management). |

The structure is **size-versioned**: the caller passes the size it knows, the
kernel reads up to the size it knows, and any unknown trailing fields must be
zero. This is how new fields are added without breaking existing programs.

Requesting a specific thread ID (`set_tid`) is a **privileged** operation — it
exists for checkpoint-and-restore tools that must recreate a process with its
original ID. The privilege required follows the
[capability model](~peios/linux-compatibility/dac-neutralization-and-capabilities).

## clone sharing flags

Each flag makes the new task **share** something with its creator instead of
getting its own copy. The flags that build threads and control creation:

| Flag | Effect |
|---|---|
| `CLONE_VM` | Share memory rather than taking a private copy. |
| `CLONE_FS` | Share filesystem context — current directory, root directory, file-creation mask. |
| `CLONE_FILES` | Share the open-descriptor table, so opening or closing a descriptor in one is seen by the other. |
| `CLONE_SIGHAND` | Share the table of signal handlers. Requires `CLONE_VM`. |
| `CLONE_THREAD` | Put the new task in the same process (thread group) as the creator. Requires `CLONE_SIGHAND`. |
| `CLONE_SETTLS` | Set the new task's thread-local-storage area. |
| `CLONE_SYSVSEM` | Share the System V semaphore-adjustment list. |
| `CLONE_IO` | Share the I/O context, so the two are accounted as one for disk I/O. |
| `CLONE_PIDFD` | Return a pidfd for the new child. |
| `CLONE_PARENT` | Make the new task a sibling of the creator — its parent becomes the creator's parent, which is also what is signalled when the task ends. An init process (PID 1) cannot use this flag, as it would create unreapable zombies. |
| `CLONE_PARENT_SETTID` / `CLONE_CHILD_SETTID` | Record the new task's ID in the parent's / child's memory. |
| `CLONE_CHILD_CLEARTID` | Clear the recorded thread ID and wake a waiter when the task exits — the mechanism behind joining a thread. |
| `CLONE_UNTRACED` | Prevent a tracer from forcing tracing onto the new child. |
| `CLONE_VFORK` | Suspend the creator until the child `exec`s or exits (the `vfork` behaviour). |

A **thread** is `CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD`
(plus TLS and thread-ID bookkeeping) — everything shared, same process. A `fork`
is the opposite end, with almost nothing shared.

Being in one thread group has consequences beyond shared memory. Every thread
returns the same PID from `getpid` (the thread-group ID), and signal **actions** are
process-wide — an unhandled fatal signal delivered to any thread ends them all —
though each thread keeps its own signal mask. A thread that ends does not notify the
thread that created it and cannot be collected with a wait call; only once every
thread in the group has ended is the process's parent sent `SIGCHLD`. The new thread
shares the creator's parent, and `CLONE_THREAD` requires `CLONE_SIGHAND` (and hence
`CLONE_VM`).

Two further flag groups select **separation** rather than sharing, each documented
where it belongs:

- The `CLONE_NEW*` flags create **namespaces** — separate views of system
  resources (mounts, process IDs, networking, and more), covered under namespaces.
- `CLONE_INTO_CGROUP` places the new process into a **resource group** at creation,
  covered under resource management.

`CLONE_DETACHED` is a historical flag with no effect and is ignored.

## The exec family

An `exec` replaces the program running in the current process with a different one.
The process keeps its PID, its Process GUID, and its identity — only the program
changes (see [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle) for the identity detail).

| Call | What it does |
|---|---|
| `execve` | Replace the current program with the one at a given path. |
| `execveat` | Replace it with a program named relative to an open directory, or — with `AT_EMPTY_PATH` — by an open file descriptor directly. `AT_SYMLINK_NOFOLLOW` refuses a final symbolic link. |
| `fexecve` | Replace it with the program referred to by an open file descriptor (a thin wrapper over `execveat`). |

### What survives an exec

A successful `exec` keeps the process itself but replaces the program it runs.
Preserved across the call:

- the PID, the parent PID, and the Process GUID
- the process's identity (its token), its process group and session, and its
  controlling terminal
- open file descriptors — except those marked close-on-exec, which are closed
- the current directory, root directory, file-creation mask, and resource limits
- pending signals, and the dispositions of signals that were ignored or left at
  their default

Reset or discarded:

- all memory — the program's mappings, stack, heap, and data are replaced; memory
  locks are dropped and `MADV_*` region markings are gone
- every thread except the one calling `exec` — the new program starts single-threaded
- handlers for caught signals — reset to the default; the alternate signal stack is
  dropped
- attached System V shared memory, POSIX shared-memory mappings, open POSIX
  message-queue descriptors and named semaphores, and in-process synchronisation
  objects (mutexes, condition variables)
- POSIX timers, outstanding asynchronous I/O, open directory streams, and registered
  exit handlers
- the floating-point environment, and the process name (set to the new program)

What an `exec` does to a process's identity when the program file is marked to run
as another principal is **not** the Linux set-user-ID model — Peios handles that
through the token, covered in
[setuid and uid0](~peios/linux-compatibility/setuid-and-uid0).

Whether a program is allowed to run at all is a separate, execution-policy
question — covered under binary signing — not part of these calls.

## posix_spawn

`posix_spawn()` is the standard library function for the create-then-replace
pattern: it makes a new process and runs a named program in it with a single call,
with controls for arranging the child's file descriptors and a few attributes
first. It is built on the calls above and is the recommended way to launch a
program, in preference to assembling `fork`/`vfork` and `exec` by hand.

## Process handles (the pidfd family)

A **pidfd** is a file descriptor referring to one specific process — the reliable
handle introduced in
[Creating processes](~peios/threads-and-processes/creating-processes). `CLONE_PIDFD`
hands one back at creation; a few calls work with them afterwards:

| Call | What it does |
|---|---|
| `pidfd_open` | Obtain a pidfd for a process that already exists, given its PID. |
| `pidfd_send_signal` | Send a signal to the process through its pidfd — with no risk of the PID having been recycled for a different process in between. |
| `pidfd_getfd` | Duplicate one of the target process's open file descriptors into the caller. |

`pidfd_getfd` reaches into another process, so it is not something any process may
do to any other: it is gated by the right to act on the target, governed by that
process's [security descriptor](~peios/threads-and-processes/the-process-security-block).

## See also

- [Creating processes](~peios/threads-and-processes/creating-processes) — the conceptual counterpart to this page.
- [Process lifecycle reference](~peios/threads-and-processes/process-lifecycle-reference) — ending a process and collecting its result.
- [Thread operations reference](~peios/threads-and-processes/thread-operations-reference) — per-thread calls: TIDs, exit notification, TLS.
