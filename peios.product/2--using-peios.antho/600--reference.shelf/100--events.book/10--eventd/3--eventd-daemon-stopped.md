---
title: "eventd.daemon.stopped"
description: "The record that eventd shut down gracefully, written after it stopped reading the rings and committed everything it had read."
---

- **Event type:** `eventd.daemon.stopped`
- **Defined in:** `eventd.evman`
- **Tier:** essential
- **Gating:** none — written on every graceful shutdown
- **Cardinality:** once per graceful shutdown

The record that eventd shut down gracefully, written after it stopped
reading the rings and committed everything it had read. A crash writes
nothing, which is how a crash is told apart from a shutdown.

Replaces `synthetic.shutdown` (PEI-617).

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`store.committed.cpus`](~peios/events/field-index/fields-store#store.committed.cpus) | `uint[]` | optional | Absent when eventd could not read its record of what it had committed (PEI-1394), rather than written as zeroes. |
| [`store.committed.sequences`](~peios/events/field-index/fields-store#store.committed.sequences) | `uint[]` | optional | Present exactly when `store.committed.cpus` is. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
