---
title: Retention
description: Log retention works exactly as event retention does, on the same thread, with a shorter default and its own reclamation.
---

Log retention works exactly as event retention does (§3.6), on the same
background thread, running after the event store and before the metric
store. As there, the v0.23 model is an early simplification and both
limits are enforced with the more aggressive one winning.

## Age and size

Rows older than `LogRetentionDays` (§A) are deleted from `logs` until
none remain.

If `LogRetentionMaxBytes` is non-zero and the store's logical live size
exceeds it, the oldest entries by timestamp are deleted until it is
within the limit. Logical live size is the same measure as §3.6 —
`(page_count - freelist_count) * page_size` after attempting a passive
checkpoint — and freed pages do not count.

There is no boot-boundary preference here. Event size retention prefers
to drop whole old boots because a boot is a self-contained unit of
sequence-numbered records; a log line has no such structure, so oldest
first is the whole rule.

## The default is shorter than events'

Fourteen days against the event store's thirty (§A).

Historical log data is worth less than historical audit data, and it is
usually bulkier per unit of value. The metric store's default is longer
than either at ninety days, for the opposite reason: a metric sample is
tiny and trend data is worth more the further back it goes (§5.5).

## Batching

The retention coordinator plans with a read-only connection and submits
low-priority commands to the log writer. Each writer-owned transaction
deletes at most `RetentionDeleteBatchRows`, and ingestion is rechecked
before the next command. Under urgent size pressure the writer may
append one bounded delete to a transaction already open. Retention
never takes a writer mutex or opens a second read-write connection
(§3.6).

The stall this avoids is the log ingestion thread's, and that thread is
also the one draining the socket (§4.1) — so a retention pass holding a
long write transaction would not merely delay writes, it would stop the
socket being read and lose the datagrams that arrived meanwhile.

## Reclamation

`VACUUM` is never run automatically, as everywhere. Freed pages are
recycled by later inserts and are excluded from the size measure.
