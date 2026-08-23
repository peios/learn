---
title: Shutdown
description: Persisting as much in-flight data as possible without blocking indefinitely — the sequence, and the timeout that bounds it.
---

When peinit signals a stop, eventd persists as much in-flight data as it
can without blocking indefinitely.

## The sequence

1. **Stop accepting.** Unlink all three socket paths so no new client
   can reach them, and stop accepting query connections. Existing
   streaming queries are terminated with an error. The log and metric
   socket descriptors stay **open**.
2. **Drain ingestion.** Read and process the datagrams still in the log
   and metric receive queues, then close those descriptors. This is
   bounded by the queue size — four times the datagram ceiling — so it
   completes quickly.
3. **Final event drain.** Each drain thread performs one last drain
   cycle from its ring buffer.
4. **Final commit.** Every writer commits its current batch immediately,
   whatever its size. The log and metric writers do the same.
5. **Record sequence state.** Derive the per-CPU last committed
   sequence from committed rows — the same rule startup uses — and write
   it to `sequence_checkpoints` for diagnostics (§3.5).
6. **Emit the shutdown event.** Write `synthetic.shutdown` with the
   per-CPU sequences, using the daemon-wide shard assignment rule
   (§2.6). If no shard is writable, the event is skipped and the failure
   logged to standard error.
7. **Close databases.** Close every connection, writer and reader.
   SQLite checkpoints the write-ahead log automatically on close.
8. **Unmap.** Unmap every ring buffer and close the per-CPU descriptors.
9. **Exit.**

Steps 1 and 2 are deliberately split. Unlinking the pathnames stops new
senders finding the socket while the descriptors stay open, so whatever
is already queued is still readable — closing them at step 1 would
discard the queue, which is the data most recently produced and
therefore most likely to explain why the system is being stopped.

The final checkpoint in step 7 matters most for the log and metric
stores, which run `synchronous=NORMAL` and whose durability boundary is
the checkpoint rather than the commit (§4.1).

## The timeout

Shutdown is bounded by peinit's service stop timeout. If the sequence
has not finished, eventd aborts and exits immediately.

What an aborted shutdown costs:

- **Uncommitted event batches** are lost. Those events remain in the
  KMES ring buffers and are available at the next start, provided they
  have not been overwritten by then.
- **Uncommitted log and metric batches** are lost, which is acceptable
  by design.
- **The diagnostic sequence metadata** may be stale. It does not matter:
  startup derives resume points from committed rows and detects the
  difference between those rows and the ring buffer state as an ordinary
  gap (§2.5).

Every consequence is one the restart path already handles, which is why
aborting is safe rather than merely tolerable.
