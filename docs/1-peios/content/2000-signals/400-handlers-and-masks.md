---
title: Handlers, Masks, and Alternate Stacks
type: concept
description: How a process registers signal handlers, controls which signals are blocked, runs handlers on a separate stack, and waits for signals synchronously.
related:
  - peios/signals/signals-on-peios
  - peios/signals/siginfo
  - peios/signals/standard-signals
---

This page covers the receiving side of signals: registering handlers, blocking and unblocking signals, running handlers on alternate stacks, and waiting for signals synchronously instead of asynchronously. The send side and access control are covered in [Signals on Peios](signals-on-peios).

The Peios kernel honours these APIs as the Linux ABI specifies. There are no Peios-specific deviations in handler installation, mask manipulation, or signal-stack handling — these are mechanical, per-process, in-process operations that don't touch security boundaries.

## Installing a handler

Two ways:

| Call | Purpose |
|---|---|
| `signal(sig, handler)` | Legacy, simplified. Cross-platform behaviour was historically inconsistent (whether the handler is reset to `SIG_DFL` after one call, whether other signals are blocked during the handler, etc.). Avoid in new code. |
| `sigaction(sig, &act, &oldact)` | The reliable interface. Specifies a handler, a flags bitmap, and a per-handler signal mask. |

`sigaction` takes a `struct sigaction`:

```c
struct sigaction {
    void (*sa_handler)(int);
    void (*sa_sigaction)(int, siginfo_t *, void *);
    sigset_t sa_mask;
    int sa_flags;
};
```

Either `sa_handler` or `sa_sigaction` is the function that runs on signal delivery. Two special values:

- `SIG_DFL` — restore the default action (terminate, stop, ignore, etc., depending on the signal).
- `SIG_IGN` — ignore the signal entirely. The kernel discards it without delivery.

`sa_mask` is a set of signals to block during execution of this handler, beyond the signal itself. `sa_flags` selects optional behaviours.

## Handler flags

| Flag | Effect |
|---|---|
| `SA_SIGINFO` | Deliver via `sa_sigaction` with `siginfo_t` and `ucontext_t` arguments instead of `sa_handler`. Required for any non-trivial signal handling. |
| `SA_RESTART` | If the signal interrupts a slow syscall (read, write, accept, etc.), the kernel automatically restarts the syscall after the handler returns instead of returning `EINTR`. |
| `SA_NODEFER` | Don't block this signal during its own handler. Without this flag, a handler for SIGUSR1 will not be re-entered if SIGUSR1 arrives during its execution. |
| `SA_RESETHAND` | After delivery, the handler is reset to `SIG_DFL`. One-shot delivery. |
| `SA_ONSTACK` | Run the handler on the alternate signal stack registered via `sigaltstack()`. Required when the normal stack might be exhausted (the SIGSEGV-on-stack-overflow case). |
| `SA_NOCLDSTOP` | Suppress SIGCHLD delivery for stopped (vs. terminated) children. |
| `SA_NOCLDWAIT` | Don't create zombies for children of this process; the kernel reaps them automatically. |

`SA_RESTORER` exists in the ABI but is set by libc; applications never touch it.

## SA_RESTART and EINTR

A blocking syscall (`read`, `write`, `accept`, `select`, etc.) interrupted by a signal returns `-1` and sets `errno = EINTR`. Code is expected to either retry manually or set `SA_RESTART` so the kernel does it automatically.

`SA_RESTART` works for most slow syscalls but **not all** — `select`, `poll`, `epoll_wait`, `nanosleep`, `pause`, `sigsuspend`, and a handful of others always return `EINTR` regardless of the flag. Robust code handles `EINTR` defensively even when `SA_RESTART` is set.

## Signal masks

Each thread has a **signal mask**: the set of signals currently blocked from delivery. A signal that arrives while it is blocked becomes pending; it stays pending until the mask changes to unblock it (at which point it is delivered immediately) or until the process exits.

Three calls manipulate the mask:

| Call | Scope |
|---|---|
| `sigprocmask(how, &set, &oldset)` | Single-threaded programs only. Behaviour in multi-threaded programs is undefined; use `pthread_sigmask` instead. |
| `pthread_sigmask(how, &set, &oldset)` | The thread-aware version. Mask changes affect only the calling thread. |
| `rt_sigprocmask` | The actual syscall behind both. |

`how` is one of:

| Value | Effect |
|---|---|
| `SIG_BLOCK` | Add `set` to the current mask. |
| `SIG_UNBLOCK` | Remove `set` from the current mask. |
| `SIG_SETMASK` | Replace the mask with `set`. |

Pending signals are inspected with `sigpending()`.

**SIGKILL and SIGSTOP cannot be masked.** Attempts to add them to the mask succeed at the API level but have no effect — they will still be delivered.

## Per-thread signal masks

In a multi-threaded program, the signal mask is per-thread, but the set of installed handlers is per-process. When a process-directed signal arrives (e.g., `kill(pid, sig)`), the kernel chooses an arbitrary thread that currently has the signal unblocked and delivers it there. If no thread has it unblocked, the signal stays pending against the process until some thread unblocks it.

Common pattern in multi-threaded programs:

1. Block all signals in the main thread before creating worker threads.
2. Workers inherit the all-blocked mask, so they receive no asynchronous signals.
3. A dedicated **signal-handling thread** unblocks the signals it cares about and uses `sigwaitinfo()` (synchronous wait, see below) to receive them.

This avoids the worst pitfalls of async signal handling — the handler thread can call any function it likes because it isn't running in interrupted context.

## Synchronous signal waiting

Signal handlers run asynchronously and are restricted to "async-signal-safe" functions (a small subset of the C library). For programs that just want to *receive* signals as events without the handler-context restrictions, three calls turn signal delivery into a synchronous operation:

| Call | Behaviour |
|---|---|
| `sigwait(set, &sig)` | Block until any signal in `set` arrives, store its number in `sig`, return. The signal is consumed without invoking any handler. |
| `sigwaitinfo(set, &info)` | Like `sigwait`, but also fills in a `siginfo_t`. |
| `sigtimedwait(set, &info, &timeout)` | Like `sigwaitinfo`, with a timeout. Returns `EAGAIN` if no signal arrives in time. |

The signals being waited for must be blocked in the calling thread — otherwise they would be delivered to a handler instead of caught by the wait. The pattern is:

```c
sigset_t set;
sigemptyset(&set);
sigaddset(&set, SIGUSR1);
pthread_sigmask(SIG_BLOCK, &set, NULL);

while (1) {
    siginfo_t info;
    sigwaitinfo(&set, &info);
    // handle signal at our leisure, in normal thread context
}
```

For signal-driven programs, this pattern is dramatically simpler than async handler code. `signalfd()` (covered in [Event fds and pidfds](../IPC/event-fds-and-pidfds)) is the same idea but exposed as a file descriptor that fits an `epoll` loop.

## sigsuspend

`sigsuspend(&mask)` is a convenience: it atomically replaces the current signal mask with `mask`, waits for a signal to arrive, runs its handler, restores the original mask, and returns. It exists to close a race where naive code unblocks a signal, calls `pause()`, and gets stuck if the signal arrived between the unblock and the `pause`.

## Alternate signal stacks

A signal handler runs on the same stack as the interrupted code by default. This is fine for most signals, but a problem for SIGSEGV — if SIGSEGV was raised because of a stack overflow, there is no stack space left to run the handler on, and the handler immediately re-faults.

`sigaltstack(&stack, &oldstack)` registers an **alternate stack**: a separate memory region the kernel uses for handlers installed with `SA_ONSTACK`. Typical pattern:

```c
stack_t ss;
ss.ss_sp = malloc(SIGSTKSZ);
ss.ss_size = SIGSTKSZ;
ss.ss_flags = 0;
sigaltstack(&ss, NULL);

struct sigaction sa = {
    .sa_sigaction = segv_handler,
    .sa_flags = SA_SIGINFO | SA_ONSTACK,
};
sigaction(SIGSEGV, &sa, NULL);
```

Now if SIGSEGV fires due to stack overflow, the handler runs on the dedicated alternate stack and can do useful work — log the crash, write a diagnostic, attempt graceful shutdown.

The alternate stack is per-thread. Multi-threaded programs that need SIGSEGV-on-overflow handling must register an alternate stack for each thread.

## Async-signal safety

A handler can be invoked at any point in the program's execution — including in the middle of a `malloc()`, in the middle of a stdio call, while holding a lock. Handler code is restricted to **async-signal-safe** functions: ones the kernel and libc guarantee can be safely called from a handler.

The async-signal-safe set is small. Roughly: low-level syscalls (`read`, `write`, `_exit`, `kill`, `sigaction`), the `string.h` functions that don't allocate, and the `<errno.h>` macros. **`malloc`, `free`, `printf`, anything that takes a pthread mutex, anything that uses errno without saving and restoring, anything that touches stdio — not safe.**

The standard discipline is: signal handlers do nothing except set a flag (`volatile sig_atomic_t`) or write to a self-pipe / eventfd. The main loop notices the flag or wakes from `epoll` and does the real work in normal context.

The synchronous-wait pattern (`sigwaitinfo` in a dedicated thread) sidesteps async-signal-safety entirely — the wait runs in a normal thread, so the handler-shaped work is just regular thread code.

## See also

- [Signals on Peios](signals-on-peios) — security model, `kill()` and friends.
- [Signal information](siginfo) — `siginfo_t`, `si_code`, identifying the sender.
- [Event fds and pidfds](../IPC/event-fds-and-pidfds) — `signalfd` and other ways to receive signals as fd events.
