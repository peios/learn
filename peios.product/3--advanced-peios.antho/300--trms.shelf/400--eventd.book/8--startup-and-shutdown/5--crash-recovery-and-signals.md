---
title: Crash Recovery and Signals
description: What an ungraceful termination leaves behind, the signals eventd handles, and the diagnostic dump.
---

## After a crash

An ungraceful termination — a segmentation fault, a kill, an
out-of-memory kill — leaves four things true.

**The ring buffers are unaffected.** KMES writes regardless of consumer
state, and events emitted while eventd was down accumulate there.

**The databases are consistent.** WAL mode guarantees committed
transactions survive, and SQLite rolls back the in-flight batch on the
next open.

**There may be uncovered sequences.** Events in an uncommitted batch
were not persisted, but some may still survive in KMES. On restart
eventd merges committed receipt ranges from all shards, re-ingests each
uncovered survivor, and writes a gap only for a sequence present in
neither receipts nor the ring (§2.2, §2.5).

**Socket-buffered data is gone.** The kernel discards a socket receive
queue on process exit, taking whatever logs and metrics were waiting.
Acceptable by the loss model.

No manual recovery is needed and none is offered. eventd restarts,
re-attaches, resumes draining, and records only what was truly missed.
The boot-boundary logic recognises the restart from committed rows or
receipts rather than a flag written in advance (§3.7) — which is the
point, since a crash is precisely the case where nothing was written in
advance.

## Signals

| Signal | Behaviour |
|---|---|
| `SIGTERM` | Begin graceful shutdown (§8.4). |
| `SIGINT` | Begin graceful shutdown. |
| `SIGQUIT` | Write a diagnostic dump to standard error, then begin graceful shutdown. |
| `SIGHUP` | Re-read configuration from the registry (§8.3). |

Every other signal keeps its default behaviour.

## The diagnostic dump

`SIGQUIT` writes human-readable text to standard error before step 1 of
the shutdown sequence, so that it reflects the daemon's state while it
is still running rather than while it is tearing down. It includes at
least:

- the current boot ID
- the active shard count and the readable historical shard count
- the per-CPU committed receipt coverage and highest covered sequence
- the current non-streaming and streaming query counts
- the metric series cache occupancy
- the last observed write error for each store, where one exists

The format is not a stable machine interface and its wording may change.

The set is chosen to answer the questions an operator has about a
misbehaving eventd that a query cannot: how far behind the writers are,
whether the series cache is thrashing (§5.3), whether query slots are
exhausted (§6.5), and whether a store has been failing writes quietly.
Standard error is the destination because peinit captures it, so the
dump reaches the log store by the ordinary path — and reaches standard
error directly when the log store is the thing that is broken.
