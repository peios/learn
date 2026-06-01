---
title: Timers
---

Timers are a trigger type, not a service type. A service with a
`timer:<schedule>` trigger is a regular Simple or Oneshot service
that peinit starts on a schedule. Timer semantics are defined here;
the trigger model is defined in §3.1.

## Calendar expressions

Timer schedules use systemd's OnCalendar expression format. The
grammar below is normative and self-contained: an implementation
MUST parse exactly this grammar.

```
DayOfWeek Year-Month-Day Hour:Minute:Second Timezone
```

### Fields and defaults

| Field | Form | Optional? | Default if omitted |
|---|---|---|---|
| DayOfWeek | weekday name(s) | yes | any day (`*`) |
| Date | `Year-Month-Day` | yes | `*-*-*` (any date) |
| Time | `Hour:Minute:Second` | yes | `00:00:00` |
| Second | the `:Second` of Time | yes | `:00` |
| Timezone | IANA tz name | yes | system-local time |

A time-only expression (e.g. `02:00:00`) implies date `*-*-*`. When
only `Hour:Minute` is given, the seconds component defaults to `00`.

### Component syntax

Each numeric component (year, month, day, hour, minute, second) and
the weekday accept:

- **Wildcard:** `*` matches any value.
- **List:** comma-separated values, e.g. `1,15` -- matches any
  listed value.
- **Range:** two values separated by `..`, e.g. `Mon..Fri` or
  `8..17` -- matches the inclusive range.
- **Repetition:** a value or range suffixed with `/` and a step:
  - `value/step` matches `value` and `value` plus every multiple of
    `step` (e.g. `0/15` in the minute field matches 0, 15, 30, 45).
  - `start..end/step` matches `start`, then `start`+`step`,
    `start`+2x`step`, ... up to and including `end`.

Weekdays are English names, case-insensitive, abbreviated (`Mon`)
or full (`Monday`), and accept lists and `..` ranges.

### Last day of month

A `~` may be used in place of the `-` separating Month and Day to
count the day from the **end** of the month -- `Year-Month~Day`,
where `~01` is the last day, `~02` the second-to-last, `~03` the
third-to-last, and so on. Repetition combines with `~`:
`Mon *-05~07/1` means "the last Monday in May." Thus `*-*~01` is the
last day of every month and `*-02~03` is the third-to-last day of
February.

### Special expressions

The following named shortcuts are accepted, each equivalent to the
calendar expression shown:

| Shortcut | Equivalent |
|---|---|
| `minutely` | `*-*-* *:*:00` |
| `hourly` | `*-*-* *:00:00` |
| `daily` | `*-*-* 00:00:00` |
| `weekly` | `Mon *-*-* 00:00:00` |
| `monthly` | `*-*-01 00:00:00` |
| `quarterly` | `*-01,04,07,10-01 00:00:00` |
| `semiannually` | `*-01,07-01 00:00:00` |
| `yearly` (alias `annually`) | `*-01-01 00:00:00` |

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

Precision is second-level. Unlike systemd, peinit does NOT support
sub-second fractional seconds in the seconds component -- service
scheduling has no use for finer granularity, and dropping it keeps
the parser simpler. A fractional second in an expression MUST be
rejected as a parse error.

### Examples

| Expression | Meaning |
|---|---|
| `*-*-* 02:00:00` | Every day at 2am (system-local). |
| `Mon *-*-* 00:00:00` | Every Monday at midnight. |
| `*-*-1,15 12:00:00` | 1st and 15th of each month at noon. |
| `*-*~01 00:00:00` | Last day of each month at midnight. |
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
    arm an absolute CLOCK_REALTIME timerfd for next
    // (TFD_TIMER_ABSTIME | TFD_TIMER_CANCEL_ON_SET; see Clock behaviour)
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
   `Machine\System\Services\<name>\TimerState\`. A schedule string
   contains characters (spaces, `:`, `*`) that may not be valid LCS
   value names (PSD-005), so the value name is the schedule string
   with every character outside `[A-Za-z0-9._-]` percent-encoded --
   the same injective encoding used for cgroup ids (§4.1). For
   example the schedule `*-*-* 02:00:00` is stored under the value
   name `%2A-%2A-%2A%2002%3A00%3A00`.
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

Calendar timers are **wall-clock** schedules, so peinit MUST arm
them as **absolute** `CLOCK_REALTIME` timers: `timerfd_settime` with
`TFD_TIMER_ABSTIME | TFD_TIMER_CANCEL_ON_SET`, set to the computed
next occurrence (plus jitter). `TFD_TIMER_CANCEL_ON_SET` makes the
timerfd `read()` return `ECANCELED` whenever the realtime clock is
discontinuously changed (NTP step, manual set); on `ECANCELED`
peinit MUST recompute the next occurrence against the new wall clock
and re-arm. This keeps a schedule like `*-*-* 02:00:00` anchored to
02:00 wall-clock across clock corrections.

Interval timers -- the watchdog, health checks, restart backoff,
and the Start/Stop/Reload phase timeouts -- are genuine relative
durations and MUST use `CLOCK_MONOTONIC`. They MUST NOT lurch when
the realtime clock is set: "wait 30 seconds" means 30 elapsed
seconds regardless of wall-clock adjustments.

Last-run timestamps are stored on `CLOCK_REALTIME` (recording when
a timer actually fired).

- **Realtime clock step (NTP or manual), runtime:** the armed
  absolute timer is cancelled (`ECANCELED`); peinit recomputes the
  next occurrence against the new wall clock and re-arms. A backward
  step pushes the next firing later; a forward step that crosses a
  missed occurrence fires it once (see below).
- **Suspend / resume:** an absolute `CLOCK_REALTIME` deadline that
  elapsed while suspended fires once on resume. peinit fires a
  missed occurrence once -- not once per occurrence that elapsed
  during the gap.
- **Missed wall-clock occurrence within one uptime:** fire once,
  then compute the next future occurrence normally. peinit MUST NOT
  replay every occurrence that elapsed during the gap. (This mirrors
  the persistent cross-reboot catch-up rule.)
- **Boot-time clock backward jump:** if LastTimerRun is in the
  future relative to the current wall clock at boot, peinit MUST
  treat it as "unknown last run" and fire the persistent catch-up
  immediately. This only applies to the boot-time check, not
  runtime.
- **Bad RTC at boot:** if the system boots with a wildly wrong
  clock and NTP corrects it later, persistent catch-up may fire
  spuriously or not at all. The runtime half of this is mitigated by
  `CANCEL_ON_SET` -- once NTP corrects the clock, armed calendar
  timers are cancelled and recomputed -- but the boot-time catch-up
  decision is already made by then, so this remains a known edge
  case short of NTP-aware rescheduling.

> [!INFORMATIVE]
> The calendar expression parser should be heavily tested. Time
> parsing is a rich source of edge-case bugs -- month boundaries,
> leap years, last-day-of-month, DST transitions, and timezone
> database updates are all fertile ground for subtle errors.
