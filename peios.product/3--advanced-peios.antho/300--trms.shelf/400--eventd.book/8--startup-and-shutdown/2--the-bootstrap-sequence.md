---
title: The Bootstrap Sequence
description: The seven startup phases, which either complete or fail entirely — configuration, KMES attachment, storage, sockets and the rest.
---

Startup proceeds in seven phases, and either completes or fails
entirely. [*bootstrap.startup-proceeds-through-seven-phases-in-order]

## Phase 1 — Configuration

1. Read every configuration key under `Machine\System\eventd\`.
   [*bootstrap.every-key-under-machine-system-eventd-is-read-first] The six
   required keys are `EventStorePath`, `LogStorePath`, `MetricStorePath`,
   `QuerySocketPath`, `LogSocketPath` and `MetricSocketPath`; a missing
   or invalid one fails startup.
   [*bootstrap.the-six-required-keys-are-the-three-store-paths-and-three-socket-paths]
   [*bootstrap.a-missing-or-invalid-required-key-fails-startup]
2. Open and validate the three provisioned store directories without
   following symbolic links.
   [*bootstrap.store-directories-are-opened-without-following-symbolic-links]
   A missing directory, unsafe component or
   descriptor that is not equivalent to the protected platform default
   fails startup (§3.3).
   [*bootstrap.a-missing-or-unsafe-store-directory-fails-startup]
3. Read the optional keys and apply compiled-in defaults for those
   absent (§A). [*bootstrap.absent-optional-keys-take-their-compiled-in-defaults]
4. Arm a persistent watch on the subtree, for runtime changes (§8.3).
   [*bootstrap.a-persistent-watch-is-armed-on-the-configuration-subtree]

## Phase 2 — KMES attachment and shard sizing

5. Query the KMES logical slot count with
   `kmes_attach(KMES_ATTACH_QUERY_SLOTS, …)`, walk every slot, skip
   `EINVAL` holes, and assign dense internal ordinals to successful
   logical CPU IDs (§2.2).
   [*bootstrap.every-kmes-slot-is-walked-skipping-einval-holes-and-given-a-dense-ordinal]
   The calls require SeSecurityPrivilege in the
   effective token.
   [*bootstrap.kmes-attachment-requires-sesecurityprivilege-in-the-effective-token]
   Discovering no buffers fails startup.
   [*bootstrap.discovering-no-kmes-buffers-fails-startup]
6. Map each per-CPU ring buffer.
   [*bootstrap.each-per-cpu-ring-buffer-is-mapped]
7. Resolve the active shard count from `StorageShards` — the attached
   KMES-buffer count when it is 0, the configured value otherwise.
   [*bootstrap.storageshards-zero-means-one-shard-per-attached-kmes-buffer]
8. Compute the shard-to-CPU assignment (§2.3).
   [*bootstrap.the-shard-to-cpu-assignment-is-computed-after-the-shard-count]

## Phase 3 — Storage

9. Open or create each active event shard: verify the schema version,
   open in WAL mode with `synchronous=FULL`, create tables and indexes
   if new, and quarantine on reported corruption (§3.3).
   [*bootstrap.each-active-event-shard-is-opened-or-created-in-wal-mode-with-synchronous-full]
   Discover
   historical shards matching the naming pattern, and open those with a
   recognised schema read-only; exclude the rest from the query path.
   [*bootstrap.historical-shards-with-a-recognised-schema-open-read-only-and-the-rest-are-excluded]
10. Open or create `logs.db` in the log store directory — schema
    verified, WAL, `synchronous=NORMAL`, quarantine on corruption
    (§4.3).
    [*bootstrap.logs-db-is-opened-or-created-in-wal-mode-with-synchronous-normal]
11. Open or create `metrics.db` in the metric store directory, likewise
    (§5.4).
    [*bootstrap.metrics-db-is-opened-or-created-in-wal-mode-with-synchronous-normal]
    The series cache starts empty and fills on demand.
    [*bootstrap.the-series-cache-starts-empty]
12. Open or create `eventd-meta.db`.
    [*bootstrap.eventd-meta-db-is-opened-or-created] Load the index counters and desired
    set, load the sequence checkpoints for diagnostics only, and
    discover each shard's material indexes from its schema (§3.5).
    [*bootstrap.sequence-checkpoints-are-loaded-for-diagnostics-only]
    [*bootstrap.each-shards-material-indexes-are-discovered-from-its-schema]

## Phase 4 — The boot boundary

13. Read `/proc/sys/kernel/random/boot_id`, require valid UUID text, and
    convert it to PCDS GUID layout.
    [*bootstrap.the-boot-id-is-read-and-converted-to-pcds-guid-layout]
    An unavailable or malformed value
    fails startup.
    [*bootstrap.an-unavailable-or-malformed-boot-id-fails-startup]
14. Read and merge every committed `receipt_ranges` row for that boot
    from every readable active and historical shard, grouped by logical
    CPU ID (§2.2, §3.1).
    [*bootstrap.receipt-ranges-for-the-boot-are-merged-from-every-readable-shard-by-cpu]
15. Search those shards for any committed row or receipt carrying the
    boot ID. None means the boot's first successful eventd start;
    otherwise this is a restart within the boot (§3.7).
    [*bootstrap.a-boot-id-with-no-committed-row-or-receipt-marks-the-boots-first-start]
16. Initialise each drain's recovery coverage from the merged receipts.
    It begins at the ring's oldest survivor, skips covered sequences,
    re-ingests uncovered survivors, and records as gaps only sequences
    in neither source (§8.5).
    [*bootstrap.each-drains-recovery-coverage-is-initialised-from-the-merged-receipts]

## Phase 5 — Sockets

17. Create the query socket at `QuerySocketPath`.
    [*bootstrap.the-query-socket-is-created-at-querysocketpath] A stale pathname left
    by a crash is unlinked first if it is an `AF_UNIX` socket; if the
    path exists and is not a socket, startup fails.
    [*bootstrap.a-stale-socket-at-a-socket-path-is-unlinked-first]
    [*bootstrap.a-non-socket-at-a-socket-path-fails-startup]
18. Create the log socket at `LogSocketPath`, then replace its inherited
    descriptor with the protected deny-Service, allow-SYSTEM broker
    descriptor (§7.6).
    [*bootstrap.the-log-socket-gets-the-deny-service-allow-system-broker-descriptor]
19. Create the metric socket at `MetricSocketPath`, same rule.
    [*bootstrap.the-metric-socket-gets-the-deny-service-allow-system-broker-descriptor]
20. Establish and verify the Security Descriptor on all three, before
    any of them accepts or receives anything (§7.6).
    [*bootstrap.socket-descriptors-are-verified-before-any-socket-accepts-or-receives]

The stale-socket rule distinguishes the two cases deliberately.
Unlinking a leftover socket is recovery from eventd's own crash;
unlinking a regular file at a configured path would be destroying
something that is not eventd's, and a path pointing at the wrong thing
is a configuration error worth failing on.

## Phase 6 — Threads

21. One writer thread per active shard.
    [*bootstrap.one-writer-thread-is-started-per-active-shard]
22. One drain thread per attached logical CPU, each beginning to
    reconcile and read its ring buffer.
    [*bootstrap.one-drain-thread-is-started-per-attached-logical-cpu]
23. The log ingestion thread.
    [*bootstrap.one-log-ingestion-thread-is-started]
24. The metric ingestion thread.
    [*bootstrap.one-metric-ingestion-thread-is-started]
25. The retention coordinator thread.
    [*bootstrap.one-retention-coordinator-thread-is-started]
26. The adaptive indexing policy thread.
    [*bootstrap.one-adaptive-indexing-policy-thread-is-started]

## Phase 7 — Ready

27. Write and **commit** a `synthetic.startup` event recording the boot
    ID, the shard count and the per-CPU recovered coverage points
    (§3.2).
    [*bootstrap.a-synthetic-startup-event-records-boot-id-shard-count-and-per-cpu-coverage]
    The commit
    happens before readiness is signalled.
    [*bootstrap.the-startup-event-is-committed-before-readiness-is-signalled]
28. Signal readiness to peinit.
    [*bootstrap.readiness-is-signalled-to-peinit-last]

Committing before signalling is what makes the startup record
trustworthy. A readiness signal sent before the commit could be followed
by a crash that loses the record, leaving a boot in which eventd
demonstrably ran and left no trace of having started.

## Failure

If any phase fails, eventd does not signal readiness.
[*bootstrap.a-failed-phase-means-readiness-is-never-signalled] It logs the
failure to standard error where standard error exists, and exits
non-zero. [*bootstrap.a-startup-failure-is-logged-to-stderr-and-exits-non-zero]
peinit's restart policy decides what happens next.

**Partial startup is not permitted.** There is no degraded mode in which
eventd runs without one of its three stores, or without KMES. It either
completes the sequence or fails.
[*bootstrap.there-is-no-degraded-mode-without-a-store-or-kmes]

The all-or-nothing rule is a simplification. A later revision might
allow log and metric ingestion to proceed with KMES unavailable, but
that means partial-failure state to manage in every subsequent path —
what a query against a store that was never opened does, what happens
when the missing subsystem returns — and the failure mode it protects
against is one peinit already handles by restarting.
