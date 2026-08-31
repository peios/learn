---
title: Evaluation and Arming
description: A timer is a trigger rather than a service type — how one is armed, how it fires, and what multiple triggers do.
---

A timer is a trigger, not a service type. A service with a
`timer:<schedule>` trigger is an ordinary Simple or Oneshot service that
peinit starts on a schedule.

## Arming

At boot, once the service graph is loaded, and whenever timer
configuration changes, peinit computes the next firing time for every
active trigger and arms a timerfd for it. Each trigger gets its own
descriptor and its own computation.

A disabled service gets neither a registration nor a firing.

A schedule that fails to parse, or whose next occurrence cannot be
computed, fails that trigger. Every other timer arms normally, and what
did not arm is reported to the console. This matches how graph
validation already treats an invalid schedule (§7.4), so the outcome no
longer depends on which of the two caught it.

The next-occurrence search looks ten years ahead and then gives up. A
schedule can parse and still match nothing — `*-02-30`, or a fixed year
already past — and the horizon turns that into a prompt error against
the one service rather than a very long walk. Ten years clears the
sparsest schedule that is genuinely meaningful: `*-02-29` skips a
century year not divisible by 400, so it can run eight years dry.

## Firing

```
handle_timer(service, trigger):
    // 1. Decide what the firing means, from the service's state.
    match (service.type, service.state):
        (Oneshot, Active | Starting):
            service.pending_timer = true      // at most one
        (Simple,  Active | Starting):
            record the firing; no action
        (_, Inactive | Completed | Failed):
            create_operation(Start, service, source = Timer)

    // 2. Record when it fired.
    write the last-run timestamp to the registry   // asynchronously

    // 3. Re-arm.
    next = next_occurrence(trigger.schedule, now) + random(0, TimerJitter)
    arm an absolute CLOCK_REALTIME timerfd for next
```

Every other state — Backoff, Stopping, Reloading, Abandoned, Skipped —
records the firing and does nothing.

The last-run write happens in a forked child so that the event loop
never waits on the registry — which matters because the registry is
served by registryd, a service peinit supervises, so a synchronous write
would let a wedged registryd stall PID 1.

The parent returns immediately with the child's pid, and remembers it.
When the child is reaped, peinit matches its exit status back to the
write; a failure is reported:

```
peinit warning: recording the last run of timer <schedule> for service
<service> failed; it will run catch-up again after a reboot
```

The write stays best-effort — nothing is retried and nothing is failed
over it — but a persistent timer whose timestamp never lands runs its
catch-up on every boot, and that is otherwise a symptom with no thread
to pull. The outstanding-write table is bounded, so a child that somehow
escapes reaping cannot grow it.

## Oneshot pending runs

A Oneshot that fires while it is already running sets a flag rather than
queueing an operation. When it next reaches Inactive or Completed,
peinit immediately creates a start operation and clears the flag.

Multiple firings during one run collapse into a single pending run.
There is no queue, and the flag is per service rather than per trigger —
a service with three timers that all fire during one long run still gets
exactly one catch-up.

## Multiple triggers

Triggers on one service are independent: each has its own timerfd, its
own next-firing computation, and its own last-run history. Only the
Oneshot pending flag is shared.
