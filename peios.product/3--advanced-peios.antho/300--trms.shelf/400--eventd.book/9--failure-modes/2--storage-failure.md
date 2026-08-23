---
title: Storage Failure
description: What a full disk does to each of the three stores, and how corruption is detected and contained.
---

## Disk full

When the filesystem holding a store reaches capacity, SQLite writes
fail.

After any write failure consistent with disk-full or quota exhaustion,
eventd schedules an immediate retention run across every store whose
retention is enabled, under the ordinary bounded-batch rules (§3.6,
§4.4, §5.5). Retention is the only lever eventd has that frees space,
and waiting up to an hour for the next scheduled pass would waste the
window in which recovery is still cheap.

### The event store

A failed `INSERT` or `COMMIT` does not crash the writer thread.

The batch is lost, and it is not recoverable: those events were already
consumed from the ring buffer, so KMES no longer has them. The writer
records the per-CPU sequence ranges of the failed batch in an in-memory
**lost-batch list**, and on its next successful commit emits
`synthetic.gap` records for every accumulated range before writing new
events.

That ordering matters. Emitting the gap records first means the store
never contains events written after a loss without the record of the
loss preceding them.

The writer also logs the failure to standard error immediately —
including the CPU identifiers and sequence ranges — which peinit
captures. That is the only visibility available while the disk is still
full and the gap record cannot yet be written.

If eventd crashes before the disk recovers, the in-memory list dies with
it. Nothing is silently lost even so: on restart, resume points are
derived from committed rows, and the difference from the current ring
buffer state is detected as an ordinary restart gap (§3.7). The record
is coarser — one gap rather than several — but the loss is still
recorded.

Meanwhile events accumulate in the ring buffers. If the disk stays full
long enough, they overrun and additional loss occurs, detected by the
same mechanism (§9.1).

### The log and metric stores

A failed commit loses the batch. The writer retries on the next one.
Acceptable under the loss model, and no lost-batch accounting exists for
either — there is nothing to reconcile against, since neither has
sequence numbers.

## Corruption

Corruption from a hardware error, a filesystem bug, or an incomplete
write during a kernel crash.

**Detection at startup** is structural: eventd verifies that the
required tables and indexes exist. It does **not** run
`PRAGMA integrity_check`, which scans the entire database and costs time
proportional to its size — unacceptable for a large event store on every
boot. Corruption that leaves the schema intact, such as a single bad
page, is found later, at query or write time, when SQLite touches it.

**At startup**, when SQLite reports corruption in a required active
store, eventd quarantines the files, creates a fresh empty database at
the original path, and continues (§3.3). It logs the corruption and
emits `synthetic.storage_error` once a shard is available to hold it.

**At write time**, eventd stops writing to the affected database, emits
`synthetic.storage_error` if it can, quarantines and replaces the
database, and resumes writes to the replacement.

**At query time**, a handler encountering corruption fails the affected
query with an error. It does **not** return the rows it managed to read:
partial data from a database SQLite has declared corrupt is
indistinguishable from complete data, and silently under-reporting an
audit query is worse than failing it.

A missing or unrecognised **schema version** is not corruption. It is
not repaired and not migrated: a required store with one fails startup,
and a historical shard with one is excluded from the query path
(§3.3).

Recovering data from a quarantined file is an administrative operation.
eventd never attempts automatic repair, and the quarantined file is the
only copy of whatever it held.
