---
title: Notification Fields
description: Every field a service may send — lifecycle, health, reporting and descriptor-store — and the ones deliberately not supported.
---

Every field a service may send. A manager MUST implement all of them. A
service MUST NOT send a recognised key with a value the field does not
define (§4.17).

## Lifecycle

| Field | Value | Meaning |
|---|---|---|
| `READY` | `1` | Startup is complete and the service is serving. |
| `RELOADING` | `1` | Configuration reload has begun. |
| `STOPPING` | `1` | Graceful shutdown has begun. |

**`READY=1`** is what a service using notification readiness sends when
it is genuinely able to serve, not when its process exists. Anything
depending on the service starts on the strength of it, so a service that
signals early declares its dependents' assumptions true before they are.

**`RELOADING=1`** opens a reload. The manager waits a bounded period
after issuing a reload for this field; a service that sends it MUST
follow with `READY=1` when the reload is complete, and the pair is what
lets the manager report the reload `confirmed` rather than `advisory`
(§4.13). A service that never sends either still reloads — it just
cannot be observed to have done so.

**`STOPPING=1`** tells the manager the service is already shutting down.
A manager that receives it MUST NOT send a further termination signal to
that service. It MUST NOT extend or reset the stop timeout: the service
still has to exit within it, and a service needing longer sends
`EXTEND_TIMEOUT_USEC`.

## Health

| Field | Value | Meaning |
|---|---|---|
| `WATCHDOG` | `1` | A keepalive. |
| `WATCHDOG_USEC` | unsigned integer | Change the expected keepalive interval, in microseconds. |
| `EXTEND_TIMEOUT_USEC` | unsigned integer | Extend the current transition's deadline, in microseconds. |

**`WATCHDOG_USEC`** with a value above zero sets the interval and MUST
re-arm the timer from the moment the message arrives, rather than
letting the new interval apply only from the next keepalive. A value of
zero MUST disable the watchdog.

The value MUST NOT persist across a restart. A restarted service gets
the interval its definition specifies.

**`EXTEND_TIMEOUT_USEC`** sets the current transition's deadline to
expire that many microseconds from the message's arrival. It
**replaces** the deadline rather than adding to it, and MAY be sent
repeatedly.

Because it replaces, a value smaller than the time remaining shortens
the deadline, and zero expires it immediately. A service MUST NOT send a
value expecting it to be treated as a floor.

The manager MUST cap the extended deadline at four times the base
timeout of the phase being extended, and MUST **clamp** rather than
reject a value beyond the cap. During a system shutdown the manager MUST
additionally cap it at the time remaining in the shutdown, and where
both apply the stricter MUST win.

A message arriving while the service is not in a transition MUST be
ignored. There is no deadline to extend.

## Reporting

| Field | Value | Meaning |
|---|---|---|
| `STATUS` | free text | A human-readable statement of what the service is doing. |
| `ERRNO` | free text | An errno-style error number. |
| `EXIT_STATUS` | free text | An exit status, informationally. |

All three MUST be authenticated like any other field and MUST be
recorded by the manager as structured events. They MUST NOT be forwarded
to a log sink as though they were the service's output — they are the
service speaking to the manager.

`STATUS` MUST additionally be retained and exposed as `status_text` in
the status shape (§4.14). `ERRNO` and `EXIT_STATUS` MUST NOT be
retained.

A service MUST NOT include a newline or carriage return in a `STATUS`
value: it would frame as two lines, the second of which is almost
certainly malformed.

## The descriptor store

| Field | Value | Meaning |
|---|---|---|
| `FDSTORE` | `1` | Store the descriptors attached to this datagram. |
| `FDNAME` | free text | The name to store or remove them under. |
| `FDSTOREREMOVE` | `1` | Remove the descriptors stored under `FDNAME`. |
| `FDPOLL` | `0` | Do not monitor the stored descriptors for error conditions. |

§4.20.

## Fields that are not supported

| Field | Why |
|---|---|
| `MAINPID` | A manager supervises the process it forked, through a kernel handle obtained at fork. There is no mechanism for redirecting supervision to another process, and there is deliberately none: a service that could nominate its own supervision target could nominate anything. |
| `BUSERROR` | Peios has no D-Bus. |

Neither is rejected distinctly. Both are simply unrecognised keys and
are ignored like any other (§4.17). A service MUST NOT rely on being
told that it sent one.
