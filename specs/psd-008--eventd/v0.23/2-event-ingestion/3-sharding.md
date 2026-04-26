---
title: Storage Sharding
---

## Shard model

eventd distributes event writes across one or more independent SQLite databases called shards. Each shard is a self-contained database with its own file, WAL, and writer thread. Shards share no write-path state.

The number of shards is configured via the `StorageShards` registry key under `Machine\System\eventd\`. The valid range is 1 to 256. A value of 0 means the shard count equals the CPU count (as reported by `kmes_attach`). The default is 0.

> [!INFORMATIVE]
> For best performance, the shard count should be a multiple of both the CPU count and 2. A shard count that is a power of two enables the implementation to use bitwise AND instead of modulo for event routing. A shard count that is a multiple of the CPU count ensures even distribution of shards across CPUs.

## Shard-to-CPU assignment

Each shard is assigned to exactly one drain thread (and thus one CPU) at startup. The assignment is static for the lifetime of the eventd process.

The assignment maps shard `j` to CPU `j % cpu_count`. When the shard count equals the CPU count, each CPU has exactly one shard (the 1:1 case). When the shard count is less than the CPU count, multiple CPUs share a shard. When the shard count exceeds the CPU count, a CPU is assigned multiple shards and round-robins events across them.

When a drain thread is assigned multiple shards, it distributes events across its shards using round-robin assignment. Each event is routed to the next shard in sequence.

When the shard count does not divide evenly by the CPU count, some CPUs are assigned one more shard than others. The resulting write throughput imbalance is proportional to one shard's worth of throughput and is negligible in practice.

The shard-to-CPU assignment is not persistent across restarts. A shard database may contain events from different sets of CPUs across different eventd lifetimes. Shards are a write-path optimisation only -- the query path MUST NOT assume any relationship between a shard and a specific CPU. Queries that filter by CPU ID MUST scan all shards.

## Writer threads

eventd MUST create one writer thread per shard. The writer thread is the sole writer to its shard's database. No other thread or connection writes to that database.

When multiple drain threads are assigned to the same shard (shard count < CPU count), they hand off events to the shard's writer thread concurrently. The handoff channel MUST support multiple concurrent producers (drain threads) and a single consumer (the writer thread). When a drain thread is assigned multiple shards (shard count > CPU count), it hands off events to the appropriate writer thread based on the round-robin assignment. The drain threads MUST NOT write to SQLite directly.

## Handoff mechanism

Each writer thread has a bounded handoff channel through which drain threads submit events. The channel capacity MUST NOT exceed `MaxBatchSize` events. The channel is the only buffer between the drain thread and the writer thread.

When the channel is full, the drain thread MUST stop reading from the KMES ring buffer and wait for the writer thread to drain the channel. The drain thread MUST NOT drop events to relieve backpressure. While the drain thread is paused, new events accumulate in the KMES ring buffer -- this is the designed backpressure path. If the ring buffer fills during the pause, KMES overwrites the oldest events, and the drain thread detects this as a sequence gap when it resumes reading.

This preserves the invariant that KMES ring buffers are the only event buffer. The handoff channel is a staging area for the current batch, not a secondary buffer. Backpressure propagates: writer thread slow → channel fills → drain thread pauses → ring buffer absorbs → KMES overwrites oldest if full → gap detected on resume.

When the writer thread commits a batch and the channel has capacity again, the drain thread resumes reading from the ring buffer immediately.

## Shard lifecycle

Shard databases are created in the event store directory on first use. eventd MUST NOT delete or overwrite existing shard databases from previous configurations. If eventd starts with a different shard count than the previous run, the previously written databases remain in the directory and are available to the query path.

Shard database filenames MUST encode sufficient information to identify the shard and distinguish active shards from historical ones. The naming convention is defined in the storage chapter.

## Reconfiguration

Changing the `StorageShards` value requires an eventd restart to take effect. eventd MUST NOT dynamically reassign CPUs to shards or create new shards while running.

> [!INFORMATIVE]
> Shard count changes are expected to be rare -- typically set once based on hardware profile (1 for a Raspberry Pi, CPU count or a multiple of CPU count for a server) and left unchanged. The registry watch mechanism detects the change, but eventd defers application to the next restart rather than attempting a live migration.
