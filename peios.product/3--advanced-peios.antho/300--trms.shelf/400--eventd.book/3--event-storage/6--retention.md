---
title: Retention
description: Bounding disk growth on two axes, age and size, with both enforced — how the pass runs and how space is reclaimed.
---

Retention bounds disk growth. eventd deletes on two axes, age and size,
and enforces both — an event goes when it exceeds either threshold.

The v0.23 model is deliberately minimal, and a later one is expected to
support rules resembling queries: retain KACS events for ninety days,
synthetic events for seven, userspace-origin events for fourteen; and to
prune during ingestion rather than only in arrears. What is here is the
least that prevents unbounded growth.

## Age

Rows are deleted from `events` where `timestamp` is older than
`EventRetentionDays` (§A) from the current wall clock, until none
remain. Each shard is processed independently, and the rule covers KMES
events, synthetic events and gap records alike.

## Size

Size is measured as **logical live size**, not file size:

```text
logical_live_bytes = (page_count - freelist_count) * page_size
```

from `PRAGMA page_count`, `PRAGMA freelist_count` and
`PRAGMA page_size`, taken after attempting a passive WAL checkpoint. The
event store's total is the sum across every shard.

Pages freed by retention do not count, because they are reusable by
future inserts. Counting them would make retention chase its own tail:
each deletion would free pages that still counted against the limit,
prompting more deletion.

When `EventRetentionMaxBytes` is non-zero and the total exceeds it:

1. Identify every non-current boot ID present in the shards.
2. Order them by their newest event timestamp, oldest boot first.
3. Delete each of those boots entirely, across all shards, one boot at a
   time, until the total is within the limit or no non-current boots
   remain.
4. If still over, delete the oldest events of the **current** boot by
   timestamp, across all shards, until within the limit.

Size pressure prefers boot boundaries. Deleting a whole old boot removes
a self-contained unit — its sequence numbers, its gap records and its
startup event go together — and it preserves recent events across the
boundary, which is what an operator investigating a reboot needs. Only
when whole boots are exhausted does eventd start on the current one.

## Running it

Retention runs on a background thread of its own, never on a writer or
drain thread, using a separate read-write connection per store. It
processes the event store first, then the log store (§4.4), then the
metric store (§5.5). The interval is `RetentionCheckIntervalMinutes`
(§A).

WAL mode lets a reader run alongside a writer, but not a second writer,
so the retention thread coordinates with each shard's writer thread — a
shard-level mutex taken before writing, which the writer briefly yields
to.

Deletion is batched. Each transaction deletes at most
`RetentionDeleteBatchRows` and commits before the next, and between
batches the retention thread releases the coordination primitive and
rechecks writer pressure. A single unbatched `DELETE` over a month of
events would hold a write transaction for as long as it took, blocking
the writer thread and, behind it, the drain thread and the ring buffer.

## Reclamation

Deleting rows does not shrink a SQLite file. Freed pages are reused by
later inserts, and reclaiming filesystem space needs `VACUUM`, which
rewrites the whole database.

eventd never runs `VACUUM` automatically. Reclamation is an explicit
administrative operation.

In steady state it is not needed. Where ingestion and retention run at
comparable rates, the file settles at roughly the high-water mark of
retained data and the freed pages are recycled without further growth —
which is also why logical live size, rather than file size, is the right
thing to measure.
