---
title: The Watchdog and Timeout Extension
description: The two notification fields a running service uses to adjust the deadlines it is held to, their caps, and where they do not apply.
---

Two notification fields let a running service adjust the deadlines it is
held to. Both are authenticated exactly as any other notification
(§10.5), and both carry microseconds.

## The watchdog

`WatchdogTimeout` sets the interval peinit expects `WATCHDOG=1` pings
at. Zero, the default, disables it. Missing a ping is a
`WatchdogTimeout` cause and takes the ordinary restart path.

A service may change the interval at runtime by sending
`WATCHDOG_USEC=<value>`:

- A value greater than zero updates the interval **and re-arms
  immediately** — the current timer is cancelled and a fresh one starts
  from the moment the message was received, rather than the new interval
  applying only from the next ping.
- A value of zero disables the watchdog entirely, equivalent to
  `WatchdogTimeout=0`.

The runtime value does not persist. On a restart the interval reverts to
the definition's `WatchdogTimeout` converted to microseconds, and if
that is zero the watchdog starts disabled whatever the previous
incarnation had set.

`WATCHDOG_USEC` is honoured only while the service is Active. A service
that sends it while still Starting — before its own `READY=1` — is
ignored and gets the definition's value.

> [!NOTE]
> Runtime watchdog updates suit a service whose phases have genuinely
> different latency. A database engine might want a tight five-second
> watchdog in normal operation and sixty seconds during a compaction
> pass. The service knows its own phases better than whoever wrote its
> definition does.

## Timeout extension

A service may ask for more time during a start, stop or reload by
sending `EXTEND_TIMEOUT_USEC=<value>`.

peinit sets the current phase's deadline to expire that many
microseconds from now. The extension **replaces** the deadline rather
than adding to it — each message sets an absolute deadline computed from
its own arrival — and may be sent repeatedly.

Because it replaces, a small value shortens the remaining time rather
than being ignored, and a value of zero sets the deadline to now.

### The caps

The extended deadline cannot exceed four times the phase's base timeout:

| Phase | Base | Ceiling |
|---|---|---|
| Starting | `StartTimeout` | `StartTimeout` × 4 |
| Stopping | `StopTimeout` | `StopTimeout` × 4 |
| Reloading | `StartTimeout` | `StartTimeout` × 4 |

A value beyond the cap is clamped, not rejected — the message succeeds
and the deadline becomes the maximum permitted. Because the cap is
anchored to when the operation started rather than to the previous
deadline, repeated messages cannot creep past it.

During shutdown an additional cap applies: the deadline cannot exceed
the time remaining in the global `ShutdownTimeout`, and where both caps
apply the stricter wins.

### Where it does not apply

A message arriving while the service is in a non-transitional state —
Active, Completed, Failed — is ignored. There is no deadline to extend.

During shutdown the extension applies only to a service whose stop wave
has already begun. A service in a later wave, or one still winding down
a start or a reload when shutdown was requested, has no shutdown
deadline recorded yet and its extension request has no effect.

> [!NOTE]
> Timeout extension is for a service doing variable-duration work in a
> transition — replaying a write-ahead log on startup, say. It sends
> periodic messages to prove it is making progress; if it stops sending,
> the last deadline fires and peinit escalates as usual. The fourfold
> cap is what stops a buggy service extending forever.
