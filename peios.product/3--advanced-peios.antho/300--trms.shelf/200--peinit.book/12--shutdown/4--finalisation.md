---
title: Finalisation
description: The three shutdown paths that reach the kernel and how much work each does on the way, including what survives a failure.
---

Three shutdown paths reach the kernel, and they do different amounts of
work on the way.

| Path | Stop waves | Seed save | Unmount | Sync | Final action |
|---|---|---|---|---|---|
| Graceful | Yes | Yes | Yes | Yes | Yes |
| Forced — three SIGINTs | No, SIGKILL everything | No | No | Yes | Yes |
| Critical service failure | No | No | No | Yes | Yes |

The two abrupt paths are required to reach `sync()` and the final kernel
action with minimal additional work, and skipping the seed and the
unmounts is what "minimal" means. A machine that is rebooting because
its audit daemon died has nothing to gain from a tidy unmount and
something to lose from the time it takes.

## What survives a failure

Steps 6 and 7 — the seed and the unmounts — retain their failures as
evidence rather than acting on them. Every one is recorded, none of them
blocks step 8, and none of them enters recovery mode. By this point
there is nothing to recover *to*: services have stopped and the
filesystems are on their way down.

## If the final action returns

`reboot(2)` does not return on success. If it does, the final action
failed, and peinit enters a minimal failed-shutdown state:

- PID 1 stays alive. It has to — PID 1 exiting panics the kernel.
- The failure is recorded.
- The same action is retried, no more than once a second.
- Services are not restarted, and recovery mode is not entered.

There is no way back from here. Finalisation has begun, the services are
gone and the filesystems are read-only; the only correct behaviour is to
keep trying the one thing that would end it.

`RB_HALT_SYSTEM` does not return either, so this state is only reachable
for a genuine failure rather than for the halt case.

## A note on the mount table

The unmount step re-reads `/proc/self/mountinfo` when checking whether a
mount point that returned `ENOENT` or `EINVAL` is really gone. Depth
ordering puts the depth-one mounts last, alphabetically — `/dev`,
`/proc`, `/run`, `/sys` — so `/proc` is unmounted before `/run` and
`/sys` are attempted, and the check for those two cannot read the file
it needs. The result is a recorded cleanup failure and a pointless
read-only remount attempt at the tail of every graceful shutdown.
