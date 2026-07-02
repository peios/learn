---
title: Events overview
type: concept
description: How KMES works from a developer's seat — the single event path, per-CPU ring buffers, trusted metadata, and MessagePack payloads.
related:
  - peios-sdk/reference/event
  - peios-sdk/reference/msgpack
  - peios/auditing/overview
---

KMES is Peios's event system, and it is the **sole** event path on the system. Audit records, subsystem events, and your own application events all travel the same way: the kernel stamps each event with trusted metadata and writes it into a per-CPU, lock-free ring buffer, and consumers drain those rings. This section teaches both sides — producing and consuming — via [`event.h`](~peios-sdk/reference/event) and [`msgpack.h`](~peios-sdk/reference/msgpack).

## What an event is

An event has two parts:

1. **Kernel-stamped metadata** you cannot forge — a `CLOCK_REALTIME` timestamp, a per-CPU monotonic sequence number, the CPU id, an origin class, and identity GUIDs (the effective token, the true token, and the process). This is the trustworthy skeleton: when you consume an event, you *know* who emitted it and when, because the kernel wrote that, not the emitter.
2. **A payload** — a single [MessagePack](~peios-sdk/reference/msgpack) value that you define. This is your event's actual content.

The `event_type` is a short UTF-8 string you choose, like `"my.app.login"`, that names the kind of event.

## Payloads are MessagePack, and you own them

The kernel does not build or interpret payloads — it only *structurally validates* them on emit (one well-formed MessagePack value, within size and nesting limits). So userspace owns encoding and decoding, and the SDK ships a [MessagePack codec](~peios-sdk/reference/msgpack) whose validator's acceptance is matched to the kernel's check. Build a payload with the writer, and a successful `peios_mp_writer_bytes` (or `peios_mp_validate`) means the emit call will accept it.

## Per-CPU rings and lost events

Events live in **per-CPU** ring buffers — one ring per logical CPU, lock-free so producers never block on consumers. Two consequences shape how you consume:

- **You drain per CPU.** To see everything, run a reader per CPU (discover the count by attaching upward from CPU 0 until it fails).
- **Rings can lap.** If you don't drain fast enough, new events overwrite old ones you haven't read. The per-CPU `sequence` numbers are contiguous, so a **gap in the sequence means events were lost** — and the reader tracks that count for you.

## Privileges

The two sides are gated separately:

- **Emitting** requires `SeAuditPrivilege`.
- **Consuming** (attaching to a ring) requires `SeSecurityPrivilege`.

## Two ways to consume

The SDK offers a **high-level reader** that hides the entire lock-free drain — barriers, lapping recovery, lost-event accounting, buffer-resize handling, and the wait — behind a simple `next`/`wait` loop. That's what almost everyone should use. There is also a **low-level ring API** for callers who need to drive the drain inside their own event loop. Both are covered in [consuming events](~peios-sdk/events/consuming-events).

## Where to go in this section

- **[Emitting events](~peios-sdk/events/emitting-events)** — build a payload and emit, singly or in batches.
- **[Consuming events](~peios-sdk/events/consuming-events)** — drain the rings with the high-level reader (and, briefly, the low-level ring).
- **[`event.h`](~peios-sdk/reference/event)** and **[`msgpack.h`](~peios-sdk/reference/msgpack)** — the exhaustive reference.
