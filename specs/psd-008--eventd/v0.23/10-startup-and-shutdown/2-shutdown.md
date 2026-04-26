---
title: Shutdown
---

## Graceful shutdown

When peinit signals eventd to stop, eventd MUST perform a graceful shutdown. The goal is to persist as much in-flight data as possible without blocking indefinitely.

### Shutdown sequence

1. **Stop accepting new connections.** Close the query, log, and metric ingestion sockets. Existing streaming queries are terminated with an error.
2. **Drain remaining log and metric data.** Read any pending datagrams from the log and metric socket buffers and process them. This is bounded by the socket buffer size and completes quickly.
3. **Final event drain.** Each drain thread performs one final drain cycle from its KMES ring buffer, reading all available events.
4. **Final batch commit.** Each writer thread commits its current batch immediately, regardless of batch size. The log and metric writers do the same.
5. **Persist sequence state.** Write the last persisted sequence number per CPU to the event store metadata. This enables correct sequence resumption on restart.
6. **Emit shutdown event.** Write a synthetic `synthetic.shutdown` event recording the per-CPU last persisted sequence numbers. This event is written directly to shard 0's database. If shard 0 is unavailable (corrupted or excluded during this session), the event is written to the lowest-numbered available shard. If no shard is available, the shutdown event is skipped.
7. **Close databases.** Close all SQLite connections (writer and reader connections). SQLite WAL checkpointing occurs automatically on connection close.
8. **Unmap ring buffers.** Unmap all KMES ring buffer mappings and close the per-CPU file descriptors.
9. **Exit.**

### Shutdown timeout

eventd MUST complete the shutdown sequence within a bounded time. If the sequence has not completed within the timeout, eventd MUST abort and exit immediately. The timeout is determined by peinit's service stop timeout (PSD-007).

If shutdown is aborted:

- In-flight event batches that have not been committed are lost. These events remain in the KMES ring buffers and will be available when eventd restarts (if they have not been overwritten).
- In-flight log and metric batches are lost (acceptable given log/metric loss tolerance).
- Per-CPU sequence numbers may not be persisted. On restart, eventd will detect a gap between the last persisted sequence and the current ring buffer state.

## Crash recovery

If eventd crashes (SIGSEGV, SIGKILL, OOM, or any ungraceful termination):

- **KMES ring buffers are unaffected.** KMES continues writing events regardless of consumer state. Events emitted while eventd is down accumulate in the ring buffers.
- **SQLite databases are consistent.** WAL mode guarantees that committed transactions survive a crash. Uncommitted transactions (the in-flight batch at crash time) are rolled back automatically by SQLite on the next open.
- **Sequence gap.** Events emitted between the last committed batch and the crash are not persisted. On restart, eventd detects this as a sequence gap and records it as a synthetic gap record.
- **Log and metric data in socket buffers is lost.** The kernel discards the socket receive buffer on process exit. This is acceptable given log/metric loss tolerance.

No manual recovery action is required. eventd restarts, re-attaches to KMES, resumes draining from the ring buffers, and continues normal operation. The gap between the last persisted event and the first event available in the ring buffer is recorded as a gap.

## Signal handling

eventd MUST handle the following signals:

| Signal | Behavior |
|---|---|
| SIGTERM | Initiate graceful shutdown. |
| SIGINT | Initiate graceful shutdown. |
| SIGQUIT | Initiate graceful shutdown with a diagnostic dump (implementation-defined). |
| SIGHUP | Re-read configuration from the registry (equivalent to a configuration watch notification). |

All other signals use default behavior.
