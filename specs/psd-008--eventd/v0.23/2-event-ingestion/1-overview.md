---
title: Overview
---

eventd is the primary consumer of KMES ring buffers. It reads events from the per-CPU shared memory ring buffers provided by KMES, processes them, and writes them to persistent storage.

The event ingestion pipeline has four stages:

1. **Drain** -- one thread per CPU reads events from the CPU's ring buffer using the lock-free read protocol defined in PSD-003 §5.1.
2. **Gap detection** -- the drain thread compares each event's sequence number against the last seen sequence for that CPU. Gaps indicate lost events and are recorded as synthetic gap records.
3. **Handoff** -- the drain thread passes processed events to the writer thread responsible for that CPU's storage shard.
4. **Write** -- the writer thread batches events and commits them to the shard's SQLite database. Batch sizing is adaptive, balancing throughput against power-loss resilience.

The pipeline is designed around two principles:

- **KMES ring buffers are the only buffer.** eventd does not maintain a large intermediate buffer between KMES and SQLite. Events move from the ring buffer through a small, bounded handoff directly into a database transaction. The ring buffer absorbs events that arrive during SQLite commits.
- **Linear scaling through sharding.** eventd distributes write work across multiple independent SQLite databases. Each database has its own writer thread and its own WAL. Shards share no write-path state, so throughput scales linearly with shard count.
