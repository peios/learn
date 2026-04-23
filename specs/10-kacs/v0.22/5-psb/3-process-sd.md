---
title: Process Security Descriptors
---

Every process carries a security descriptor that controls who can perform operations on it. This replaces Linux's UID-based process access control (which is a patchwork of UID comparisons and capabilities) with unified SD evaluation.

## Process access rights

| Right | Value | Meaning |
|---|---|---|
| PROCESS_TERMINATE | 0x0001 | Send signals whose default action is process termination (see signal table below). |
| PROCESS_SIGNAL | 0x0002 | Send informational signals whose default action is ignore (SIGCHLD, SIGURG, SIGWINCH). |
| PROCESS_SUSPEND_RESUME | 0x0800 | Send signals whose default action is stop or continue (SIGSTOP, SIGTSTP, SIGTTIN, SIGTTOU, SIGCONT). |
| PROCESS_VM_READ | 0x0010 | Read process memory (ptrace peek, `/proc/<pid>/mem`, `process_vm_readv`). |
| PROCESS_VM_WRITE | 0x0020 | Write process memory (ptrace poke, `/proc/<pid>/mem`, `process_vm_writev`). Includes debugger attach. |
| PROCESS_DUP_HANDLE | 0x0040 | Extract file descriptors from the process (`pidfd_getfd`). |
| PROCESS_QUERY_INFORMATION | 0x0400 | Inspect the process's token, read detailed `/proc/<pid>/*` files (maps, status, fd, environ). |
| PROCESS_QUERY_LIMITED | 0x1000 | Read basic process information: PID, image name, state, CPU/memory usage. This is the level visible in `ps` and `top`. |
| PROCESS_SET_INFORMATION | 0x0200 | Change process priority, CPU affinity, I/O priority, resource limits. |
| READ_CONTROL | 0x20000 | Read the process's own SD. |
| WRITE_DAC | 0x40000 | Modify the process's DACL. |
| WRITE_OWNER | 0x80000 | Change the process's SD owner. |

## Signal classification

Each Linux signal maps to a process access right based on its default action:

### PROCESS_TERMINATE — default action: terminate (or terminate + core)

| Signal | # | Default | Notes |
|--------|---|---------|-------|
| SIGHUP | 1 | Terminate | Session hangup |
| SIGINT | 2 | Terminate | Ctrl-C |
| SIGQUIT | 3 | Terminate + core | Quit request |
| SIGILL | 4 | Terminate + core | Illegal instruction |
| SIGTRAP | 5 | Terminate + core | Debug trap |
| SIGABRT | 6 | Terminate + core | Abort |
| SIGBUS | 7 | Terminate + core | Bus error |
| SIGFPE | 8 | Terminate + core | Floating point exception |
| SIGKILL | 9 | Terminate | Forced kill (cannot be caught) |
| SIGUSR1 | 10 | Terminate | User-defined |
| SIGSEGV | 11 | Terminate + core | Segfault |
| SIGUSR2 | 12 | Terminate | User-defined |
| SIGPIPE | 13 | Terminate | Broken pipe |
| SIGALRM | 14 | Terminate | Alarm timer |
| SIGTERM | 15 | Terminate | Graceful termination request |
| SIGSTKFLT | 16 | Terminate | Stack fault |
| SIGXCPU | 24 | Terminate + core | CPU time exceeded |
| SIGXFSZ | 25 | Terminate + core | File size exceeded |
| SIGVTALRM | 26 | Terminate | Virtual timer |
| SIGPROF | 27 | Terminate | Profiling timer |
| SIGIO | 29 | Terminate | I/O possible |
| SIGPWR | 30 | Terminate | Power failure |
| SIGSYS | 31 | Terminate + core | Bad syscall |

### PROCESS_SUSPEND_RESUME — default action: stop or continue

| Signal | # | Default | Notes |
|--------|---|---------|-------|
| SIGSTOP | 19 | Stop | Forced stop (cannot be caught) |
| SIGTSTP | 20 | Stop | Terminal stop (Ctrl-Z) |
| SIGTTIN | 21 | Stop | Background read from terminal |
| SIGTTOU | 22 | Stop | Background write to terminal |
| SIGCONT | 18 | Continue | Resume stopped process |

### PROCESS_SIGNAL — default action: ignore

| Signal | # | Default | Notes |
|--------|---|---------|-------|
| SIGCHLD | 17 | Ignore | Child status change |
| SIGURG | 23 | Ignore | Urgent socket data |
| SIGWINCH | 28 | Ignore | Window resize |

> [!INFORMATIVE]
> Real-time signals (SIGRTMIN through SIGRTMAX, signals 32-64) have a default action of terminate. They require PROCESS_TERMINATE.

> [!INFORMATIVE]
> This classification applies only to signals sent by userspace processes (via `kill()`, `tkill()`, `tgkill()`). Kernel-generated signals (hardware faults like SIGSEGV/SIGBUS/SIGFPE, SIGCHLD from child exit, SIGPIPE from broken pipe) are delivered by the kernel and bypass the process SD check entirely — the LSM `task_kill` hook does not fire for kernel-originated signal delivery.

## Generic mapping

| Generic right | Maps to |
|---|---|
| GENERIC_READ | PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ \| READ_CONTROL |
| GENERIC_WRITE | PROCESS_SET_INFORMATION \| PROCESS_VM_WRITE \| WRITE_DAC |
| GENERIC_EXECUTE | PROCESS_TERMINATE \| PROCESS_SUSPEND_RESUME \| PROCESS_QUERY_LIMITED |
| GENERIC_ALL | PROCESS_TERMINATE \| PROCESS_SIGNAL \| PROCESS_SUSPEND_RESUME \| PROCESS_VM_READ \| PROCESS_VM_WRITE \| PROCESS_DUP_HANDLE \| PROCESS_SET_INFORMATION \| PROCESS_QUERY_INFORMATION \| PROCESS_QUERY_LIMITED \| READ_CONTROL \| WRITE_DAC \| WRITE_OWNER |

## Default process SD

Processes MUST receive a default SD at creation time:

```
Owner: <creator's primary token user SID>
Group: <creator's primary token primary group SID>
DACL:
  ALLOW  <process's own user SID>        GENERIC_ALL
  ALLOW  BUILTIN\Administrators           GENERIC_ALL
  ALLOW  SYSTEM                            GENERIC_ALL
  ALLOW  Everyone                          PROCESS_QUERY_LIMITED
SACL:
  SYSTEM_MANDATORY_LABEL  <process's token integrity level>  NO_WRITE_UP
```

This means:

- The process can do anything to itself.
- Administrators and SYSTEM have full control over all processes.
- Everyone can see basic process info (PID, name, status) -- this is what makes `ps` and `top` work for all users.
- Detailed inspection (token, memory, environment) is restricted to self, administrators, and SYSTEM.
- A lower-integrity process running as the same user is blocked from write-category operations (signals, memory write, token replacement) by MIC. This is the foundation of elevation isolation — an unelevated Medium-integrity process cannot tamper with an elevated High-integrity process even when both run under the same user SID.

Services MAY request a custom SD at launch (via the service definition), or modify their own SD at runtime (via `kacs_set_sd` on their own process, which requires WRITE_DAC -- granted by the default SD to the process itself).

## PIP interaction

PIP and the process SD are complementary. The process SD controls *who* can perform operations on the process. PIP controls *which trust level is required* for invasive access to protected processes. Both checks MUST pass:

1. AccessCheck evaluates the caller's token against the target process's SD for the requested right.
2. PIP evaluates the caller's trust level against the target's `pip_type` and `pip_trust` (for operations that cross the process boundary).

A process MAY have a permissive SD (Administrators: GENERIC_ALL) but be PIP-protected -- administrators pass the SD check, but only if their PIP trust level is sufficient. Conversely, a non-PIP process MAY have a restrictive SD that denies even administrators specific operations.

## Thread security model

KACS does not define per-thread security descriptors or thread-specific access rights. All thread operations are gated by the process SD.

This is an intentional architectural decision. Linux threads share the process address space (`mm_struct`), so per-thread isolation has limited security value — a thread that can write the shared address space can compromise any other thread in the same process. Per-thread SDs would add complexity without meaningful isolation.

Consequence: `kacs_open_thread_token` gates access using the process SD (PROCESS_QUERY_INFORMATION). A caller who passes the process SD check can open any thread's impersonation token within that process. If finer-grained token isolation is required, the service should use separate processes rather than separate threads.
