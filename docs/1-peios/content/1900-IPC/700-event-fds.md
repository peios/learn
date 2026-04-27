---
title: Event-bearing File Descriptors
type: concept
description: File descriptors that deliver kernel events on Peios — eventfd, signalfd, timerfd, pidfd, and the access-controlled cross-process pidfd_getfd primitive.
related:
  - peios/IPC/epoll-and-polling
  - peios/IPC/io-uring
  - peios/IPC/fd-passing
  - peios/process-management/process-lifecycle
  - peios/process-security/process-security-descriptors
---

A family of Linux primitives takes events that historically arrived through other channels — signals, timers, process-state changes — and delivers them through file descriptors instead. The advantage: events become composable with `epoll`, `select`, `poll`, and the rest of the fd-readiness ecosystem. A single `epoll` loop can wait on file I/O, network events, signals, timers, and process exits uniformly.

This page covers `eventfd`, `signalfd`, `timerfd`, and the pidfd family.

## eventfd

`eventfd(initval, flags)` creates an fd associated with a 64-bit unsigned counter. Reads return the counter's value (and reset it to zero); writes add to the counter; the fd is "readable" via `epoll`/`poll`/`select` whenever the counter is non-zero.

| Flag | Effect |
|---|---|
| `EFD_CLOEXEC` | Close on `exec`. |
| `EFD_NONBLOCK` | Non-blocking by default. |
| `EFD_SEMAPHORE` | Read decrements the counter by 1 (semaphore mode) instead of resetting to zero. |

eventfd is the standard "kick someone awake" primitive for in-process synchronisation between threads, or cross-process via fd-passing. A worker pool can wait on an eventfd; the dispatcher writes 1 to wake one worker (with `EFD_SEMAPHORE`) or N to wake N workers (without).

eventfd is unprivileged and has no access control beyond the fd-bearer model: whoever holds the fd can read or write.

## signalfd

`signalfd(fd, &sigmask, flags)` creates (or modifies) an fd that delivers signals as readable events. The signals named in `sigmask` are still blocked from normal delivery; they are instead pending on the signalfd, and a `read` on the fd returns a `struct signalfd_siginfo` describing each pending signal.

| Flag | Effect |
|---|---|
| `SFD_CLOEXEC` | Close on `exec`. |
| `SFD_NONBLOCK` | Non-blocking. |

The point: signals become composable with `epoll`. A standard event loop can wait on file events, network events, and signals uniformly through one `epoll_wait` call. The traditional pattern of "block signals everywhere, install a handler that sets a flag, check the flag in the main loop" becomes "wait on signalfd in the main loop."

signalfd is unprivileged and per-process. You can only signalfd-receive signals delivered to your own process; cross-process signal interception is not what signalfd does.

## timerfd

`timerfd_create(clockid, flags)` creates an fd associated with a kernel timer. Arming the timer with `timerfd_settime` causes the fd to become readable when the timer expires; reading returns the number of expirations since the last read.

The clock IDs are the same as for `clock_gettime`: `CLOCK_REALTIME`, `CLOCK_MONOTONIC`, `CLOCK_BOOTTIME`, `CLOCK_REALTIME_ALARM`, `CLOCK_BOOTTIME_ALARM`. The realtime/boottime alarm clocks wake the system from suspend; the others do not.

| Flag | Effect |
|---|---|
| `TFD_CLOEXEC` | Close on `exec`. |
| `TFD_NONBLOCK` | Non-blocking. |
| `TFD_TIMER_ABSTIME` (in `settime`) | The expiration is an absolute time, not a relative duration. |
| `TFD_TIMER_CANCEL_ON_SET` (in `settime`) | Notify the consumer if the realtime clock is reset (e.g. by `settimeofday`). |

timerfd is unprivileged for normal clocks. The alarm clocks (`CLOCK_REALTIME_ALARM`, `CLOCK_BOOTTIME_ALARM`) require **`SeWakeFromSleepPrivilege`** — waking a sleeping system has system-wide impact and is not appropriate for unprivileged code. Default holders are TCB services that legitimately need to wake the system (a scheduled-task daemon, a maintenance window scheduler).

## pidfd

A **pidfd** is a stable kernel-attestable handle to a process. Unlike a PID, a pidfd does not recycle when the process exits and a new one inherits the PID. Operations on a stale pidfd (after the target has exited) fail with appropriate errors rather than silently misdirecting.

| Call | Purpose |
|---|---|
| `pidfd_open(pid, flags)` | Create a pidfd for an existing process. Substrate-as-is; no privilege required for self or for children. |
| `pidfd_send_signal(pidfd, sig, info, flags)` | Send a signal to the named process. Race-free vs PID reuse. Same access rules as `kill`. |
| `pidfd_getfd(pidfd, targetfd, flags)` | Steal an fd from the target process's fd table. |
| pidfd readability via `epoll` | A pidfd becomes readable when the target process exits. Lets event loops wait on process death. |

Pidfds are also produced by `clone3` with `CLONE_PIDFD`, returning the child's pidfd at process creation. This is the race-free way to handle "wait on this child" — capturing the pidfd at creation eliminates the window between `fork` and `pidfd_open`.

### pidfd_send_signal

Sending a signal via pidfd uses the same access checks as the equivalent `kill` syscall — see [Process Lifecycle](../process-management/process-lifecycle) — but is race-free against PID reuse. If the target has exited, `pidfd_send_signal` returns an error rather than potentially signalling a different process.

### pidfd_getfd — fd extraction

`pidfd_getfd(pidfd, targetfd, flags)` lets the caller take a duplicate of an fd from the target's fd table. The result is a fresh fd in the caller's table referring to the same underlying kernel object — equivalent to `dup` but cross-process.

This is a powerful primitive. Once you have the fd, you can read, write, and operate on it as if you'd opened it yourself, regardless of whether you have permission to open the underlying object directly. This is the inverse of [FD passing](fd-passing) — instead of the holder choosing to share, a third party with appropriate authority *takes*.

**Access control.** `pidfd_getfd` requires the **`PROCESS_DUP_HANDLE`** access mask on the target's process SD plus PIP dominance. The default DACL grants `PROCESS_DUP_HANDLE` to the process owner and to TCB-tier identities; ordinary processes cannot extract fds from arbitrary other processes.

The dedicated `PROCESS_DUP_HANDLE` mask (rather than reusing `PROCESS_VM_WRITE`) is intentional: extracting an fd is a meaningfully different capability from modifying memory, and the granular mask lets administrators grant fd-extraction authority to debugging or supervisory tooling without granting full memory access. This matches the Windows `PROCESS_DUP_HANDLE` design exactly.

Self-extraction (calling on a pidfd referring to your own process) is unrestricted and equivalent to a regular `dup`.

### pidfd as exit-notification

A pidfd added to an `epoll` set becomes readable when the target process exits. Reading the pidfd at that point returns nothing (it's a "level-triggered exit notification"); the consumer typically follows up with `waitid(P_PIDFD, pidfd, ...)` to collect the exit status.

This is the recommended pattern for waiting on processes. The traditional `wait`/`waitpid` interface has historical race conditions around PID reuse and SIGCHLD delivery; pidfd-based waiting is cleaner.

## Composability

The point of all of these is composability. A single `epoll` loop can wait on:

- File I/O (regular fds).
- Timers (timerfd).
- Signals (signalfd).
- Process exits (pidfd).
- Cross-thread wakeups (eventfd).
- Network I/O (socket fds).

This is the modern pattern for event-driven Peios services: one event loop, all event sources unified through fd-readiness, no special-case handling for any single category. See [epoll and polling](epoll-and-polling) for the readiness-checking primitives.

## See also

- [Epoll and polling](epoll-and-polling) — the fd-readiness primitives that consume these events.
- [io_uring](io-uring) — async event handling at higher scale.
- [FD passing](fd-passing) — the consensual inverse of `pidfd_getfd`.
- [Process lifecycle](../process-management/process-lifecycle) — wait, exit, and the pidfd-based replacements.
- [Process security descriptors](../process-security/process-security-descriptors) — the access mask vocabulary including `PROCESS_DUP_HANDLE`.
