---
title: Process Lifecycle
type: concept
description: How processes terminate, how parents collect their exit status, what happens to children whose parent dies, and the handles that make waiting and signalling race-free.
related:
  - peios/process-management/understanding-process-creation
  - peios/process-security/understanding-process-security
  - peios/process-management/core-dumps
---

A process on Peios runs from `exec()` through some amount of work and ends in one of two ways: it terminates voluntarily by calling `exit()`, or it is terminated by a signal it does not catch. Either way, it does not vanish immediately. The kernel keeps a small piece of state alive — the process's exit status — until the parent process collects it. This intermediate state is called a **zombie**, and the dance between exit, zombie, wait, and reparenting is what this page is about.

## Termination

Two syscalls end execution:

- **`exit_group()`** terminates the entire process — every thread in the thread group, immediately. This is what the C library's `exit()` and a normal `return` from `main()` ultimately call.
- **`exit()`** terminates only the calling thread. The rest of the process continues. Used by threading libraries internally; rarely called directly by application code.

Termination releases most of the process's kernel resources: file descriptors are closed (firing any registered close-on-exec or pidfd notifiers), memory mappings are torn down, locks are released, signal handlers are dropped. What remains is the **task struct** carrying the exit status, just enough kernel state for a parent to inspect, and is held until either the parent waits for it or the parent itself exits.

A terminated-but-uncollected process is a **zombie**. It has no memory, no open files, and no executable state. It exists only as a record waiting to be acknowledged.

## Waiting

A parent collects a zombie child's exit status by calling one of the wait family of syscalls:

| Syscall | Use |
|---|---|
| `waitpid()` | Wait for a specific child or any child. The traditional interface. |
| `wait4()` | Like `waitpid()` but also returns resource usage (`struct rusage`). |
| `waitid()` | Extended interface. Specify what to wait for (`P_PID`, `P_PGID`, `P_PIDFD`, `P_ALL`) and observe stop/continue events as well as exits. |

Wait calls take a flag set that controls what state changes count as "interesting":

| Flag | Meaning |
|---|---|
| `WEXITED` | Wait for normal exit (default). |
| `WSTOPPED` | Also wake on stop signals (`SIGSTOP`, `SIGTSTP`). |
| `WCONTINUED` | Also wake on continuation (`SIGCONT`) of a previously stopped child. |
| `WNOHANG` | Don't block — return immediately if no child has changed state. |
| `WNOWAIT` | Peek at the state without reaping it. The zombie remains a zombie. |
| `__WALL`, `__WCLONE` | Filters for waiting on `clone()`-created children with non-default exit signals. |

When a child terminates, the kernel sends the parent a `SIGCHLD`. A parent that ignores or blocks `SIGCHLD` still has the children sitting as zombies; if the parent never waits for them, they accumulate. Conventional supervisors install a `SIGCHLD` handler that calls `waitpid()` in a loop until no more zombies remain.

A parent can also explicitly opt out of being notified of child exits by setting `SIGCHLD` to `SIG_IGN` (or by using `SA_NOCLDWAIT`). With this flag set, children of the parent are auto-reaped on exit and produce no zombies.

## Reparenting and subreapers

When a process exits before its children, those children are **reparented** — the kernel rewrites their parent field to point somewhere else. By default, the new parent is **PID 1 (peinit)**, which is structurally guaranteed to wait for any orphan that lands on it.

This guarantee makes peinit the "parent of last resort." A double-forking daemon — fork, fork again, exit the middle process — produces a grandchild whose original parent has exited; that grandchild is reparented to peinit, which keeps the system from accumulating zombies regardless of how careless the original parent was.

A process can opt to be the reaping target for its descendants' orphans rather than handing them off to peinit:

```c
prctl(PR_SET_CHILD_SUBREAPER, 1);
```

After this call, any descendant process that is orphaned anywhere below the calling process in the tree is reparented to the **nearest still-living ancestor** that has the subreaper attribute set, instead of being reparented all the way to PID 1. This is the mechanism behind service managers, terminal multiplexers, and container runtimes that need to keep "their" processes within their own subtree.

Subreaper status is **not gated** on Peios. Any process can declare itself a subreaper for its own descendants; the call is self-targeting and has no equivalent for setting it on another process. Becoming a subreaper does not grant the process any authority over the orphans it adopts — sending signals, reading memory, attaching a debugger, and waiting all still go through the orphan's process security descriptor. Subreaper status only routes `SIGCHLD` and the right to call `waitpid`; it does not change what the new parent can do once it has the handle.

## Pidfds

Traditional process identification uses PIDs, which are integers reused after a process exits. This creates well-known race conditions: between observing a PID and acting on it, the process can exit and its number can be assigned to a different process. **Pidfds** solve this by giving each process a stable file-descriptor handle that refers to that process and only that process, never reused even if the PID is.

Three operations create or use pidfds:

- **`pidfd_open(pid, flags)`** returns a pidfd for an existing process. On Peios this requires `PROCESS_QUERY_INFORMATION` on the target's process SD — issuing a handle to a process you cannot otherwise inspect would leak existence information and create observable timing channels through pidfd-based polling.
- **`CLONE_PIDFD`** to `clone()` returns a pidfd to the parent at the same time the child is created. No race window, no separate access check.
- **`pidfd_getfd(pidfd, target_fd)`** retrieves a copy of a file descriptor from another process by its pidfd. Subject to `PROCESS_DUP_HANDLE` on the target's SD.

Once a parent has a pidfd, it can:

- `waitid(P_PIDFD, pidfd, ...)` — wait for the process to exit, race-free.
- `pidfd_send_signal(pidfd, sig, ...)` — signal it without risking PID reuse confusion.
- Poll the pidfd with `epoll`/`poll` and be woken when the process exits.

Pidfds are the recommended interface for any code that observes another process. Operations through a pidfd carry their normal access checks against the target's SD; the pidfd itself just removes the PID-reuse race.

## Task states

Every task — process or thread — is in one of a small set of states the kernel tracks:

| State | Meaning |
|---|---|
| Running (`R`) | Currently executing or eligible to be scheduled. |
| Sleeping (`S`) | Waiting for an event (interruptible). |
| Disk Sleep (`D`) | Waiting on uninterruptible I/O — typically a disk operation. Cannot be woken by signals. |
| Stopped (`T`) | Suspended by `SIGSTOP` / `SIGTSTP` or by a debugger. |
| Traced (`t`) | Stopped under `ptrace` for debugging. |
| Zombie (`Z`) | Terminated, exit status not yet collected. |
| Dead (`X`) | Fully released. Not normally observable. |

These states are visible via `/proc/<pid>/status` and in tools like `ps`. They are observational — Peios does not introduce additional states or hide existing ones — but observing them is gated by the process SD: a caller without `PROCESS_QUERY_INFORMATION` cannot read `/proc/<pid>/status` and therefore cannot observe a process's state.

## Process accounting (`acct`)

`acct()` is a legacy Linux mechanism for writing a fixed-format record to a file every time a process exits — historically used for billing on time-shared Unix systems. Peios honours it for backward compatibility with Linux software that depends on it, but it is **strongly discouraged for new Peios applications**. Structured lifecycle events flow through eventd, which is the modern, queryable equivalent and the recommended path.

Calling `acct()` to enable or disable system-wide accounting requires `SeTcbPrivilege` (mapped from Linux's `CAP_SYS_PACCT`). See the Linux `acct(2)` documentation for the file format and per-record fields.

## Core dumps

When a process is terminated by an uncaught fatal signal, the kernel may write a snapshot of the process's memory, registers, and mappings to a file or pipe — a **core dump**. Because dumps contain potentially sensitive process state (token material, secrets, environment), Peios applies its own dump policy on top of the Linux substrate's mechanism. See [Core dumps](core-dumps) for the full rules, including the policy framework, protected-process exclusion, and how dumps are routed.
