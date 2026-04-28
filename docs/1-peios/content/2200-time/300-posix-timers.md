---
title: POSIX Timers
type: concept
description: Per-process scheduled timers — create, arm, query, delete. Notification via signal or thread, integration with the real-time signal model.
related:
  - peios/time/clocks
  - peios/time/timerfd-and-intervals
  - peios/signals/real-time-signals
  - peios/signals/siginfo
---

The POSIX timer interface lets a process schedule a notification to fire at a specified absolute or relative time, optionally with a periodic repeat. Timers are per-process objects identified by an opaque `timer_t` handle; they are created, armed, queried, and destroyed through a small syscall family.

POSIX timers are the canonical answer for "I need to run code at a specific time, possibly periodically, possibly relative to a specific clock." They integrate cleanly with the [real-time signal](../signals/real-time-signals) model and provide a single coherent ABI across every clock the kernel supports.

## The interface

| Call | Purpose |
|---|---|
| `timer_create(clockid, &sigevent, &timerid)` | Create a timer associated with a clock and a notification configuration. Returns a handle. |
| `timer_settime(timerid, flags, &new_spec, &old_spec)` | Arm or disarm. Sets the initial expiry and periodic interval. |
| `timer_gettime(timerid, &spec)` | Query time remaining and current period. |
| `timer_getoverrun(timerid)` | Get the number of expirations missed because the previous notification was still pending. |
| `timer_delete(timerid)` | Destroy the timer and release its kernel resources. |

The flow:

```c
struct sigevent sev = {
    .sigev_notify = SIGEV_SIGNAL,
    .sigev_signo  = SIGRTMIN + 0,
    .sigev_value  = { .sival_int = 42 },  // tag in si_value
};

timer_t timer;
timer_create(CLOCK_MONOTONIC, &sev, &timer);

struct itimerspec spec = {
    .it_value    = { .tv_sec = 5, .tv_nsec = 0 },   // first expiry: 5s from now
    .it_interval = { .tv_sec = 1, .tv_nsec = 0 },   // periodic every 1s after
};
timer_settime(timer, 0, &spec, NULL);
```

The handler receives `siginfo` with `si_code == SI_TIMER`, `si_value.sival_int == 42`, and `si_overrun` populated with the count of missed expirations.

## Choosing a clock

The first argument to `timer_create` is any of the clocks documented in [Clocks](clocks). The most common choices:

- `CLOCK_REALTIME` — for "fire at this wall-clock moment." Subject to clock jumps; if `CLOCK_REALTIME` is stepped backward, timers may fire late or not fire at all.
- `CLOCK_MONOTONIC` — for "fire after this much elapsed time." Robust against clock-set events but pauses across suspend.
- `CLOCK_BOOTTIME` — for "fire after this much wall time including any suspends." Useful for activity-tracking-style timers that must fire even if the system slept.
- `CLOCK_REALTIME_ALARM` / `CLOCK_BOOTTIME_ALARM` — for "fire even if the system is suspended." These wake the system from suspend; using them as a timer source requires `SeWakeFromSleepPrivilege`.
- `CLOCK_PROCESS_CPUTIME_ID` — for "fire after this much CPU time." Useful for compute-time-bounded operations.
- `CLOCK_THREAD_CPUTIME_ID` — for "fire after this much CPU time on a specific thread." Used by per-thread CPU profilers.

## Notification methods

The `sigevent` argument controls how the timer notifies the process when it expires. Four notification types:

| `sigev_notify` | Behaviour |
|---|---|
| `SIGEV_SIGNAL` | Deliver the signal `sigev_signo` to the process. The signal carries `si_code == SI_TIMER`, `si_value` from `sigev_value`, and `si_overrun` from the kernel's overrun count. |
| `SIGEV_THREAD` | libc-level: the C library spawns a thread to run `sigev_notify_function(sigev_value)`. Implemented in userspace using `SIGEV_THREAD_ID` underneath. |
| `SIGEV_THREAD_ID` | Deliver the signal to a specific thread within the calling process (specified by `sigev_notify_thread_id`). |
| `SIGEV_NONE` | No notification. The process polls `timer_gettime` to see whether the timer has expired. |

`SIGEV_SIGNAL` is the standard path for asynchronous notification. Most uses fire a real-time signal (SIGRTMIN..SIGRTMAX) so the delivery is queued and carries the full siginfo payload — important for distinguishing multiple timers using the same signal number, which is done by tagging each timer with a distinct `sigev_value.sival_int` that comes back through `siginfo->si_value`.

`SIGEV_NONE` is the right choice when the process wants to poll — for example, a state machine that periodically checks "has the timeout fired yet?" without paying the signal-delivery cost.

## Timer overrun

If a timer is configured for a periodic interval shorter than the time between deliveries — common when the handler is slow, or when the signal is briefly blocked — multiple expirations can accumulate. POSIX timers track the *count* of missed expirations and expose it through `timer_getoverrun()` and via `siginfo->si_overrun` on signal-style deliveries.

This avoids the signal-queue-overflow problem of naive periodic timers: instead of pushing N delivery records into the signal queue (which has a finite size), the timer pushes a single delivery and reports "you missed N-1 ticks before this one." Handlers that care about per-expiration work read the overrun count and process accordingly:

```c
void timer_handler(int sig, siginfo_t *info, void *ucontext) {
    int missed = info->si_overrun;
    while (missed-- > 0) { do_one_tick(); }
    do_one_tick();
}
```

## Resource limits

Each timer consumes a small amount of kernel memory. The number of timers a process can have outstanding is bounded by `RLIMIT_SIGPENDING` (which also bounds queued real-time signals). A process that hits the limit gets `EAGAIN` from `timer_create` and must delete an existing timer before creating a new one.

This limit is enforced per-process (and on Peios specifically per-token, not per-UID — see the `feedback` pattern that all "per-user" Linux quotas become per-token-or-per-SID on Peios). The default value is generous; raising it for high-timer-count workloads is a registry-driven sysctl override.

## Security model

POSIX timers are entirely intra-process. There is no syscall that lets one process create or manipulate timers in another process. Timer operations therefore have no cross-process security implications — they don't go through any process SD check, and there's nothing to gate.

The notification path inherits the security properties of whichever signal is being delivered. A timer that fires `SIGRTMIN+0` to its own process delivers a signal with `si_code == SI_TIMER`; the receiver's process SD doesn't enter the picture because there is no "sender" — the kernel itself is generating the delivery in response to the timer's own configuration.

For wake-from-suspend timers (`CLOCK_REALTIME_ALARM`, `CLOCK_BOOTTIME_ALARM`), the privilege gate is at timer-creation time: `timer_create` with one of these clocks requires `SeWakeFromSleepPrivilege` and fails with `EPERM` otherwise. Once created, no further check applies.

## Comparison with other timer interfaces

POSIX timers are one of three modern timer interfaces on Peios:

| Interface | When to prefer |
|---|---|
| **POSIX timers** (this page) | Async signal-handler delivery, multiple distinct timers using the same signal (distinguished by `si_value`), CPU-time-based timers, integration with existing signal-driven code. |
| **`timerfd`** | Integration with `epoll`/`io_uring` event loops. Timer expirations become readable events on a file descriptor. See [timerfd and intervals](timerfd-and-intervals). |
| **`setitimer`** | Legacy. Fixed signals (SIGALRM/SIGVTALRM/SIGPROF), one timer per signal, no per-timer payload. Avoid in new code. See [timerfd and intervals](timerfd-and-intervals). |

For most new event-loop code, `timerfd` is the cleaner choice. POSIX timers remain useful for code that already deals in signals (a profiler that uses SIGPROF for sampling, a periodic-timer-driven state machine).

## See also

- [Clocks](clocks) — the clock IDs that timers can be associated with.
- [timerfd and intervals](timerfd-and-intervals) — fd-shaped timer interface and the legacy `setitimer` family.
- [Real-time signals](../signals/real-time-signals) — the queued-signal model that timers integrate with.
- [Signal information](../signals/siginfo) — `si_code`, `si_value`, `si_timerid`, `si_overrun`.
