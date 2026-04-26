---
title: Failure Modes
---

## KMES ring buffer overrun

When events are emitted faster than eventd can drain them, the per-CPU ring buffers fill and KMES overwrites the oldest events.

- eventd detects the loss as a sequence gap on the affected CPU.
- A synthetic `synthetic.gap` record is written to the event store.
- eventd continues draining from the oldest surviving event (`tail_pos`).
- This is the most serious data loss scenario for events. Ring buffer overrun means audit events were lost irrecoverably.

Mitigations:
- Adaptive batch sizing maximises commit throughput.
- Adaptive index shedding reduces per-insert overhead under pressure.
- Configurable shard count provides linear write scaling.
- KMES ring buffer size is configurable (BufferCapacity) to increase the absorption window.

## Disk full

When the filesystem containing the event, log, or metric store reaches capacity, SQLite write operations fail.

### Event store

- SQLite returns an error on INSERT or COMMIT. The writer thread MUST NOT crash.
- The current batch is lost. Events in the failed batch were already consumed from the KMES ring buffer and cannot be recovered from KMES.
- The writer thread MUST record the per-CPU sequence ranges of events in the failed batch in an in-memory lost-batch list. On the next successful commit, the writer MUST emit synthetic `synthetic.gap` records for all accumulated lost-batch ranges before writing new events. This ensures that disk-full data loss is recorded in the event store once disk recovers.
- If eventd crashes before disk recovers, the in-memory lost-batch list is lost. On restart, the gap between the last persisted sequence and the current ring buffer position is detected as a normal restart gap (§3.5), so the loss is still recorded.
- The writer thread MUST log the commit failure to stderr immediately (peinit captures this), including the CPU IDs and sequence ranges of the lost events. This provides immediate visibility even if the gap record cannot be written yet.
- Events continue accumulating in the KMES ring buffers. If the disk remains full long enough for the ring buffers to overrun, additional event loss occurs (detected by the drain thread's normal sequence gap mechanism).
- The retention process SHOULD be triggered immediately to attempt to free space by deleting old data.

### Log store

- Log batches that fail to commit are lost. Acceptable given log loss tolerance.
- The log writer thread retries on the next batch.

### Metric store

- Metric batches that fail to commit are lost. Acceptable given metric loss tolerance.
- The metric writer thread retries on the next batch.

## SQLite corruption

If a SQLite database becomes corrupt (hardware error, filesystem bug, incomplete write due to kernel crash):

- Corruption is detected at startup by verifying that the required tables and indexes exist (structural check). eventd MUST NOT run `PRAGMA integrity_check` at startup -- it scans the entire database and is O(DB size), which is unacceptable for large event stores. Corruption that does not affect the schema structure (e.g., a single corrupt page) is detected at query or write time when SQLite encounters the corrupt page and returns an error.
- eventd MUST NOT write to a database that fails the structural check.
- A corrupt event shard database is excluded from the write path but remains available for read-only queries on the uncorrupted portions. SQLite can often read rows from uncorrupted pages.
- eventd MUST log the corruption and emit a synthetic `synthetic.storage_error` event (to a healthy shard).
- If all event shards are corrupt, eventd creates new shard databases and continues writing. Historical data is accessible only from the corrupt databases on a best-effort basis.
- If the log or metric store is corrupt, eventd creates a new database and continues. Historical data from the corrupt database is available for read-only queries on a best-effort basis.

Recovery from corruption is an administrative operation. eventd does not attempt automatic repair.

## eventd crash

If eventd crashes:

- KMES is unaffected. Events continue accumulating in ring buffers.
- SQLite databases are consistent (WAL guarantees). Uncommitted batches are rolled back.
- peinit restarts eventd per its service restart policy.
- On restart, eventd detects the gap between its last persisted sequence numbers and the current ring buffer state. The gap is recorded as a synthetic gap record.
- Log and metric data in socket buffers at crash time is lost.

No manual intervention required. See §10.2 for crash recovery details.

## Registry unavailable

If LCS / loregd becomes unavailable after eventd has started:

- eventd retains its last known configuration. Configuration changes are not applied until the registry is available again.
- Access control SD lookups fall back to the cached SDs. If the cache is cold for a particular pattern, access is denied (fail-closed).
- eventd continues operating with stale configuration indefinitely. This is a degraded state but not a failure.
- When the registry becomes available again, the watch fires and eventd re-reads its configuration.

## KACS unavailable

If KACS becomes unavailable after eventd has started:

- `kacs_open_peer_token` fails on new query connections. New queries are denied.
- `kacs_access_check` / `kacs_access_check_list` fails. Queries in progress that need a fresh access check are denied.
- Cached access check results remain valid for their query's duration.
- Event ingestion is unaffected -- the drain and write path does not use KACS.
- Log and metric ingestion are unaffected.

eventd continues ingesting data but cannot serve queries. When KACS recovers, query service resumes.

## Query timeout

If a query exceeds `QueryTimeoutMs`:

- The query is cancelled. eventd returns an error to the client.
- Read-only SQLite connections used by the query are released.
- No data loss occurs. The query simply did not complete.

Queries that scan large unindexed datasets are the primary timeout risk. The adaptive indexing system (§3.3) mitigates this over time by creating indexes for frequently queried fields.

## Log or metric socket backpressure

If the log or metric socket receive buffer is full when a sender transmits a datagram:

- The kernel drops the datagram silently. Neither the sender nor eventd is notified.
- This is by design. Senders MUST NOT be blocked by eventd's ingestion rate.
- eventd MAY track a dropped-datagram estimate (by monitoring socket statistics) but this is not normative.

## Writer thread stall during index creation

If an adaptive index build is in progress when events arrive:

- The drain threads detect rising write pressure and signal the writer thread to cancel the index build.
- The writer thread cancels the `CREATE INDEX` via `sqlite3_interrupt()` and resumes normal event writing.
- See §3.3 for the full cancellation mechanism.

## Writer thread stall during retention

If the retention process holds a write lock on a shard database:

- The shard's writer thread blocks briefly until the retention process releases the lock.
- Retention operates in small, bounded delete batches to minimise lock hold time.
- Events accumulate in the KMES ring buffer during the stall.
- Under sustained write pressure, the retention process SHOULD yield more frequently (smaller batches, longer pauses between batches).

## Power loss

On sudden power loss:

- **Event store** (`synchronous=FULL`): all committed transactions survive. The in-flight batch (not yet committed) is lost. On restart, this appears as a sequence gap.
- **Log store** (`synchronous=NORMAL`): transactions committed since the last WAL checkpoint may be lost. On restart, some recent logs may be missing. Acceptable given log loss tolerance.
- **Metric store** (`synchronous=NORMAL`): same as log store. Recent metrics may be lost.

The different durability guarantees between event and log/metric stores directly reflect the importance hierarchy: events are sacred, logs and metrics are important but not fundamental.

## Memory exhaustion

If eventd is killed by the OOM killer:

- Treated identically to an eventd crash. peinit restarts eventd.
- SQLite databases are consistent (WAL guarantees).
- KMES ring buffers are unaffected.
- To reduce OOM risk, eventd's memory usage is bounded by: the in-memory series cache (proportional to number of distinct metric time series), the adaptive indexing/rollup counters (proportional to number of distinct fields queried), and SQLite page caches (configurable per connection).
