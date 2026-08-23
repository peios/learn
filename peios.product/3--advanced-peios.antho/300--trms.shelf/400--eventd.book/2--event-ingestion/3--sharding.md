---
title: Sharding
description: Event writes distributed across up to 256 independent databases — the count, the assignment, the writer threads and the handoff.
---

## The shard count

Event writes are distributed across one to 256 independent SQLite
databases. The count comes from `StorageShards` (§A); zero means "as
many shards as there are CPUs", and is the default.

Two properties make a count perform well, and neither is enforced. A
power of two lets routing use a bitwise AND rather than a modulo. A
multiple of the CPU count distributes shards evenly across CPUs. The
default satisfies the second by construction.

## Assignment

Shard-to-CPU assignment is computed once at startup and is fixed for the
process lifetime.

For each CPU `c`, eventd assigns every shard `j` where
`j % cpu_count == c`. If that produces nothing — which happens when
there are fewer shards than CPUs — CPU `c` is instead assigned
`c % shard_count`. Every CPU ends with at least one write path.

The three cases behave differently:

| Relation | Result |
|---|---|
| shards == CPUs | one shard per CPU, the 1:1 case |
| shards < CPUs | several CPUs share a shard |
| shards > CPUs | a CPU owns several shards |

A drain thread owning several shards distributes its events round-robin,
sending each successive event to the next shard it owns.

When the counts do not divide evenly, some CPUs carry one shard more
than others, or some shards receive from one CPU more than others. The
resulting imbalance is one shard's worth of throughput, which is
negligible against the whole.

## Shards are not a query-path concept

Assignment is not persisted. A shard database accumulates events from
whatever CPUs routed to it during whatever eventd lifetimes wrote it, so
a single shard file may hold events from a different set of CPUs in
different regions of its history.

The query path therefore assumes nothing: it reads every database in the
directory, and a query filtering on `cpu_id` scans all of them (§6.4).
Sharding is a write-path optimisation that the read path pays a fan-out
for.

## Writer threads

Each shard has exactly one writer thread, and that thread is the only
writer to that database. No other thread and no other connection writes
to it, which is what makes the single-writer assumptions in §5.3 and
§3.4 safe.

Drain threads never write to SQLite. When several drain threads share a
shard they hand off concurrently, so the handoff channel is
multi-producer and single-consumer.

## The handoff channel

Each writer thread has one bounded channel through which drain threads
submit events. Its capacity does not exceed the maximum batch size
(§2.4).

When the channel is full the drain thread **stops reading from the ring
buffer** and waits. It does not drop events to relieve the pressure and
it does not grow the channel. Events accumulate in the ring buffer
instead, which is the designed path (§2.1):

```text
writer slow → channel fills → drain pauses → ring buffer absorbs
            → KMES overwrites oldest if full → gap detected on resume
```

When the writer commits and the channel has room, the drain thread
resumes immediately.

The channel is a staging area for one batch, not a second buffer. Its
bound is the batch size precisely so that it cannot become one.

## Lifecycle and reconfiguration

Shard databases are created in the event store directory on first use.
eventd never deletes or overwrites one left by a previous configuration:
starting with fewer shards than exist leaves the excess in place, and
the query path continues to read them (§3.3).

Changing `StorageShards` takes effect at the next restart. The
configuration watch notices the change and eventd defers it rather than
reassigning CPUs or creating shards while running (§8.3).

Shard count changes are expected to be rare — set once from the hardware
profile, one for a small board and a multiple of the CPU count for a
server, and then left alone. Live migration would mean rebalancing
writer threads and channels while events are in flight, for a
configuration change that happens once in a machine's life.
