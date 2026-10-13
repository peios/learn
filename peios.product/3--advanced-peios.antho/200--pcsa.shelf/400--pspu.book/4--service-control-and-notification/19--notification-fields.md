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
| `LEVEL` | free text | A currently true readiness condition. Repeated fields publish the complete set; an empty-only set retracts it. |

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

**`LEVEL`** names a condition the service currently satisfies, in the
service's own vocabulary. A service MAY repeat this field within one
datagram to publish several conditions. For example, a routed netd sends
`LEVEL=link`, `LEVEL=addressed` and `LEVEL=routed` as three lines in one
datagram.

When a datagram contains at least one `LEVEL` field, the manager MUST
atomically replace the sender's retained set with the distinct nonempty
values from all its `LEVEL` fields. Field order and duplicates MUST NOT
change the resulting set. An empty value adds no member; a datagram with
only empty `LEVEL` values MUST clear the set. A datagram without `LEVEL`
MUST leave the retained set unchanged. The entire replacement MUST be
visible before releasing dependents, including when the datagram also
contains `READY=1`.

The manager MUST discard the set whenever the service leaves a state
that satisfies dependents: these are claims made by a running process.

A level-conditioned dependency (`Requires = ["netd:routed"]`) MUST NOT
be satisfied unless the target is in a dependent-satisfying state **and**
the retained set contains the named level. Names are opaque,
case-sensitive and per-publisher; commas have no special meaning. The
manager MUST NOT assume an ordering or implication between them. A
publisher that knows several conditions hold MUST publish each one that
it promises to expose to dependents.

The value SHOULD be a single token of at most 64 printable ASCII
characters. A value outside that shape is not an error, but a dependency
condition cannot name it, so nothing can ever wait on it.

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
| `PROGRESS` | see below | How far the service has got. |
| `PROGRESS_UNIT` | `bytes`, `items` or `percent` | What `PROGRESS` counts. |
| `ERRNO` | free text | An errno-style error number. |
| `EXIT_STATUS` | free text | An exit status, informationally. |

All five MUST be authenticated like any other field and MUST be
recorded by the manager as structured events (PGSS §6), which, like
every event, are not written while the emission policy has their type
switched off (PGSS §6.9). They MUST NOT be forwarded
to a log sink as though they were the service's output — they are the
service speaking to the manager.

`STATUS`, `PROGRESS` and `PROGRESS_UNIT` MUST additionally be retained
and exposed — as `status_text` and `progress` in the status shape
(§4.14), and in a submitted job's view (§7.7). `ERRNO` and
`EXIT_STATUS` MUST NOT be retained.

### Progress

`PROGRESS` takes one of three forms, each of two unsigned decimal
integers at most, separated by `/`:

| Form | Meaning | A viewer shows |
|---|---|---|
| `N` | Counting, with no end. | A rising count. |
| `N/` | Counting towards an end that exists but is not yet known. | A rising count, and expects a bound to arrive. |
| `N/T` | `N` of `T`. | A bar. |

`T` MUST be at least 1, and `N` MUST NOT exceed `T` when `T` is given.
A value outside these forms, or violating either rule, is an
**unexpected value** under §4.17: the line is ignored and the datagram
is otherwise applied. A manager MUST NOT clamp or repair a progress
value.

The manager retains the most recent accepted value and exposes it as a
`progress` object: `current` is `N`; `total` is `T` or null; `bounded`
is true for the second and third forms and false for the first; `unit`
is the most recent accepted `PROGRESS_UNIT` or null. A `PROGRESS_UNIT`
outside its three values is an unexpected value and is ignored. Each
field is replaced only by a datagram that carries it: a `STATUS` alone
leaves `progress` as it was.

`T` MAY change from one datagram to the next — a job that rescans has
learned something — and `N` MAY fall. A viewer renders the latest
value; it MUST NOT infer motion from the difference between two.

A service that sends progress with no end in sight MUST send the
first form and not a guessed `T`. A service that has not started
counting sends nothing: absence means *no progress concept*, and a
viewer shows an indeterminate indicator.

The manager MUST bound how often a change of progress becomes an event
on its event stream, so that a sender updating a thousand times a
second cannot produce a thousand events; the retained value is the
latest regardless. The bound a Peios service manager uses is §4.A.

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
