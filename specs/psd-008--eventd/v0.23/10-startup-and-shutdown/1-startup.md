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

### Phase 2: KMES attachment and shard sizing

4. Discover the CPU count and attach to each per-CPU ring buffer by calling
   `kmes_attach(cpu_id)` (PSD-003 syscall 1091) with incrementing `cpu_id`
   values starting from 0 until EINVAL is returned. The caller's token MUST
   hold SeSecurityPrivilege. If no CPUs are discovered, eventd MUST fail to
   start.
5. Map each per-CPU ring buffer.
6. Resolve the active event shard count from `StorageShards`: if
   `StorageShards` is 0, the active shard count is the discovered CPU count;
   otherwise it is the configured value.
7. Compute shard-to-CPU assignments from the active shard count and the CPU
   count.

### Phase 3: Storage initialization

8. Open or create the event shard databases in the event store directory. For
   each active shard: verify schema version, open in WAL mode with
   `synchronous=FULL`, create tables and indexes if new, and apply the
   corruption quarantine rules in §3.2 when SQLite reports corruption.
   Discover historical shard databases that match the shard naming pattern but
   are not active in the current configuration; open them read-only when they
   have a recognised schema and pass structural verification. Historical shard
   databases with unrecognised schemas are excluded from the query path as
   defined in §3.2.
9. Open or create the log store database. Verify schema, open in WAL mode with
   `synchronous=NORMAL`, and apply the corruption quarantine rules in §5.2 when
   SQLite reports corruption.
10. Open or create the metric store database. Verify schema, open in WAL mode
    with `synchronous=NORMAL`, and apply the corruption quarantine rules in §7.2
    when SQLite reports corruption. The series cache starts empty and is
    populated on demand as metrics arrive.
11. Open or create the `eventd-meta.db` metadata database in the event store directory. Load adaptive indexing state: read query frequency counters and desired index set. Load adaptive rollup state: read rollup counters and desired rollup set. Load sequence checkpoints for diagnostics only. Discover material indexes from each shard's schema.

### Phase 4: Boot boundary

12. Read the current boot ID from peinit.
13. Search all readable event shard databases for committed rows with the current boot ID.
14. If no committed rows exist for the current boot ID (first eventd start for this boot): reset all per-CPU sequence trackers to 0, record the new boot ID for subsequent writes.
15. If committed rows exist for the current boot ID (restart within same boot): derive the last committed sequence number per CPU from the maximum committed `sequence` value for that (`boot_id`, `cpu_id`) across all readable event shard databases. Resume sequence tracking from those values; CPUs with no committed rows for this boot resume from 0.

### Phase 5: Socket creation

16. Create the query socket at `QuerySocketPath`. If a stale socket pathname
    exists from a previous crash and is an `AF_UNIX` socket, unlink it before
    creating the new socket. If the path exists and is not a socket, fail
    startup.
17. Create the log ingestion socket at `LogSocketPath`, applying the same stale
    socket handling rule.
18. Create the metric ingestion socket at `MetricSocketPath`, applying the same
    stale socket handling rule.
19. Set filesystem permissions on all three socket pathnames as defined by their
    transport sections.

### Phase 6: Thread startup

20. Start one drain thread per CPU. Each drain thread begins reading from its assigned ring buffer.
21. Start one writer thread per active event shard.
22. Start the log ingestion thread.
23. Start the metric ingestion thread.
24. Start the retention background thread.
25. Start the adaptive indexing/rollup background thread.

### Phase 7: Ready

26. Write and commit a synthetic `synthetic.startup` event recording the boot ID,
    shard count, and per-CPU sequence resume points. The event MUST be committed
    before readiness is signalled.
27. Signal readiness to peinit.

## Failure during startup

If any phase fails, eventd MUST NOT signal readiness to peinit. eventd MUST log
the failure to stderr if stderr is available and MUST exit with a nonzero status.
peinit's restart policy determines whether eventd is retried.

Partial startup is not permitted. eventd either completes the full bootstrap sequence and signals readiness, or it fails entirely. There is no degraded mode where eventd operates without one of its stores or without KMES attachment.

> [!INFORMATIVE]
> The "no degraded mode" rule is a v0.23 simplification. Future versions may allow eventd to operate with partial functionality (e.g., log and metric ingestion without event ingestion if KMES is unavailable). For v0.23, the all-or-nothing model is simpler and avoids complex partial-failure state management.

## Configuration changes at runtime

Configuration change notifications MUST be deferred until after the bootstrap sequence completes (phase 7). Changes that arrive during startup are queued and processed after readiness is signalled. This prevents configuration reloads from interacting with partially initialised state.

When a change is detected:

- **Tuning parameters** (batch sizes, latencies, retention periods, adaptive
  index and rollup thresholds, adaptive scalar rollup window, WAL checkpoint
  threshold, query timeout, cross-type window, and streaming/query limits):
  applied immediately to the running instance.
- **Socket paths**: ignored until restart. Changing a socket path requires an eventd restart.
- **Store paths**: ignored until restart. Changing a store path requires an eventd restart.
- **StorageShards**: ignored until restart.

eventd MUST emit a synthetic `synthetic.config_change` event for each configuration change applied at runtime.
