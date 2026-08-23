---
title: The Bootstrap Sequence
description: The seven startup phases, which either complete or fail entirely — configuration, KMES attachment, storage, sockets and the rest.
---

Startup proceeds in seven phases, and either completes or fails
entirely.

## Phase 1 — Configuration

1. Read every configuration key under `Machine\System\eventd\`. The six
   required keys are `EventStorePath`, `LogStorePath`, `MetricStorePath`,
   `QuerySocketPath`, `LogSocketPath` and `MetricSocketPath`; a missing
   or invalid one fails startup.
2. Read the optional keys and apply compiled-in defaults for those
   absent (§A).
3. Arm a persistent watch on the subtree, for runtime changes (§8.3).

## Phase 2 — KMES attachment and shard sizing

4. Discover the CPU count by calling `kmes_attach` with incrementing
   CPU identifiers from 0 until `EINVAL`. The call requires
   SeSecurityPrivilege in the effective token. Discovering no CPUs fails startup.
5. Map each per-CPU ring buffer.
6. Resolve the active shard count from `StorageShards` — the CPU count
   when it is 0, the configured value otherwise.
7. Compute the shard-to-CPU assignment (§2.3).

## Phase 3 — Storage

8. Open or create each active event shard: verify the schema version,
   open in WAL mode with `synchronous=FULL`, create tables and indexes
   if new, and quarantine on reported corruption (§3.3). Discover
   historical shards matching the naming pattern, and open those with a
   recognised schema read-only; exclude the rest from the query path.
9. Open or create the log store — schema verified, WAL,
   `synchronous=NORMAL`, quarantine on corruption (§4.3).
10. Open or create the metric store, likewise (§5.4). The series cache
    starts empty and fills on demand.
11. Open or create `eventd-meta.db`. Load the index and rollup counters
    and desired sets, load the sequence checkpoints for diagnostics
    only, and discover each shard's material indexes from its schema
    (§3.5).

## Phase 4 — The boot boundary

12. Read the current boot ID from peinit.
13. Search every readable event shard for committed rows carrying it.
14. **No rows** — the boot's first eventd start. Reset every per-CPU
    sequence tracker to 0 and record the new boot ID for subsequent
    writes.
15. **Rows exist** — a restart within the boot. Derive each CPU's resume
    point from the maximum committed `sequence` for
    `(boot_id, cpu_id)` across every readable shard; CPUs with no rows
    resume at 0 (§3.7).

## Phase 5 — Sockets

16. Create the query socket at `QuerySocketPath`. A stale pathname left
    by a crash is unlinked first if it is an `AF_UNIX` socket; if the
    path exists and is not a socket, startup fails.
17. Create the log socket at `LogSocketPath`, same rule.
18. Create the metric socket at `MetricSocketPath`, same rule.
19. Establish the Security Descriptor on all three, before any of them
    accepts or receives anything (§7.6).

The stale-socket rule distinguishes the two cases deliberately.
Unlinking a leftover socket is recovery from eventd's own crash;
unlinking a regular file at a configured path would be destroying
something that is not eventd's, and a path pointing at the wrong thing
is a configuration error worth failing on.

## Phase 6 — Threads

20. One drain thread per CPU, each beginning to read its ring buffer.
21. One writer thread per active shard.
22. The log ingestion thread.
23. The metric ingestion thread.
24. The retention thread.
25. The adaptive indexing and rollup policy thread.

## Phase 7 — Ready

26. Write and **commit** a `synthetic.startup` event recording the boot
    ID, the shard count and the per-CPU resume points (§3.2). The commit
    happens before readiness is signalled.
27. Signal readiness to peinit.

Committing before signalling is what makes the startup record
trustworthy. A readiness signal sent before the commit could be followed
by a crash that loses the record, leaving a boot in which eventd
demonstrably ran and left no trace of having started.

## Failure

If any phase fails, eventd does not signal readiness. It logs the
failure to standard error where standard error exists, and exits
non-zero. peinit's restart policy decides what happens next.

**Partial startup is not permitted.** There is no degraded mode in which
eventd runs without one of its three stores, or without KMES. It either
completes the sequence or fails.

The all-or-nothing rule is a simplification. A later revision might
allow log and metric ingestion to proceed with KMES unavailable, but
that means partial-failure state to manage in every subsequent path —
what a query against a store that was never opened does, what happens
when the missing subsystem returns — and the failure mode it protects
against is one peinit already handles by restarting.
