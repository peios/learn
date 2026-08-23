---
title: Persistence
description: Where last-run history lives in the registry, how a missed firing is caught up after a reboot, and when the timestamp is written.
---

`TimerPersistent`, on by default, controls whether a run missed across a
reboot is caught up.

## Where history lives

Last-run timestamps are `REG_QWORD` values in the registry, written
after a firing.

A service with a **single** timer trigger stores its timestamp as
`LastTimerRun` on the service's own key:

```
Machine\System\Services\<name>\LastTimerRun
```

A service with **multiple** triggers stores one per trigger under a
subkey, named by the schedule string:

```
Machine\System\Services\<name>\TimerState\<encoded-schedule>
```

A schedule contains characters — spaces, `:`, `*` — that are not valid
LCS value names, so the name is the schedule with every character
outside `[A-Za-z0-9._-]` percent-encoded, with uppercase hex digits.
This is the same encoding used for cgroup ids (§5.1). The schedule
`*-*-* 02:00:00` is stored as:

```
%2A-%2A-%2A%2002%3A00%3A00
```

Two identical schedule strings on one service encode to the same name
and therefore share one timestamp.

Timer firings are infrequent, so the write cost is negligible.

## Catching up

On boot, for each persistent trigger:

1. Read the last-run timestamp.
2. Compute the next scheduled firing after it.
3. If that time has already passed, at least one run was missed: fire
   once, immediately.
4. Compute the next future occurrence normally.

Catch-up is always a **single** run however many were missed. A daily
timer that missed five days fires once on the next boot, not five times.

A trigger with no history at all is treated the same way, so its first
boot produces one catch-up firing.

`TimerPersistent=0` ignores history entirely — peinit does not even read
the registry for that trigger, and computes the next occurrence from
now.

## When the timestamp is written

The timestamp is written after the timer fires and the start is
*initiated*, not after the service finishes. A service that crashes
mid-run is not re-triggered on the next boot: the run was attempted, not
missed.

A configuration reload re-arms every timer from the current time with no
catch-up, whatever `TimerPersistent` says. History is consulted at boot
only.

> [!NOTE]
> Timestamps for a multi-trigger service are keyed by schedule string,
> so changing a schedule orphans its history and the new schedule
> produces one spurious catch-up run. A stable trigger identifier would
> fix it; schedule changes are rare and one extra run is the whole cost.
> A single-trigger service is unaffected, since its timestamp lives at a
> fixed name.
