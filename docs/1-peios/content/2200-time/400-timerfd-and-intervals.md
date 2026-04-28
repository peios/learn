---
title: timerfd and Interval Timers
type: concept
description: File-descriptor-shaped timers that integrate with epoll, and the legacy interval-timer interface (setitimer, alarm).
related:
  - peios/time/posix-timers
  - peios/time/clocks
  - peios/IPC/event-fds-and-pidfds
  - peios/IPC/epoll-and-polling
---

This page covers two related-but-distinct timer interfaces: **`timerfd`** (the modern fd-shaped variant) and the legacy **interval-timer** family (`setitimer`, `alarm`).

For the canonical modern timer interface — `timer_create` and friends — see [POSIX timers](posix-timers). For the underlying clocks all of these read from, see [Clocks](clocks).

## timerfd: timers as file descriptors

`timerfd` exposes timer expirations as readable events on a file descriptor, designed for integration with `epoll` and `io_uring` event loops. Where a POSIX timer fires a signal that interrupts whatever the process is doing, a timerfd posts a readability edge — the event loop notices it on its next iteration, reads the expiration count, and dispatches handler logic in normal thread context.

This is the right primitive for any code that already runs an event loop. No async-signal-safety constraints, no signal-mask juggling, no thread-targeting complexity.

### The interface

| Call | Purpose |
|---|---|
| `timerfd_create(clockid, flags)` | Create a timerfd associated with a clock. Returns an fd. |
| `timerfd_settime(fd, flags, &new_spec, &old_spec)` | Arm or disarm. Same `itimerspec` shape as POSIX timers. |
| `timerfd_gettime(fd, &spec)` | Query time remaining and current period. |

Creation flags:

| Flag | Effect |
|---|---|
| `TFD_CLOEXEC` | Set `O_CLOEXEC` on the fd — almost always wanted. |
| `TFD_NONBLOCK` | Make the fd non-blocking. `read()` returns `EAGAIN` if no expirations are pending. |

Settime flags:

| Flag | Effect |
|---|---|
| `TFD_TIMER_ABSTIME` | The `it_value` field is an absolute time on the chosen clock, not relative. |
| `TFD_TIMER_CANCEL_ON_SET` | If the underlying `CLOCK_REALTIME` is stepped, cancel the timer and have the next `read()` return `ECANCELED`. Useful for code that wants to know when wall-clock time jumped. |

### Reading expirations

`read()` on a timerfd returns an 8-byte unsigned 64-bit count: the number of expirations that have occurred since the last successful read.

```c
uint64_t expirations;
read(timerfd, &expirations, sizeof(expirations));
// expirations == number of times the timer fired since last read
```

If multiple expirations accumulated (the periodic interval was shorter than the time between reads), the count reports them all in one read — same conceptual model as POSIX timer overrun counts.

### Choice of clock

`timerfd_create` accepts the same clocks as `timer_create`: `CLOCK_REALTIME`, `CLOCK_MONOTONIC`, `CLOCK_BOOTTIME`, `CLOCK_REALTIME_ALARM`, `CLOCK_BOOTTIME_ALARM`. The wake-from-suspend variants (`*_ALARM`) require `SeWakeFromSleepPrivilege` at create time, same gate as POSIX timers.

CPU-time clocks (`CLOCK_PROCESS_CPUTIME_ID`, `CLOCK_THREAD_CPUTIME_ID`) are **not** valid for timerfd. Use POSIX timers if you need a CPU-time-based timer.

### Integration with event loops

A timerfd lives natively in an `epoll` set:

```c
int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC | TFD_NONBLOCK);
struct itimerspec spec = { .it_value = {1, 0}, .it_interval = {1, 0} };
timerfd_settime(tfd, 0, &spec, NULL);

epoll_ctl(epfd, EPOLL_CTL_ADD, tfd, &(struct epoll_event){
    .events = EPOLLIN, .data.fd = tfd
});
// ... in the event loop:
//   when tfd is readable, read 8 bytes for expiration count
```

The same fd is registered with `io_uring` via `IORING_OP_READ` or `IORING_REGISTER_EVENTFD`-style integration. See [Event fds and pidfds](../IPC/event-fds-and-pidfds) for the full ecosystem of fd-shaped notification primitives.

### Cross-references and security

A timerfd is just a file descriptor. It can be passed across `fork`, transferred via `SCM_RIGHTS` (a service that creates timers and hands the fds to client processes), or duplicated with `dup2`. The receiver of a passed timerfd can `read()` and `timerfd_gettime()` it; whether they can `timerfd_settime()` (re-arm or disarm) requires the same fd, no separate check applies.

There are no Peios-specific access checks beyond what the file-descriptor model provides for any other fd.

## Interval timers (legacy)

The interval-timer interface predates POSIX timers and timerfd by decades. It exists in the ABI for compatibility with old software but offers nothing the modern interfaces don't, plus several drawbacks.

| Call | Purpose |
|---|---|
| `setitimer(which, &new_spec, &old_spec)` | Arm an interval timer of type `which`. |
| `getitimer(which, &spec)` | Query current state. |
| `alarm(seconds)` | One-shot real-time alarm. Equivalent to `setitimer(ITIMER_REAL, ...)` with a single second-precision expiry. |

Three timer types, each tied to a fixed signal:

| `which` | Clock | Signal on expiry |
|---|---|---|
| `ITIMER_REAL` | Wall time (decremented in real time) | SIGALRM |
| `ITIMER_VIRTUAL` | User CPU time | SIGVTALRM |
| `ITIMER_PROF` | User + system CPU time | SIGPROF |

The drawbacks vs. modern interfaces:

- **One timer per type per process.** Calling `setitimer(ITIMER_REAL, ...)` twice replaces the first with the second.
- **Fixed signal numbers.** Multiple subsystems within one process that all want a periodic timer end up fighting over the same signal.
- **No payload.** The handler receives just the signal — no `si_value`, no way to tell "which logical timer fired" beyond the signal number.
- **Microsecond resolution at best.** The interface uses `struct timeval`, which doesn't expose nanosecond precision.

`alarm()` is even more constrained — single-second precision, single signal (SIGALRM), one outstanding alarm per process. Its primary use today is in test harnesses ("kill this test if it doesn't finish in N seconds") and in legacy single-purpose programs.

### When you'd still see them

Only in old code or in code that's been ported from old Unix substrates. New Peios code should use:

- `timerfd` for event-loop integration.
- `timer_create` (POSIX timers) for signal-driven code that needs distinct per-timer payloads.
- `epoll_wait` with a timeout for "wait at most N ms" patterns.

## See also

- [POSIX timers](posix-timers) — the modern signal-driven timer interface.
- [Clocks](clocks) — the underlying clock sources timers read from.
- [Event fds and pidfds](../IPC/event-fds-and-pidfds) — other fd-shaped notification primitives that compose with timerfd in event loops.
- [epoll and polling](../IPC/epoll-and-polling) — the event-loop interface most modern code uses to wait for timerfd events.
