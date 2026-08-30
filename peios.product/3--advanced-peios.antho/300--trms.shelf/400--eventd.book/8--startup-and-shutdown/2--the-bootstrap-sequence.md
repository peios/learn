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
2. Open and validate the three provisioned store directories without
   following symbolic links. A missing directory, unsafe component or
   descriptor that is not equivalent to the protected platform default
   fails startup (§3.3).
3. Read the optional keys and apply compiled-in defaults for those
   absent (§A).
4. Arm a persistent watch on the subtree, for runtime changes (§8.3).

## Phase 2 — KMES attachment and shard sizing

5. Query the KMES logical slot count with
   `kmes_attach(KMES_ATTACH_QUERY_SLOTS, …)`, walk every slot, skip
   `EINVAL` holes, and assign dense internal ordinals to successful
   logical CPU IDs (§2.2). The calls require SeSecurityPrivilege in the
   effective token. Discovering no buffers fails startup.
6. Map each per-CPU ring buffer.
7. Resolve the active shard count from `StorageShards` — the attached
   KMES-buffer count when it is 0, the configured value otherwise.
8. Compute the shard-to-CPU assignment (§2.3).

## Phase 3 — Storage

9. Open or create each active event shard: verify the schema version,
   open in WAL mode with `synchronous=FULL`, create tables and indexes
   if new, and quarantine on reported corruption (§3.3). Discover
   historical shards matching the naming pattern, and open those with a
   recognised schema read-only; exclude the rest from the query path.
10. Open or create `logs.db` in the log store directory — schema
    verified, WAL, `synchronous=NORMAL`, quarantine on corruption
    (§4.3).
11. Open or create `metrics.db` in the metric store directory, likewise
    (§5.4). The series cache starts empty and fills on demand.
12. Open or create `eventd-meta.db`. Load the index counters and desired
    set, load the sequence checkpoints for diagnostics only, and
    discover each shard's material indexes from its schema (§3.5).

## Phase 4 — The boot boundary

13. Read `/proc/sys/kernel/random/boot_id`, require valid UUID text, and
    convert it to PCDS GUID layout. An unavailable or malformed value
    fails startup.
14. Read and merge every committed `receipt_ranges` row for that boot
    from every readable active and historical shard, grouped by logical
    CPU ID (§2.2, §3.1).
15. Search those shards for any committed row or receipt carrying the
    boot ID. None means the boot's first successful eventd start;
    otherwise this is a restart within the boot (§3.7).
16. Initialise each drain's recovery coverage from the merged receipts.
    It begins at the ring's oldest survivor, skips covered sequences,
    re-ingests uncovered survivors, and records as gaps only sequences
    in neither source (§8.5).

## Phase 5 — Sockets

17. Create the query socket at `QuerySocketPath`. A stale pathname left
    by a crash is unlinked first if it is an `AF_UNIX` socket; if the
    path exists and is not a socket, startup fails.
18. Create the log socket at `LogSocketPath`, then replace its inherited
    descriptor with the protected deny-Service, allow-SYSTEM broker
    descriptor (§7.6).
19. Create the metric socket at `MetricSocketPath`, same rule.
20. Establish and verify the Security Descriptor on all three, before
    any of them accepts or receives anything (§7.6).

The stale-socket rule distinguishes the two cases deliberately.
Unlinking a leftover socket is recovery from eventd's own crash;
unlinking a regular file at a configured path would be destroying
something that is not eventd's, and a path pointing at the wrong thing
is a configuration error worth failing on.

## Phase 6 — Threads

21. One writer thread per active shard.
22. One drain thread per attached logical CPU, each beginning to
    reconcile and read its ring buffer.
23. The log ingestion thread.
24. The metric ingestion thread.
25. The retention coordinator thread.
26. The adaptive indexing policy thread.

## Phase 7 — Ready

27. Write and **commit** a `synthetic.startup` event recording the boot
    ID, the shard count and the per-CPU recovered coverage points
    (§3.2). The commit
    happens before readiness is signalled.
28. Signal readiness to peinit.

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
