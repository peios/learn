---
title: Power Loss
description: The failure the three stores' durability settings were chosen against, and what a restart does afterwards.
---

Sudden power loss is the failure the three stores' durability settings
were chosen against, and it is where the hierarchy the whole daemon is
built on becomes visible as three different outcomes.

| Store | Setting | What survives |
|---|---|---|
| Event | `synchronous=FULL` | Every committed transaction. |
| Log | `synchronous=NORMAL` | Transactions up to the last checkpoint. |
| Metric | `synchronous=NORMAL` | Transactions up to the last checkpoint. |

**The event store** loses only the in-flight batch — the events
accumulated since the last commit, which the adaptive batcher keeps as
small as throughput allows (§2.4). On restart this appears as an
ordinary sequence gap and is recorded as one (§3.7).

**The log and metric stores** may lose everything committed since their
last write-ahead log checkpoint, which under `synchronous=NORMAL` is the
real durability boundary rather than the commit. How much that is
depends on `WalCheckpointPages` and the write rate, and it can be
considerably more than one batch.

The difference is bought and paid for deliberately. `FULL` costs an
fsync on every commit, which at ten thousand events a batch is amortised
and at three events a batch is not — and eventd commits small batches
constantly under light load. The event store pays it because an event
may be an audit record whose absence is itself the finding. The other
two do not, because their loss is defined as acceptable and paying for
durability they do not need would slow the paths that are most likely to
be bursty.

Events are sacred; logs and metrics are important but not fundamental.
Every durability decision in this manual is that sentence applied to a
particular store.

## What restart does

Nothing manual. eventd starts, finds its databases consistent — WAL
recovery is SQLite's, and an incomplete transaction is rolled back on
open — derives its per-CPU resume points from the committed rows, and
records the difference from the ring buffer state as a gap.

The one case that differs from a crash is that events emitted *while the
machine was off* are gone from the ring buffers too, since those are
memory. A gap after a power cut therefore covers the downtime as well as
the uncommitted batch, and there is nothing anywhere that held those
events.
