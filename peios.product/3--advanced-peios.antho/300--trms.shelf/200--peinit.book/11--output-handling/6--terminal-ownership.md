---
title: Terminal Ownership
description: A TTYPath has one owner at a time — how peinit picks it, what happens to the losers, and how a terminal is handed on when it comes free.
---

A `TTYPath` (§3.2) names a device that has exactly one owner at a time.
Two services writing to the same terminal do not fail; they interleave.
On a console that produces a login prompt with a progress line through
the middle of it, and a password echoed into whatever redrew last. So
peinit hands the device to one service and makes the others wait.

## Who is holding it

A service holds its terminal in every state where it may still have a
process on the device:

| Holding | Released |
|---|---|
| Starting, Active, Reloading, Stopping, **Backoff** | Inactive, Completed, Failed, Skipped, **Abandoned** |

The two emphasised entries are the ones worth stating outright.

**Backoff holds.** A service between restart attempts is coming back,
and handing its console to somebody else during the gap produces two
owners a second later. This is deliberately *not* the "settled" rule
used by `boot:settled` (§2.5), which also treats Backoff as still
moving, but reaches it from the opposite direction.

**Abandoned releases**, and that one is a compromise. The process
survived SIGKILL (§5.7) and may well still be writing. But peinit has no
remaining way to reclaim the device from it, so treating it as held
would mean the terminal is lost for the rest of the boot — and a console
nobody can log in on is worse than a console with a stuck process on it.

Nothing is stored. The holder is derived from the service table, so
there is no claim to leak, to double-release, or to fall out of step
with the state machine.

## Losing the terminal

Every start path — boot, deferred, on-demand, restart, and the
completion leg after a filesystem check helper (§5.2) — asks whether the
terminal is free before it asks anything else. If another service holds
it, the start ends there: the service goes to **Skipped** with cause
`TtyUnavailable` (§6.3), its operation completes, and its dependents are
satisfied exactly as any other skip satisfies them.

Skipped rather than Failed, because nothing is wrong. Nothing is written
to the console about it either — it is the mechanism working, and the
message would land on the very terminal whose new owner is at that
moment drawing on it.

The check runs ahead of the service's own conditions and asserts, which
is why a service queued on a busy terminal never forks a check helper.

## Winning the terminal

`TTYPrecedence` decides who wins when several services want the same
device at the same moment. Higher wins; equal precedence breaks on
service name, so an operator who states no preference still gets the
same machine on every boot rather than whichever definition the registry
happened to enumerate first. The default is 0.

Precedence is consulted among *simultaneous* candidates only. A service
that already holds a terminal is never preempted by a higher-precedence
latecomer: taking a live terminal away from a process that is using it
would lose whatever the operator was in the middle of typing.

Two places have simultaneous candidates. Deferred starts (§2.5) are
dispatched highest-precedence first, so the winner takes the device and
the rest are skipped. Handovers, below, pick one winner outright.

Within the Phase 2 boot plan the order is the dependency graph's, not
precedence's — a boot-plan terminal service is being written over by
peinit's own progress output anyway, which is what `boot:settled`
exists to avoid.

## Handing it on

A service that names a terminal and carries the `tty:released` trigger
(§3.4) is started when that terminal comes free. peinit watches every
transition out of a holding state, so it does not matter whether the
holder exited cleanly, crashed, was stopped by an administrator or was
evicted by a conflict — all four free the device, and the waiter is
wanted after a crash more than after a clean exit, not less.

Which terminal was released is recorded **on the transition**, not looked
up afterwards, and that is load-bearing rather than tidy. A service whose
definition has been removed loses its table entry the moment it reaches a
state that does not retain one (§3.8) — the same moment it releases its
terminal. Asking afterwards which `TTYPath` it had gets nothing.

That is not a corner case. It is precisely what a service that retires
itself does: remove its own definition so it never runs again, then exit.
First-boot setup is exactly that, and before the release rode on the
transition it ended by telling the operator they could log in, on a
console it had just vacated and nobody had been given.

One winner per release, chosen by precedence. Starting the whole queue
would have every loser immediately skipped again by the rule above:
the same outcome, reached noisily, with a skipped-looking service for
each.

Two services are never offered a terminal:

- **The one whose exit freed it.** It has the strongest claim on its own
  console, so without this exclusion the highest-precedence holder
  restarts itself on every exit — a restart policy with no budget, and
  one no waiter behind it ever gets past. Relaunching a service that
  stopped is `RestartPolicy`'s job (§6.4).
- **One whose definition has been removed** (§3.8), since it cannot be
  started at all.

A waiter is usually sitting in Skipped when its turn comes, from the
moment it lost the terminal. The handover starts it as an explicit start
would, which is the transition that takes a service out of Skipped
(§6.2) and re-evaluates its conditions.

## Why not Conflicts, or a dependency

`Conflicts` (§7.1) fails *both* services when they meet in one boot. The
services that want a terminal are the interactive ones — a login prompt,
an installer, a first-boot setup flow — so that answer is a machine with
no way into it.

A dependency says the wrong thing twice. A login prompt does not need
first-boot setup to have *run*; it needs the console to be free, and a
setup flow that failed frees it just as well as one that succeeded.
And naming the holder would mean rewriting every waiter each time the
set of things that might take the console changed.

What is left is a queue on a device, which is what this is.
