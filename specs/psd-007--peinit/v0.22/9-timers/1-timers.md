---
title: Timers
---

Timers are a trigger type, not a service type. A service with a
`timer:<schedule>` trigger is a regular Simple or Oneshot service
that peinit starts on a schedule. Timer semantics are defined here;
the trigger model is defined in §3.1.

## Calendar expressions

Timer schedules use the following format:

```
DayOfWeek Year-Month-Day Hour:Minute:Second Timezone
```

Each field supports:

- **Wildcards:** `*` matches any value.
- **Lists:** `1,15` matches either value.
- **Ranges:** `Mon..Fri` matches Monday through Friday.
- **Repetition:** `*:00/15:00` matches every 15 minutes.
- **Last day:** `~01` in the day field means last day of month.
  `~02` means second-to-last day.

All fields except Timezone are optional with implicit wildcards.
DayOfWeek is omitted entirely if not needed. Timezone is omitted
to use system-local time.

### Shortcuts

| Shortcut | Equivalent |
|---|---|
| `daily` | `*-*-* 00:00:00` |
| `hourly` | `*-*-* *:00:00` |
| `weekly` | `Mon *-*-* 00:00:00` |
| `monthly` | `*-*-01 00:00:00` |

### Timezone

Timezone specifiers follow the IANA timezone database format (e.g.,
`Europe/London`, `US/Eastern`, `UTC`). Expressions without a
timezone are interpreted in system-local time.

### DST transitions

When a timezone-aware expression evaluates across a DST transition:

- **Spring forward** (clock skips an hour): scheduled times that
  fall within the skipped interval MUST NOT fire. The next valid
  occurrence fires normally.
- **Fall back** (clock repeats an hour): scheduled times that fall
  within the repeated interval MUST fire exactly once, on the first
  occurrence.

### Precision

Precision is second-level. Sub-second scheduling is not supported.

### Examples

| Expression | Meaning |
|---|---|
| `*-*-* 02:00:00` | Every day at 2am (system-local). |
| `Mon *-*-* 00:00:00` | Every Monday at midnight. |
| `*-*-1,15 12:00:00` | 1st and 15th of each month at noon. |
| `*-*-~01 00:00:00` | Last day of each month at midnight. |
| `Mon..Fri *-*-* 09:00:00` | Weekdays at 9am. |
| `*-*-* *:00/15:00` | Every 15 minutes. |
| `*-*-* 02:00:00 Europe/London` | Every day at 2am London time. |

## Timer evaluation

At boot (after the service graph is loaded) and whenever timer
configuration changes, peinit MUST compute the next firing time
for every active timer trigger and arm a timerfd.

When a timerfd fires:

```
handle_timer(service, trigger):
    // Step 1: Check service state and create operation.
    match (service.type, service.state):
        (Oneshot, Active or Starting):
            set service.pending_timer = true
            // At most one pending run.

        (Simple, Active or Starting):
            log "timer fired for active Simple service, no-op"
            // No action.

        (_, Inactive or Completed or Failed):
            create_operation(Start, service, source=Timer)

    // Step 2: Record firing.
    write last-run timestamp to registry
    // (async -- peinit does not block on this write)

    // Step 3: Rearm.
    next = compute_next_occurrence(trigger.schedule, now())
    next = next + random(0, service.timer_jitter)
    arm timerfd for next
```

### Oneshot pending runs

When a Oneshot service with a pending flag transitions to Inactive
or Completed (finishes running), peinit MUST immediately create a
start operation and clear the flag. Multiple missed firings during
a single run collapse into one pending run -- there is no queue.

### Multiple timers

Multiple timer triggers on a single service are independent. Each
has its own timerfd, its own next-firing computation, and its own
last-run timestamp. Oneshot services share a single pending flag
across all triggers -- a service can only have one pending run
regardless of how many timers fired while it was active.

## Persistent timers

`TimerPersistent` (default 1) controls whether missed timer runs
are caught up after a reboot.

On boot, for each persistent timer trigger, peinit MUST:

1. Read the last-run timestamp. For services with a single timer
   trigger, the timestamp is stored as a REG_QWORD value at
   `Machine\System\Services\<name>\LastTimerRun`. For services
   with multiple timer triggers, each trigger's timestamp is
   stored as a REG_QWORD value under the subkey
   `Machine\System\Services\<name>\TimerState\`, with the value
   name set to the trigger's schedule string (e.g., the value
   name `*-*-* 02:00:00` stores the timestamp for that trigger).
2. Compute the next scheduled firing after the last-run timestamp.
3. If that time is in the past (at least one run was missed), fire
   once immediately.
4. Compute the next future occurrence normally.

Persistent catch-up is always a single run, not one per missed
occurrence. A daily timer that missed 5 days fires once on boot,
not 5 times.

Non-persistent timers (`TimerPersistent=0`) ignore history. On
boot, peinit computes the next future occurrence from now.

### Timestamp storage

Last-run timestamps are stored in the registry. Timer firings are
low-frequency, so write overhead is negligible.

The timestamp is written after the timer fires and the service
start is initiated -- not after the service completes. A service
that crashes mid-run MUST NOT re-trigger on next boot (the run was
attempted, not missed).

> [!INFORMATIVE]
> Timestamps are keyed by schedule string. If a timer's schedule is
> changed (e.g., `daily` to `*-*-* 03:00:00`), the old timestamp
> is orphaned and the new schedule has no history, causing one
> spurious persistent catch-up run. A stable trigger ID would fix
> this but is deferred -- schedule changes are rare and the worst
> case is one extra run.

## Jitter

`TimerJitter` (default 0 seconds) adds a random delay to each
timer firing. When peinit computes the next firing time, it MUST
add a uniformly random delay between 0 and TimerJitter seconds.

The jitter is recomputed on each firing -- a daily timer with
`TimerJitter=900` fires at a slightly different time between 00:00
and 00:15 each day.

Jitter is applied after the calendar expression is evaluated. A
timer MUST NOT fire before its scheduled time, only after.

## Clock behaviour

peinit MUST use `CLOCK_MONOTONIC` for timerfd arming (computing
"fire in N seconds from now") and `CLOCK_REALTIME` for last-run
timestamp storage (recording when a timer actually fired).

- **NTP forward jump:** armed timers fire at the correct monotonic
  interval. The next-occurrence computation uses realtime, so after
  a forward jump, peinit may compute that the next firing is sooner
  than expected. This is correct -- the scheduled wall-clock time
  arrived.
- **Runtime clock backward jump:** armed timers still fire at the
  monotonic interval. Last-run timestamps are NOT invalidated at
  runtime -- the run happened.
- **Boot-time clock backward jump:** if LastTimerRun is in the
  future relative to the current wall clock at boot, peinit MUST
  treat it as "unknown last run" and fire the persistent catch-up
  immediately. This only applies to the boot-time check, not
  runtime.
- **Bad RTC at boot:** if the system boots with a wildly wrong
  clock and NTP corrects it later, persistent catch-up may fire
  spuriously or not at all. This is a known edge case with no clean
  solution short of NTP-aware timer rescheduling.

> [!INFORMATIVE]
> The calendar expression parser should be heavily tested. Time
> parsing is a rich source of edge-case bugs -- month boundaries,
> leap years, last-day-of-month, DST transitions, and timezone
> database updates are all fertile ground for subtle errors.
