---
title: Startup
---

## Dependencies

eventd requires the following subsystems to be available before it can operate:

- **KMES** (PSD-003) -- for event ingestion. KMES is available as soon as PKM is loaded.
- **LCS / loregd** (PSD-005, PSD-006) -- for registry configuration. eventd reads all its configuration from the registry.
- **KACS** (PSD-004) -- for access control. eventd uses the KACS AccessCheck API for query authorization and `kacs_open_peer_token` for caller identification.
- **peinit** (PSD-007) -- for boot ID and service lifecycle management.

eventd is a peinit-managed service. peinit starts eventd after loregd is available (eventd cannot read its configuration without the registry).

## Bootstrap sequence

eventd startup proceeds in the following order:

### Phase 1: Configuration

1. Read all configuration keys from the registry under `Machine\System\eventd\`. Required keys are `EventStorePath`, `LogStorePath`, `MetricStorePath`, `QuerySocketPath`, `LogSocketPath`, and `MetricSocketPath`. If any required key is missing or invalid, eventd MUST fail to start.
2. Read optional configuration keys (`StorageShards`, `MaxBatchSize`, `MaxBatchLatencyMs`, `LogMaxBatchSize`, `LogMaxBatchLatencyMs`, and all other tuning parameters). Apply compiled-in defaults for missing keys.
3. Arm a persistent watch on `Machine\System\eventd\` to detect configuration changes at runtime.

### Phase 2: Storage initialization

4. Open or create the event shard databases in the event store directory. For each shard: verify schema version, open in WAL mode with `synchronous=FULL`, create tables and indexes if new. Log errors for databases with unrecognised schema versions (open read-only for queries, do not write).
5. Open or create the log store database. Verify schema, open in WAL mode with `synchronous=NORMAL`.
6. Open or create the metric store database. Verify schema, open in WAL mode with `synchronous=NORMAL`. The series cache starts empty and is populated on demand as metrics arrive.
7. Open or create the `eventd-meta.db` metadata database in the event store directory. Load adaptive indexing state: read query frequency counters and desired index set. Load adaptive rollup state: read rollup counters and desired rollup set. Discover material indexes from each shard's schema.

### Phase 3: Boot boundary

8. Read the current boot ID from peinit.
9. Compare the boot ID against the most recently stored boot ID in the event shard databases.
10. If the boot ID differs (new boot): reset all per-CPU sequence trackers to 0, record the new boot ID.
11. If the boot ID matches (restart within same boot): read the last persisted sequence number per CPU from the event store, resume sequence tracking from those values.

### Phase 4: KMES attachment

12. Discover the CPU count and attach to each per-CPU ring buffer by calling `kmes_attach(cpu_id)` (PSD-003 syscall 1091) with incrementing `cpu_id` values starting from 0 until EINVAL is returned. The caller's token MUST hold SeSecurityPrivilege.
13. Map each per-CPU ring buffer.
14. Compute shard-to-CPU assignments based on the configured `StorageShards` value and the CPU count.

### Phase 5: Socket creation

15. Create the query socket at `QuerySocketPath`. If a stale socket file exists from a previous crash, unlink it before creating the new socket.
16. Create the log ingestion socket at `LogSocketPath`. Unlink stale socket files if present.
17. Create the metric ingestion socket at `MetricSocketPath`. Unlink stale socket files if present.
18. Set filesystem permissions on the log and metric sockets to allow service writes.

### Phase 6: Thread startup

19. Start one drain thread per CPU. Each drain thread begins reading from its assigned ring buffer.
20. Start one writer thread per event shard.
21. Start the log ingestion thread.
22. Start the metric ingestion thread.
23. Start the retention background thread.
24. Start the adaptive indexing/rollup background thread.

### Phase 7: Ready

25. Emit a synthetic `synthetic.startup` event recording the boot ID, shard count, and per-CPU sequence resume points.
26. Signal readiness to peinit.

## Failure during startup

If any phase fails, eventd MUST NOT signal readiness to peinit. eventd SHOULD log the failure and exit with a nonzero status. peinit's restart policy determines whether eventd is retried.

Partial startup is not permitted. eventd either completes the full bootstrap sequence and signals readiness, or it fails entirely. There is no degraded mode where eventd operates without one of its stores or without KMES attachment.

> [!INFORMATIVE]
> The "no degraded mode" rule is a v0.23 simplification. Future versions may allow eventd to operate with partial functionality (e.g., log and metric ingestion without event ingestion if KMES is unavailable). For v0.23, the all-or-nothing model is simpler and avoids complex partial-failure state management.

## Configuration changes at runtime

Configuration change notifications MUST be deferred until after the bootstrap sequence completes (phase 7). Changes that arrive during startup are queued and processed after readiness is signalled. This prevents configuration reloads from interacting with partially initialised state.

When a change is detected:

- **Tuning parameters** (batch sizes, latencies, retention periods, adaptive thresholds, query timeout): applied immediately to the running instance.
- **Socket paths**: ignored until restart. Changing a socket path requires an eventd restart.
- **Store paths**: ignored until restart. Changing a store path requires an eventd restart.
- **StorageShards**: ignored until restart.

eventd MUST emit a synthetic `synthetic.config_change` event for each configuration change applied at runtime.
