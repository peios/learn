---
title: The Child Path
description: The deliberately minimal straight line between clone3 returning and execve — streams, signals, oom_score_adj and the environment.
---

Between `clone3` returning in the child and `execve`, peinit runs a
straight line of setup. The path is kept minimal — no logging, no
complex library calls — because it runs after a fork, where very little
is safe to do.

Each step reports through the error pipe with the identifier from §5.3
if it fails, then exits: `_exit(126)` for a setup failure, `_exit(127)`
for a failed exec. [*child.a-setup-failure-exits-126-and-a-failed-exec-127]

The steps, in the order the child runs them:
[*child.the-child-setup-order]

| # | Step | Id |
|---|---|---|
| 1 | Close the read end of the error pipe | 1 |
| 2 | `setsid()` — only with a `TTYPath` | 12 |
| 3 | Set the standard streams | 2 |
| 4 | `ioctl(TIOCSCTTY)` — only with a `TTYPath` | 13 |
| 5 | Reset the signal environment | 3 |
| 6 | Install the KACS token, then close its descriptor | 4 |
| 7 | Set `RLIMIT_NOFILE` and `RLIMIT_CORE` | 5 |
| 8 | Set `oom_score_adj` | 6 |
| 9 | Change the working directory | 7 |
| 10 | Confirm `NOTIFY_SOCKET` is present in the environment | 9 |
| 11 | Inject stored descriptors from fd 3 upward | 10 |
| 12 | `execve` | 11 |

## The terminal steps [*child.setsid-precedes-the-stream-setup]

`setsid()` comes first, and its position is load-bearing in two
directions. It has to precede the stream setup, because `setsid()` drops
any controlling terminal the child inherited — doing it afterwards would
throw away the terminal just attached. And it has to precede
`TIOCSCTTY`, which requires a session leader that does not already own a
controlling terminal.

`TIOCSCTTY` is passed a literal zero argument, which is what makes it
unable to steal a terminal already owned by another session.

Without a `TTYPath` neither step runs and the service stays in peinit's
session. [*child.without-a-ttypath-the-terminal-steps-do-not-run]

## The standard streams [*child.the-standard-streams]

Without a `TTYPath`: stdin from `/dev/null`, stdout and stderr onto the
write ends of the service's output pipes, and every inherited pipe end
that is no longer needed closed.

With a `TTYPath`: all three streams onto the opened terminal, and the
`/dev/null` descriptor and both pipe pairs closed.
[*child.a-terminal-attached-service-gets-the-terminal-on-all-three-streams]
A terminal-attached service's output is therefore **not** captured for
logging — it goes to the terminal, which is the point of asking for one.

## The signal environment [*child.the-signal-mask-is-emptied-and-dispositions-reset]

peinit blocks every signal for its signalfd (§12.3) and the child
inherits that mask across the fork. Step 5 empties the mask and resets
every resettable disposition to `SIG_DFL`. A service starting with
signals blocked, or with PID 1's handling in place, is one of the
classic ways for a daemon to behave inexplicably.

## oom_score_adj [*child.oom-score-adj-follows-error-control]

`-1000` — OOM-immune — for an `ErrorControl=Critical` service, and `0`
for everything else. A Critical service is one whose loss reboots the
machine, so letting the OOM killer choose it would convert memory
pressure into a reboot.

## The environment

There is no step that sets the environment, which is why identifier 8 is
reserved and never emitted. peinit builds the environment in the parent
(§5.5) and hands it to `execve` as `envp`, so it arrives with the exec
rather than being installed beforehand. Step 10 is a check rather than a
set: it confirms `NOTIFY_SOCKET` is present in the prebuilt environment
and fails with a synthetic `EINVAL` if it is not.
[*child.notify-socket-is-confirmed-not-set]

## What the child does not inherit [*child.only-the-streams-and-injected-descriptors-are-inherited]

A service inherits only what peinit hands it: its standard streams and
any descriptors injected from the fd store. Everything else peinit holds
is created close-on-exec — the control socket and every accepted
connection, the notification socket, the epoll instance, the signalfd,
every timerfd, both pidfds, every pipe, and every stored descriptor
until it is deliberately un-marked at injection.

The signal reset and the close-on-exec discipline together are what make
a service start from a clean context rather than from PID 1's
privileged one.

A descriptor opened through the Peios native file interface returns
*without* close-on-exec set, so it does not get the discipline for free.
peinit sets the flag by hand on each of those — the input devices it
opens for the power button, and the `main/` cgroup directory descriptor
it opens per launch — immediately after opening them, and nothing peinit
opens reaches a service's descriptor table.
[*child.natively-opened-descriptors-have-cloexec-set-by-hand]
