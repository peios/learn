---
title: Process Security Descriptors
description: The descriptor controlling who may operate on a process — the access rights, signal classification, what bypasses the check, and the default.
---

Every process carries a security descriptor controlling who may
operate on it, stored on the PSB alongside the PIP and mitigation
fields. It replaces Linux's UID-based process access control — a
patchwork of UID comparisons and capabilities — with a single
descriptor evaluation.

## Process access rights

| Right | Value | Meaning |
|---|---|---|
| `PROCESS_TERMINATE` | 0x0001 | Send signals whose default action is termination. |
| `PROCESS_SIGNAL` | 0x0002 | Send informational signals whose default action is to ignore: `SIGCHLD`, `SIGURG`, `SIGWINCH`. |
| `PROCESS_VM_READ` | 0x0010 | Read process memory — ptrace peek, `/proc/<pid>/mem`, `process_vm_readv`. |
| `PROCESS_VM_WRITE` | 0x0020 | Write process memory — ptrace poke, `/proc/<pid>/mem`, `process_vm_writev`. Includes debugger attach. |
| `PROCESS_DUP_HANDLE` | 0x0040 | Extract file descriptors from the process through `pidfd_getfd`. |
| `PROCESS_SET_INFORMATION` | 0x0200 | Change priority, CPU affinity, I/O priority, resource limits, process group membership where Linux permits it, timer slack, memory-placement policy or pages, and mutable `/proc/<pid>` task state — `sched`, `autogroup`, `timens_offsets`, `timerslack_ns`, `coredump_filter`, `oom_adj`, `oom_score_adj`, `make-it-fail`, `fail-nth`, `latency` and `clear_refs`, plus write intent on the coupled `uid_map`, `gid_map`, `projid_map` and `setgroups` seq files. |
| `PROCESS_QUERY_INFORMATION` | 0x0400 | Inspect the process's token; read the detailed `/proc/<pid>/*` files — `cmdline`, `status`, `io`, `limits`, `sched`, `autogroup`, `timens_offsets`, `personality`, `syscall`, `latency`, `timers`, `timerslack_ns`, `mounts`, `mountinfo`, `mountstats`, `coredump_filter`, `oom_adj`, `oom_score_adj`, `loginuid`, `make-it-fail`, `fail-nth`, `seccomp_cache`, `ksm_merging_pages` and `ksm_stat` — plus read intent on the coupled `uid_map`, `gid_map`, `projid_map` and `setgroups` seq files; query Linux compatibility capability state through `capget(pid)`; and query detailed scheduler, CPU-affinity and I/O-priority state. |
| `PROCESS_SUSPEND_RESUME` | 0x0800 | Send signals whose default action is to stop or continue. |
| `PROCESS_QUERY_LIMITED` | 0x1000 | Read basic process information: PID, process group ID, session ID, image name, state, CPU and memory usage — `stat`, `statm`, `comm`, `wchan`, `schedstat`, `cpuset`, `cgroup`, `cpu_resctrl_groups`, `oom_score`, `sessionid`, `patch_state`, `stack_depth` and `arch_status`. This is what `ps` and `top` show, it covers `/proc/<pid>/stat`, and it is the right required for `pidfd_open()` and for `kill(pid, 0)` existence probes. |
| `READ_CONTROL` | 0x20000 | Read the process's own descriptor. |
| `WRITE_DAC` | 0x40000 | Modify the process's DACL. |
| `WRITE_OWNER` | 0x80000 | Change the descriptor's owner. |

Three `/proc` entries are not where the right names suggest.
`maps`, `fd` and `environ` are not gated by
`PROCESS_QUERY_INFORMATION`: they keep their upstream
`PTRACE_MODE_READ_FSCREDS` gating, which maps to **`PROCESS_VM_READ`**
— reading a process's memory map is treated as reading its memory,
which is defensible but is not what the right's name implies. And
`cgroup` sits in the **`PROCESS_QUERY_LIMITED`** set rather than the
detailed one.

## Signal classification

Each Linux signal maps to a process access right according to its
default action.

Signal 0 is not delivered at all. A `kill()`, `tkill()`, or `tgkill()`
call with signal 0 is an existence and permission probe, requiring
`PROCESS_QUERY_LIMITED` on the target plus PIP dominance.

**`PROCESS_TERMINATE`** — default action terminate, or terminate with
a core dump:

| Signal | # | Default | Notes |
|---|---|---|---|
| `SIGHUP` | 1 | Terminate | Session hangup |
| `SIGINT` | 2 | Terminate | Ctrl-C |
| `SIGQUIT` | 3 | Terminate + core | Quit request |
| `SIGILL` | 4 | Terminate + core | Illegal instruction |
| `SIGTRAP` | 5 | Terminate + core | Debug trap |
| `SIGABRT` | 6 | Terminate + core | Abort |
| `SIGBUS` | 7 | Terminate + core | Bus error |
| `SIGFPE` | 8 | Terminate + core | Floating point exception |
| `SIGKILL` | 9 | Terminate | Forced kill, cannot be caught |
| `SIGUSR1` | 10 | Terminate | User-defined |
| `SIGSEGV` | 11 | Terminate + core | Segfault |
| `SIGUSR2` | 12 | Terminate | User-defined |
| `SIGPIPE` | 13 | Terminate | Broken pipe |
| `SIGALRM` | 14 | Terminate | Alarm timer |
| `SIGTERM` | 15 | Terminate | Graceful termination request |
| `SIGSTKFLT` | 16 | Terminate | Stack fault |
| `SIGXCPU` | 24 | Terminate + core | CPU time exceeded |
| `SIGXFSZ` | 25 | Terminate + core | File size exceeded |
| `SIGVTALRM` | 26 | Terminate | Virtual timer |
| `SIGPROF` | 27 | Terminate | Profiling timer |
| `SIGIO` | 29 | Terminate | I/O possible |
| `SIGPWR` | 30 | Terminate | Power failure |
| `SIGSYS` | 31 | Terminate + core | Bad syscall |

**`PROCESS_SUSPEND_RESUME`** — default action stop or continue:

| Signal | # | Default | Notes |
|---|---|---|---|
| `SIGSTOP` | 19 | Stop | Forced stop, cannot be caught |
| `SIGTSTP` | 20 | Stop | Terminal stop, Ctrl-Z |
| `SIGTTIN` | 21 | Stop | Background read from terminal |
| `SIGTTOU` | 22 | Stop | Background write to terminal |
| `SIGCONT` | 18 | Continue | Resume a stopped process |

**`PROCESS_SIGNAL`** — default action ignore:

| Signal | # | Default | Notes |
|---|---|---|---|
| `SIGCHLD` | 17 | Ignore | Child status change |
| `SIGURG` | 23 | Ignore | Urgent socket data |
| `SIGWINCH` | 28 | Ignore | Window resize |

The real-time signals, `SIGRTMIN` through `SIGRTMAX` (32–64), default
to terminate and therefore require `PROCESS_TERMINATE`.

### What bypasses the check

This classification applies only to signals sent by userspace through
`kill()`, `tkill()`, and `tgkill()`. Kernel-generated signals —
hardware faults such as `SIGSEGV`, `SIGBUS` and `SIGFPE`, `SIGCHLD`
from a child exiting, `SIGPIPE` from a broken pipe — are delivered by
the kernel and bypass the process descriptor check entirely, because
the `task_kill` LSM hook does not fire for kernel-originated delivery.

Terminal-generated job control signals are kernel-originated under
that rule and bypass the check the same way: `SIGINT`, `SIGQUIT` and
`SIGTSTP` from the tty driver's `isig` handling, and `SIGHUP` on
hangup. This is intentional. Authorization for keyboard-driven signals
is possession of the controlling terminal, which was gated by the
terminal's file descriptor at open time — so Ctrl-C reaches the whole
foreground process group even when a member of it is more privileged
or more PIP-trusted than whoever holds the terminal. A process that
cannot accept that exposure must not attach to an untrusted
controlling terminal.

The `si_uid` in a delivered signal's `siginfo_t` is the sender's
projected UID (§3.10), captured at send time. Like every projected
credential surface it is informational only and is not an
authorization input; `si_pid` carries the same caveat and is subject
to PID reuse besides.

## Generic mapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `PROCESS_QUERY_INFORMATION \| PROCESS_VM_READ \| READ_CONTROL` |
| `GENERIC_WRITE` | `PROCESS_SET_INFORMATION \| PROCESS_VM_WRITE \| WRITE_DAC` |
| `GENERIC_EXECUTE` | `PROCESS_TERMINATE \| PROCESS_SUSPEND_RESUME \| PROCESS_QUERY_LIMITED` |
| `GENERIC_ALL` | every process right above, together with `READ_CONTROL`, `WRITE_DAC` and `WRITE_OWNER` |

## The default process descriptor

Every process receives a default descriptor at creation:

```
Owner: <creator's primary token user SID>
Group: <creator's primary token primary group SID>
DACL:
  ALLOW  <process's own user SID>   GENERIC_ALL
  ALLOW  BUILTIN\Administrators     GENERIC_ALL
  ALLOW  SYSTEM                     GENERIC_ALL
  ALLOW  Everyone                   PROCESS_QUERY_LIMITED
```

A process can therefore do anything to itself; Administrators and
SYSTEM have full control over every process; everyone can see basic
process information, which is what makes `ps` and `top` work for all
users; and detailed inspection — token, memory, environment — is
restricted to the process itself, administrators, and SYSTEM.

A service can modify its own descriptor at runtime with
`kacs_set_sd`, which requires `WRITE_DAC` — granted to the process
itself by the default DACL. Requesting a custom descriptor *at launch*
through a service definition is not implemented: the only descriptor
creation path always builds the default template, so every process
starts from it and any deviation is a subsequent write.

## How PIP relates to it

PIP and the process descriptor are complementary, and both checks have
to pass. The descriptor controls *who* may operate on the process; PIP
controls *what trust level* is required for invasive access to a
protected one. AccessCheck evaluates the caller's token against the
target's descriptor for the requested right, and PIP evaluates the
caller's trust against the target's `pip_type` and `pip_trust` for
operations crossing the process boundary.

The two are genuinely independent. A process may have a permissive
descriptor granting Administrators `GENERIC_ALL` and still be
PIP-protected, so administrators pass the descriptor check and are
stopped only by insufficient PIP trust.

The converse — a process with no PIP protection carrying a restrictive
descriptor that denies even administrators — holds with one
qualification. When a descriptor check denies access and PIP was not
the deciding factor, an enabled `SeDebugPrivilege` on the caller
grants the access anyway and is marked used. The privilege therefore
rescues a descriptor denial while remaining unable to cross a PIP
boundary, which is exactly the split §3.4.2 describes for it.
