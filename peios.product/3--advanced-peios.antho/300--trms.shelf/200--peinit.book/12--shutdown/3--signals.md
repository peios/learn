---
title: Signals
description: Every signal is blocked and read through a signalfd from the event loop — the setup, the signals handled, and reaping.
---

PID 1 handles every signal through a signalfd. All signals are blocked
and read from the event loop, so there are no signal handlers and no
async-signal-safety concerns anywhere in peinit.

## Setup

peinit builds a mask containing every blockable signal in the supported
range — SIGKILL and SIGSTOP are not blockable and are never delivered
through a signalfd — and installs it with
`rt_sigprocmask(SIG_BLOCK, ...)` **before** entering the main event
loop. It then creates the descriptor with `signalfd4(-1, mask, ...)`,
using the same mask, with `SFD_CLOEXEC | SFD_NONBLOCK`.

If any part of that fails — blocking, creating the descriptor,
retaining it, registering it with the event loop — peinit fails closed.
There is no fallback to asynchronous handlers, because a PID 1 with
handlers installed where it expected a signalfd is a PID 1 whose
assumptions about what can interrupt it are wrong.

The mask is inherited across fork, which is why every child resets it
before exec (§5.4).

## The signals

| Signal | Behaviour |
|---|---|
| SIGCHLD | Reap children with `waitpid`. Match them to tracked jobs; also reap orphans belonging to nothing. |
| SIGINT | Reboot. Three within five seconds forces one. |
| SIGTERM | Poweroff. |
| SIGPWR | Poweroff. |
| SIGHUP | Ignored. PID 1 has no controlling terminal. |
| SIGPIPE | Ignored. A broken pipe on the control socket cannot be allowed to kill PID 1. |

Everything else is ignored. The kernel protects PID 1 from fatal
signals, so no signal can kill it.

## Reaping

peinit reaps with `waitpid(-1, ..., WNOHANG)` in a drain loop, and
normalises the wait status before any service or job policy sees it:

- An exited child carries its exact exit code, 0–255.
- A signalled child carries the terminating signal number and whether
  the core-dump bit was set.
- A stopped or continued status is invalid on this path, because peinit
  never asks for them. Observing one **fails closed** rather than being
  interpreted.

That last rule matters more than it looks. A stopped child reported as
an exit would be read as a service that had terminated, and peinit would
act on a process that is merely paused.

As PID 1, peinit also reaps processes nobody is tracking — orphans
reparented to it — and reports them as untracked rather than trying to
attribute them to a service.
