---
title: Real-Time Signals
type: concept
description: The real-time signal range (SIGRTMIN to SIGRTMAX) — queued delivery, payloads, priority ordering, and how POSIX timer expiry uses them.
related:
  - peios/signals/signals-on-peios
  - peios/signals/standard-signals
  - peios/signals/siginfo
---

The signal numbers 32 through 64 are the **real-time signals** (RT signals). Unlike the standard POSIX signals, RT signals are queued individually, carry a small payload from sender to receiver, and have a defined priority ordering. They are the closest thing the signal mechanism has to a general-purpose IPC primitive.

Real-time signals are useful when:

- An application needs to receive multiple instances of the same logical event without losing any.
- The sender wants to attach a small data payload to the signal — a tag, an ID, a pointer to shared state.
- The receiver wants strict priority among multiple signal sources.

For most uses, modern alternatives like `eventfd`, `signalfd`, or message queues are simpler and more flexible. Real-time signals remain the canonical way to receive POSIX timer expiries.

## What "real-time" means here

The term is a historical artefact from POSIX 1003.1b — the realtime extensions, which standardised these signals alongside POSIX timers, message queues, and shared memory. It does not imply that delivery has bounded latency or any other realtime-system guarantee. The kernel makes a best effort to deliver them promptly, the same as any other signal.

## The three properties

### Queued delivery

A standard signal that arrives while the same signal is already pending is **coalesced** — only one delivery happens, even if the signal was sent ten times. This loses count: a process that sends SIGUSR1 ten rapid-fire times to a target with SIGUSR1 currently blocked produces a single SIGUSR1 delivery when the target unblocks.

Real-time signals are **queued**. Each send produces a distinct queue entry. If a process sends SIGRTMIN+0 ten times to a target, the target's handler runs ten times when the signal becomes deliverable, in send order, with each delivery's siginfo intact.

The kernel imposes a per-process limit on queued real-time signals (`RLIMIT_SIGPENDING`). If the queue is full, `sigqueue()` returns `EAGAIN` and the sender retries.

### Payload via sigqueue

Standard signals carry only "this signal arrived, and these are the kernel-supplied siginfo fields." Real-time signals can carry an additional **`si_value`** payload — either a 32-bit integer or a pointer-sized value — chosen by the sender.

```c
union sigval val;
val.sival_int = 42;
sigqueue(target_pid, SIGRTMIN, val);
```

The receiver sees `info->si_value.sival_int == 42` (or `sival_ptr` if a pointer was sent). This is enough room for a small tag — a request ID, an opcode, an index into shared state — but not for arbitrary data.

`kill()` can also send real-time signals, but it does not provide a payload. The receiver sees `si_value` set to a default value and `si_code` set to `SI_USER`, distinguishing the kill-style send from the sigqueue-style send.

### Priority ordering

When multiple signals are pending for delivery, real-time signals are dispatched in **lowest-number-first** order — SIGRTMIN before SIGRTMIN+1, and so on. Within a single signal number, queued instances are delivered in FIFO order.

Standard (non-realtime) signals do not have a defined ordering relative to each other; the kernel chooses some sensible deterministic ordering but applications should not rely on it.

## Sending real-time signals

| Call | Notes |
|---|---|
| `sigqueue(pid, sig, value)` | The canonical real-time signal send. Carries a payload. |
| `rt_sigqueueinfo(pid, sig, info)` | Lower-level syscall that sigqueue is built on. Allows fully-custom siginfo. |
| `rt_tgsigqueueinfo(tgid, tid, sig, info)` | Same, but targets a specific thread within a process. |
| `kill(pid, sig)` | Sends a real-time signal but with no payload. `si_code` is `SI_USER`. |
| `tgkill(tgid, tid, sig)` | Thread-targeted kill, no payload. |

All of these go through the same access-control gate as any other signal send: `PROCESS_TERMINATE` on the target's SD plus PIP dominance. (Real-time signals all default to terminate, hence the heaviest mask.) See [Signals on Peios](signals-on-peios) for the full security model.

## How many real-time signals are there

The kernel reserves the first two RT signals (typically SIGRTMIN+0 and SIGRTMIN+1) for libc internal use — NPTL uses them for thread cancellation and timer-thread coordination. Applications get SIGRTMIN+2 through SIGRTMAX, which works out to about 30 usable signal numbers on Linux.

Software should refer to these by the symbolic names `SIGRTMIN+N` rather than absolute numbers, since the values can shift between libc versions.

## POSIX timers and real-time signals

The most common use of real-time signals is **POSIX timer expiry**. `timer_create(CLOCK_REALTIME, &sigevent, &timerid)` creates a timer; the `sigevent` argument specifies how expiry should be delivered. When `sigevent.sigev_notify` is `SIGEV_SIGNAL`, expiry produces a real-time signal whose `si_value` carries the timer's user-supplied tag.

This is how a single process can manage hundreds of timers and tell their expiries apart — each timer is created with a distinct `sigev_value`, and the handler reads `info->si_value` to identify which timer fired. The siginfo `si_code` is `SI_TIMER` for these deliveries, and `si_overrun` reports how many expiries happened between the previous delivery and this one (relevant when the receiver is too slow to keep up with a fast-firing timer).

POSIX message queues use the same mechanism for queue-state notifications: `mq_notify()` registers for delivery via real-time signal when a previously-empty queue becomes non-empty.

## Choosing real-time vs other primitives

For a new design, prefer:

- **`signalfd`** when you want to convert signal delivery into a normal file descriptor that fits an `epoll` loop. The signal arrives as a struct read from the fd; no async handler context.
- **`eventfd`** when the only thing you need is a wake-up edge with a counter, and the sender already has a way to coordinate with the receiver out-of-band.
- **POSIX message queues** when the payload doesn't fit in `si_value` (16 bytes), or when you want priorities and proper queue semantics.

Real-time signals are the right choice when you specifically need:

- Signal-handler-context delivery (e.g., a debugger or runtime that intercepts execution at signal-delivery points).
- POSIX timer expiry, where the API already pushes you toward `SIGEV_SIGNAL`.
- A small, queued, prioritised event channel where adding a new IPC mechanism would be overkill.

## See also

- [Signals on Peios](signals-on-peios) — the security model that gates real-time signal sending.
- [Standard signals catalogue](standard-signals) — the 31 non-realtime signals.
- [Signal information](siginfo) — `si_code`, `si_value`, and how senders are identified.
- [Event fds and pidfds](../IPC/event-fds-and-pidfds) — `signalfd` and other fd-shaped notification primitives.
