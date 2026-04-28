---
title: Signals on Peios
type: concept
description: How signals work on Peios — the access-mask model that gates signal sending, PIP dominance, and the carve-out for kernel-originated signals.
related:
  - peios/process-security/process-security-descriptors
  - peios/pip/understanding-pip
  - peios/process-management/core-dumps
  - peios/seccomp/seccomp-overview
---

A **signal** is a short asynchronous notification delivered to a process or a specific thread. Every running process has a set of registered handlers (or default actions) for each signal number, and a set of currently-blocked signals it has chosen not to receive right now. When a signal is delivered, the kernel either runs the handler, applies the default action (terminate, stop, continue, ignore), or queues the signal until the process unblocks it.

Signals predate most of Unix's other IPC mechanisms. They are intentionally small — a number, optionally a payload — and intentionally asynchronous: the kernel can deliver one between any two instructions, which makes signal handlers some of the most constrained code in any program. Despite their age and their warts, signals remain the canonical way to terminate, suspend, resume, and wake processes.

This page covers the security model: who can send signals to whom, how that decision is made, and how Peios's KACS evaluation slots into the existing Linux signal API.

## The send and the deliver

Two distinct events happen for every signal:

- **Send.** Some agent — a userspace process via `kill()`, `tgkill()`, `pidfd_send_signal()`, or the kernel itself — asks for a signal to be delivered to a target process or thread. The send is where the security check lives.
- **Deliver.** The kernel runs the target's handler, applies a default action, or queues the signal pending the target's unblock. Delivery is unaffected by the sender's identity; the target's own configuration governs what happens.

Most security questions about signals are really questions about the send. A successful send is "I have authority to interrupt you in the way this signal interrupts you." Once that authority is established, the rest is mechanical.

## The access-mask model

On Linux, the kernel decides whether a process may send a signal by checking the sender's UID against the target's UID, with a `CAP_KILL` bypass for privileged callers. Peios replaces that with a uniform AccessCheck against the **target's process security descriptor**, the same way every other process-targeting operation is gated.

Three access masks divide the signal space according to the *default action* of each signal:

| Mask | Value | Covers signals whose default action is | Examples |
|---|---|---|---|
| `PROCESS_TERMINATE` | 0x0001 | Terminate (or terminate + core dump). | SIGTERM, SIGKILL, SIGINT, SIGHUP, SIGSEGV, SIGABRT, all real-time signals (SIGRTMIN..SIGRTMAX). |
| `PROCESS_SUSPEND_RESUME` | 0x0800 | Stop or continue execution. | SIGSTOP, SIGTSTP, SIGTTIN, SIGTTOU, SIGCONT. |
| `PROCESS_SIGNAL` | 0x0002 | Ignore. | SIGCHLD, SIGURG, SIGWINCH. |

A process that holds `PROCESS_TERMINATE` on a target can send any lethal signal to it, including SIGKILL. A process that holds only `PROCESS_SUSPEND_RESUME` can pause and resume the target but cannot kill it. A process that holds only `PROCESS_SIGNAL` can deliver informational signals (such as SIGWINCH for terminal-resize notifications) but cannot interfere with the target's execution.

This split is intentional. Most processes legitimately need to receive informational signals from a wide range of senders (a window manager wants to deliver SIGWINCH; a network daemon wants to deliver SIGCHLD to a child-reaper) but should be guarded against arbitrary termination by those same senders. The default DACL on a process SD reflects this — the standard pattern grants `PROCESS_SIGNAL` widely, `PROCESS_SUSPEND_RESUME` and `PROCESS_TERMINATE` only to the process's own user, administrators, and SYSTEM.

> [!INFORMATIVE]
> The full per-signal classification is in the [process security descriptor specification](../process-security/process-security-descriptors). When a new signal is added to the kernel ABI, its mask is determined by its default action, automatically slotting into the existing access-control framework.

## Real-time signals

Signals 32 through 64 — the **real-time signals** — all have a default action of terminate, so they all require `PROCESS_TERMINATE` to send. Real-time signals are queued (not coalesced like standard signals), can carry a payload via `sigqueue()`, and have a defined priority order. The full discussion is on [Real-Time Signals](real-time-signals); for the purposes of access control they are no different from any other terminate-default signal.

## PIP dominance

The SD check is necessary but not sufficient. Every process-to-process signal send also goes through a **PIP dominance check**: the sender's process integrity (`pip_type` and `pip_trust`) must dominate the target's. PIP applies uniformly regardless of which signal is being sent — even SIGKILL is gated by PIP.

This means:

- A medium-integrity process running as the same user as a PIP-protected high-integrity process cannot kill it, even though both share a user SID.
- An administrator process at a lower trust band cannot interrupt a higher-trust service. Lifecycle management of PIP-protected services flows through `peinit`, which runs at the highest trust band and dominates everything.
- `SeDebugPrivilege`, which bypasses the SD check for diagnostic tooling, **does not** bypass PIP. There is no privilege that lets a non-dominant principal signal a PIP-protected target.

The combination is straightforward: AccessCheck on the SD answers *who is allowed*, PIP dominance answers *what trust band is required*. A signal send succeeds only if both checks pass.

> [!INFORMATIVE]
> PIP enforcement on signals is identical to PIP enforcement on memory access, ptrace attach, and resource-limit changes — see [PIP enforcement points](../pip/enforcement-points) for the full picture.

## Userspace senders versus kernel senders

The access-mask model applies only to **userspace-originated signal sends** — the explicit calls a process makes via `kill()`, `tkill()`, `tgkill()`, `pidfd_send_signal()`, `sigqueue()`, and friends. These are the signals where some agent is asking the kernel to deliver something on its behalf, and where the question "is this agent allowed to do this?" makes sense.

A second class of signals is generated by the kernel itself in response to events that the receiving process caused or that the kernel needs to inform it about:

| Signal | Cause |
|---|---|
| SIGSEGV | Process accessed unmapped or protection-violating memory. |
| SIGBUS | Process accessed memory at a bad alignment, or beyond the end of a memory-mapped file. |
| SIGFPE | Floating-point exception, integer divide by zero. |
| SIGILL | Process executed an illegal instruction. |
| SIGTRAP | Hit a debugger breakpoint or single-step trap. |
| SIGSYS | Made a syscall denied by a seccomp filter. |
| SIGCHLD | Child process changed state (exit, stop, continue). |
| SIGPIPE | Wrote to a pipe or socket whose reader has closed. |
| SIGIO / SIGPOLL | Asynchronous I/O readiness. |
| SIGURG | Out-of-band data on a socket. |
| SIGALRM | Process's alarm timer expired. |
| SIGXCPU / SIGXFSZ | Process exceeded a resource limit. |

These signals bypass the process SD check entirely. There is no userspace agent doing the send — the kernel observed an event and is informing the affected process. Authorising the kernel against the target's own SD would be meaningless. PIP also does not apply: the kernel is not a principal, and the signal is intrinsic to the receiver's own situation.

The receiving process can still tell these apart from userspace-sent signals by examining the `si_code` field in the siginfo struct, covered in [Signal Information](siginfo).

## Identifying the sender

When a signal arrives, the receiving process can inspect the **siginfo** struct to learn who sent it. The `si_uid` field is automatically populated with the sender's effective UID — *truth-projected* from the sender's effective token (the impersonation token if active, otherwise the primary token), in the same fsuid-style way that `SO_PEERCRED` reflects truth on Unix sockets. A receiver that authenticates senders by inspecting `si_uid` therefore gets a UID derived from real KACS state, not a self-asserted value.

For Peios-strength identity (a SID, not a UID), the receiver reads `si_pid` from siginfo, opens a pidfd against the sender with `pidfd_open`, and obtains the sender's token via `kacs_open_process_token`. This goes through the existing process-token access path and gives the receiver as much identity information as it has authority to read.

The full discussion of siginfo and sender identity is on [Signal Information](siginfo).

## Threads, process groups, and pidfds

Three different ways to name a signal target:

| Call | Target |
|---|---|
| `kill(pid, sig)` | A process (whole thread group). One thread is chosen to handle the signal. |
| `kill(-pgid, sig)` | All processes in the process group. Each one is access-checked independently. |
| `tgkill(tgid, tid, sig)` | A specific thread within a specific process. |
| `pidfd_send_signal(pidfd, sig, ...)` | The process referred to by the pidfd. Race-free — pidfds cannot be reused. |

The access check is the same in all four cases: AccessCheck against the *process's* SD plus PIP dominance. Peios does not define per-thread security descriptors — see the [thread security model note](../process-security/process-security-descriptors) for why.

For the process-group case (`kill(-pgid, sig)`), each member process is checked independently. If the sender is authorised against some members and not others, the signal is delivered only to the authorised ones; the call as a whole returns success if at least one delivery succeeded, otherwise `EPERM`.

`pidfd_send_signal` is the modern interface and the recommended one for any code path where PID reuse could matter — between the `kill(pid, ...)` call and the kernel's lookup, a PID can be recycled to a different process; pidfds eliminate that race.

## Catching, blocking, ignoring

The receiving side controls what actually happens to a delivered signal. Three knobs:

- **Handler installation.** `sigaction()` registers a function to run when a signal arrives. The function executes with restrictions on what it may safely call (see [Handlers and Masks](handlers-and-masks)).
- **Signal mask.** A per-thread set of signals that are currently blocked. A blocked signal stays pending; it is delivered when unblocked.
- **Default action.** If no handler is installed and the signal is unblocked, the kernel takes the signal's default action — terminate, stop, continue, or ignore.

Two signals are special: **SIGKILL and SIGSTOP** cannot be caught, blocked, or ignored. There is no userspace mechanism to handle them. A process receiving SIGKILL terminates; a process receiving SIGSTOP suspends. This is a load-bearing design decision: it guarantees that a process holding `PROCESS_TERMINATE` or `PROCESS_SUSPEND_RESUME` plus PIP dominance can always end or pause the target. Bugs and malicious code cannot prevent termination by trapping every signal.

## Core dumps

A subset of terminate-default signals — SIGQUIT, SIGILL, SIGTRAP, SIGABRT, SIGBUS, SIGFPE, SIGSEGV, SIGSYS, SIGXCPU, SIGXFSZ, plus uncaught real-time signals in some configurations — produce a **core dump** in addition to terminating the process. The dump captures the process's memory state for post-mortem debugging.

Core dumps are sensitive: they contain arbitrary process memory, including credentials, decrypted data, and cryptographic keys. Peios's core-dump policy — registry-driven generation modes, PIP-aware storage and access control, audit on every generation and every read — is documented in full at [Core Dumps](../process-management/core-dumps). The signal-side knobs (`prctl(PR_SET_DUMPABLE)` for narrowing, `RLIMIT_CORE` for size capping) are honoured normally and clamped by the system policy.

## Seccomp and SIGSYS

Processes can voluntarily restrict their own syscall surface using **seccomp** filters; a denied syscall can be configured to deliver SIGSYS to the offending process. Seccomp is a self-restriction primitive distinct from KACS-based authorisation, with its own design considerations and audit knobs. The full discussion is in the [Seccomp](../seccomp/seccomp-overview) chapter.

## See also

- [Process security descriptors](../process-security/process-security-descriptors) — the SD model that gates signal sending.
- [PIP enforcement points](../pip/enforcement-points) — the dominance check for cross-process operations including signals.
- [Standard signals catalogue](standard-signals) — every POSIX signal with its default action and required mask.
- [Real-time signals](real-time-signals) — queued delivery, payloads, priority.
- [Handlers and masks](handlers-and-masks) — signal-handler installation, blocking, alternate stacks.
- [Signal information](siginfo) — siginfo_t, si_code, sender identity.
- [Seccomp](../seccomp/seccomp-overview) — voluntary syscall filtering and SIGSYS.
- [Core dumps](../process-management/core-dumps) — generation policy, storage, access control.
