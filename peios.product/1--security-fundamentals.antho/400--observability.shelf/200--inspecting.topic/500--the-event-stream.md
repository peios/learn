---
title: The event stream
type: reference
description: revstrm is a diagnostic probe that attaches directly to the KMES ring buffers and prints every audit event it drains. Options, output format, and caveats.
related:
  - peios/inspecting/overview
  - peios/inspecting/sessions
  - peios/auditing/events-and-transport
  - peios/auditing/overview
---

The other pages in this topic inspect *state* — what a token holds, which session a thread belongs to, what a process is authorised for. This page inspects *flow*: the live stream of audit events the kernel produces as access checks fire. State tells you what is true right now; the event stream tells you what is happening, event by event, as it happens.

The tool for reading that stream raw is **`revstrm`**. It attaches directly to the [KMES](~peios/auditing/events-and-transport) per-CPU ring buffers and prints every event it drains. It is deliberately oblivious to the rest of the audit pipeline: it knows nothing about eventd, applies no persistence, and makes no attempt at reliable delivery. It is a debugging probe for the transport layer itself.

## What revstrm is (and is not)

`revstrm` is not the normal way to look at audit events. The normal way is to query **eventd**, the userspace audit daemon that subscribes to KMES, persists events, and serves them to consumers. eventd is the durable, deployment-facing surface. `revstrm` sits *underneath* it, tapping the same kernel stream directly.

Two things make it worth having:

- **It is a diagnostic.** When events are not reaching eventd, or you suspect the kernel is not emitting what you expect, `revstrm` lets you see the raw KMES stream with no daemon in the path. It is the "is the wire live?" probe for the audit pipeline.
- **It is the reference consumer.** `revstrm` exercises the full KMES consumption protocol of [PSPK §2.4](~peios/kmes-event-stream/consuming) — one drain thread per CPU ring, the futex notification wait, generation-change re-attach, and lapping/gap detection. It is the worked example that proves the consumption path before a production consumer like eventd relies on it.

Because it taps KMES directly rather than through eventd, `revstrm` is subject to the raw transport's limits: it is its *own* KMES subscriber, it can fall behind, and when it does its ring laps and it loses events — visibly (see [Lapping and gaps](#lapping-and-gaps)). It is not a lossless audit sink and must never be relied on as one. For durable audit, that is eventd's job.

## Access requirement

Attaching to the KMES ring buffers requires **`SeSecurityPrivilege`**. Without it, the attach fails at the first ring with a clear hint rather than a silent empty stream:

```
revstrm: cannot attach to the KMES ring buffers (SeSecurityPrivilege required)
```

This is the same privilege class that gates the rest of the security-sensitive surfaces: reading the audit stream reveals every access decision on the machine, so it is not something a low-privileged process can do. An administrator (whose token holds `SeSecurityPrivilege`) can run it; an ordinary user cannot.

## Synopsis

```
revstrm [OPTION]...
```

With no options, `revstrm` **follows** the live stream: it attaches to every per-CPU ring and prints each event as it arrives, oldest surviving event first, until you interrupt it (Ctrl-C) or the output pipe closes. There is no target to name and no subscription to configure — it drains whatever the kernel is currently writing to KMES.

## Options

The option surface is small and entirely about *what to show* and *how to show it* — there is nothing to configure about the subscription itself.

| Option | Description |
|---|---|
| `-t, --type GLOB` | Only show events whose event-type string matches `GLOB`. Repeatable; an event is shown if it matches **any** supplied pattern (OR). Uses shell-glob syntax (e.g. `--type 'access-*'`). |
| `-o, --origin CLASS` | Only show events from origin `CLASS`, one of `userspace`, `kmes`, `kacs`, or `lcs` (case-insensitive; `user`/`usr` alias `userspace`). Repeatable; an event is shown if its origin matches any supplied class. |
| `-p, --pretty` | Expand the msgpack payload across multiple indented lines instead of the compact one-line form. |
| `-s, --snapshot` | Drain the events currently buffered across all rings and exit, instead of following the live stream. Single-threaded, in CPU order; there is nothing to wait for. |
| `--help` | Print usage and exit. |
| `--version` | Print version and exit. |

Long options may be abbreviated as long as the prefix is unambiguous (e.g. `--sn` for `--snapshot`).

The `--type` and `--origin` filters are applied by `revstrm` after draining, purely to reduce what is printed — they are *display* filters, not a kernel-side subscription. The kernel still writes every event into the ring, and `revstrm` still drains every event; filtered-out events are simply not printed. This matters for lapping: filtering does not reduce the drain load, so it does not make `revstrm` less likely to fall behind.

## Output format

Each event prints as a single header line (followed, under `--pretty`, by an indented payload block):

```
TIME  cpuN  #SEQUENCE  ORIGIN  event.type  payload
```

| Field | Meaning |
|---|---|
| `TIME` | UTC time-of-day with microsecond precision, `HH:MM:SS.uuuuuu`. The calendar date is dropped — a live tail cares about wall-clock time of day, not the day. |
| `cpuN` | The per-CPU ring the event was drained from. Events are sharded per CPU all the way down; `revstrm` prints the CPU rather than merging into a single ordered stream. |
| `#SEQUENCE` | The event's per-ring sequence number. Gaps in the sequence on a given CPU indicate lost events. |
| `ORIGIN` | The origin class: one of `USR`, `KMES`, `KACS`, `LCS` (or `cN` for an unrecognised class). |
| `event.type` | The event-type string (e.g. `access-audit`, `logon-session-destroyed`). |
| `payload` | The msgpack payload, rendered as described below. |

### Payload rendering

By default the payload is rendered **compactly** on the header line, truncated if long. `revstrm` decodes the msgpack and applies a couple of field-name conventions to make raw events readable:

- Keys ending in `sid` are rendered as canonical string SIDs (`S-1-5-18`); keys ending in `sids` render as an array of them.
- Keys ending in `access` are decoded into `|`-joined access-right names (e.g. `FILE_READ_DATA|FILE_READ_ATTRIBUTES`), with any unrecognised bits shown as a hex remainder so nothing is hidden.

A payload that will not decode as msgpack falls back to a hex preview rather than being dropped. With `--pretty`, the same payload is expanded into an aligned, indented block — one key per line, nested maps and arrays expanded beneath their key. Use `--pretty` when you are reading individual events closely; leave it off when tailing a busy stream.

The event schemas themselves — `access-audit`, `continuous-audit`, `privilege-use`, `logon-session-destroyed` — are documented in [Events and transport](~peios/auditing/events-and-transport). `revstrm` does not interpret them beyond the field-name conventions above; it is a stream printer, not an event analyser.

### Example

A short follow session might look like:

```
14:22:07.481923  cpu0  #10432    KACS  access-audit  {subject: {user_sid: S-1-5-21-…, integrity_level: 12288, …}, requested_access: FILE_READ_DATA|FILE_READ_ATTRIBUTES, granted_access: FILE_READ_DATA|FILE_READ_ATTRIBUTES, success: true, …}
14:22:07.492010  cpu3  #8871     KACS  privilege-use  {privilege: "SeBackupPrivilege", surviving_access: FILE_READ_DATA, success: true, …}
14:22:08.003114  cpu0  #10433    KACS  logon-session-destroyed  {session_id: 4051, user_sid: S-1-5-21-…, logon_type: 2, …}
```

## Lapping and gaps

`revstrm` is one KMES subscriber among possibly several, with its own per-CPU rings. If it cannot drain a ring fast enough — a burst of audit events, a slow terminal, a `--pretty` render on a busy stream — that ring **laps**: the kernel overwrites the oldest un-drained events with new ones. This is the flow-control behaviour of KMES, not a bug in `revstrm`.

When a ring laps, `revstrm` does not hide it. It prints a visible marker naming the CPU and the count lost:

```
--- cpu2: lost 37 event(s) (ring lapped) ---
```

A dropped event a debugger cannot see is the worst possible outcome, so lapping is always surfaced. If you see these markers, `revstrm` is not keeping up — narrowing the output with `--type`/`--origin` won't help (the drain still happens), but redirecting to a file, dropping `--pretty`, or reducing the event rate will. Sustained lapping is also a signal in its own right: the kernel is producing events faster than a single un-buffered consumer can drain them.

Gaps are also visible directly in the `#SEQUENCE` column: a jump in the per-CPU sequence number is a run of events that this subscriber never saw.

## Exit behaviour

- In **follow** mode (the default), `revstrm` runs until interrupted or until stdout closes. A downstream `head` (or any reader) closing the pipe shuts `revstrm` down cleanly — it treats the broken pipe as "nothing left to print to" and exits, rather than being killed by `SIGPIPE`. If every per-CPU ring hits a fatal error, all drain threads exit and the process ends.
- In **snapshot** mode (`--snapshot`), it drains what is currently buffered across all rings and exits immediately.

## When to use it

Use `revstrm` when you are debugging the audit *pipeline* — "are events being emitted at all?", "is eventd's problem upstream or downstream of KMES?", "what exactly is the kernel putting on the wire?". Use eventd (or whatever consumes it in your deployment) for everything else: durable audit, historical queries, and any consumption that must not lose events.

## See also

- [Inspecting security state](~peios/inspecting/overview) — the state-inspection counterparts: tokens, sessions, and processes.
- [Events and transport](~peios/auditing/events-and-transport) — the schemas of the events revstrm prints.
- [Auditing](~peios/auditing/overview) — where the events come from.
