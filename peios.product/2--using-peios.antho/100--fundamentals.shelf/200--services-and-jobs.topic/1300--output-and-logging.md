---
title: Service output and logging
type: concept
description: peinit captures every service's stdout and stderr, buffers before eventd exists, and forwards after — best-effort logs, guaranteed audit events.
related:
  - peios/services-and-jobs/execution-environment
  - peios/services-and-jobs/jobs-and-operations
  - peios/auditing/overview
  - peios/auditing/events-and-transport
  - peios/services-and-jobs/boot-and-boot-modes
---

peinit is **not** a logging system — storage, indexing, and queries belong to [eventd](~peios/auditing/overview). But peinit holds the `stdout`/`stderr` pipes of every service at the moment it forks, so it is unavoidably in charge of *where output goes*, and it has to cope with the window early in boot before eventd even exists. This page is about that responsibility.

## Capturing output

When peinit forks a service it creates pipes for `stdout` and `stderr`, redirects the child's streams to the write ends, and keeps the read ends — monitoring them in its event loop. (The child's `stdin` is `/dev/null`; see [The execution environment](~peios/services-and-jobs/execution-environment).) It reads output **line by line** and tags each line with:

- the **service name**,
- the **stream** (stdout or stderr),
- a **timestamp**,
- the **[job](~peios/services-and-jobs/jobs-and-operations) GUID**.

The job GUID is the important one: it is what lets a later query return exactly one execution's output, never interleaved with the run before or after it. Hook output is captured too, labelled with the hook (e.g. `jellyfin/ExecStartPre[0]`), and so is health-check output — invaluable for diagnosing *why* a check failed.

## Logs are best-effort; audit events are not

This is the distinction to internalise, because it explains why some things survive a crash and others do not. peinit handles **two different streams of information** with two different guarantees:

| | Service logs | Audit events |
|---|---|---|
| What | `stdout`/`stderr` from services and hooks | Access denials, critical failures, recovery-mode entry, graph errors, job/operation lifecycle |
| Path | Forwarded to eventd's log socket | Emitted into the **KMES** kernel ring buffer |
| Guarantee | **Best-effort** — may be dropped under load | **Durable** — survive eventd restarts and reboots |
| Available from | Once eventd is up (buffered before) | The moment PKM loads — before eventd, before the registry |

Service logs are a convenience: useful, but lossy by design. **Audit events are part of the security posture** and go through [KMES](~peios/auditing/events-and-transport), which persists them in the kernel from the instant the module loads. So peinit keeps a pre-eventd *buffer* for logs but needs none for events — eventd picks events up from the ring buffer whenever it attaches, no matter how late.

## The pre-eventd buffer

Before eventd is running there is nowhere to send logs — its socket does not exist yet. peinit therefore buffers captured output in a fixed-size in-memory **pre-eventd buffer** (default 1 MB); when it fills, the oldest entries are dropped.

In practice the only services that run before eventd are `registryd`, `lpsd`, `authd`, and `eudev`. The first three are Peios-owned with controlled output; `eudev` is the real overrun risk (verbose device enumeration), and the [restart budget](~peios/services-and-jobs/supervision) naturally bounds output from a crash loop.

## Flood protection

A noisy service must never starve peinit's event loop. Several limits enforce that:

| Key (`Machine\System\Init\`) | Default | Limits |
|---|---|---|
| `MaxLogLineLength` | 8192 | Bytes per line; longer lines are truncated with a `[truncated]` marker. |
| `MaxLogBufferPerService` | 65536 | Bytes buffered per service pipe before back-pressure. |

Two mechanisms back these up:

- **A per-iteration read budget.** Each pass of the event loop reads at most a bounded number of bytes from service pipes before moving on to other events — so no single chatty service can monopolise a loop iteration.
- **Back-pressure, not dropping.** If a service writes faster than peinit reads, the kernel pipe buffer fills and the service's own `write()` calls block. This is deliberate: the service slows down. While reading the pipe, peinit does **not** drop output — the no-silent-drop guarantee covers *reading the pipe*. It is only *downstream* (the pre-eventd buffer, and eventd's datagram socket) that delivery becomes lossy.

> [!NOTE]
> Signals are never starved. In every loop iteration, child reaping (SIGCHLD) and shutdown handling take priority over all other event sources, including log reading. A flood of service output can never delay peinit noticing that a service died or that the system is shutting down.

## The eventd handoff

When eventd reaches Active, peinit switches from buffering to forwarding:

1. It begins sending to eventd's log datagram socket (path from `Machine\System\eventd\LogSocketPath`).
2. It **replays the pre-eventd buffer**, oldest first, preserving each line's timestamp and metadata. This replay is best-effort — the records are datagrams on a loss-tolerant socket and some may be dropped under load; peinit never blocks waiting to deliver them.
3. It switches to real-time forwarding — new output goes out as it arrives.
4. It clears the buffer.

From then on peinit is a pipe relay: read a line, tag it, forward it as a datagram. The log socket is **non-blocking and loss-tolerant** — if eventd cannot drain it fast enough the kernel drops further datagrams silently, because log ingestion must never exert back-pressure on the whole system through PID 1. peinit keeps no unbounded outbound buffer and never blocks on a send to eventd.

If eventd itself crashes after starting, peinit (which supervises it like any service) notices, **re-enables the pre-eventd buffer**, and repeats the handoff when eventd comes back. There is a log gap across the restart, bounded by the buffer size — but audit **events** are unaffected, because they were going to KMES the whole time and eventd resumes consuming them from the last persisted sequence.

## Console output

peinit writes its **own** operational messages to `/dev/console`:

- Phase 1 progress (mount results, registryd start),
- Phase 2 progress (service starts and failures, dependency errors),
- shutdown progress,
- recovery-mode entry,
- critical service failures.

Service `stdout`/`stderr` is **not** echoed to the console by default — the console is for peinit's status messages only. This keeps the console legible during boot and, crucially, usable in [Recovery mode](~peios/services-and-jobs/boot-and-boot-modes), where it may be the only interface an administrator has.

## Where to start

To see how the pipes are wired and what else the process inherits, read [The execution environment](~peios/services-and-jobs/execution-environment).

To follow the job GUID that tags every log line, read [Jobs and operations](~peios/services-and-jobs/jobs-and-operations).

For where the logs and events actually go — storage, indexing, and queries — read [Auditing](~peios/auditing/overview).
