---
title: Configuration at Runtime
description: Which settings apply immediately, which wait for a restart, which do neither, and what SIGHUP does.
---

eventd watches `Machine\System\eventd\` and reacts to changes without
restarting — for the settings that can be changed that way.
[*runtime.eventd-watches-its-configuration-subtree-and-applies-changes-without-restarting]

Notifications arriving **during** startup are queued and processed after
readiness is signalled (§8.2).
[*runtime.notifications-arriving-during-startup-are-processed-after-readiness] Applying a configuration reload to
half-initialised state would mean every phase having to tolerate its
inputs changing underneath it.

## What applies immediately

Tuning parameters: batch sizes and latencies for all three writers,
retention periods and the delete batch size, adaptive index thresholds
and windows, the WAL checkpoint threshold, the query request and
response sizes, the query timeout, the cross-type window and lookback
limit, and the query and streaming concurrency limits.
[*runtime.tuning-parameters-apply-immediately]

A live `MaxBatchSize` change is an atomic update to the event writers'
next commit threshold.
[*runtime.a-live-maxbatchsize-change-atomically-updates-the-next-commit-threshold]
It does not resize, replace or drain their
startup-fixed handoff channels (§2.3).
[*runtime.a-live-maxbatchsize-change-leaves-the-handoff-channels-untouched]
The log and metric batch settings
likewise affect only subsequent transaction thresholds.
[*runtime.log-and-metric-batch-changes-affect-only-subsequent-transactions]

## What waits for a restart

| Change | Why |
|---|---|
| Socket paths | The sockets are bound and clients are connected to them. [*runtime.a-socket-path-change-waits-for-a-restart] |
| Store paths | The databases are open, and moving a store is a data migration, not a setting. [*runtime.a-store-path-change-waits-for-a-restart] |
| `StorageShards` | Shard-to-CPU assignment, writer threads and handoff channels are all built from it at startup (§2.3). [*runtime.a-storageshards-change-waits-for-a-restart] |

The watch notices these changes and eventd defers them rather than
attempting a live migration.
[*runtime.restart-only-changes-are-deferred-not-migrated-live] Shard count changes in particular are
expected once in a machine's life, and rebalancing writer threads while
events are in flight is a large mechanism for a rare event.

## What is neither

Security Descriptors under `Security\` are not configuration in this
sense. The registry watch invalidates the descriptor cache and the next
query resolves afresh (§7.5), so a grant or revocation takes effect
immediately without anything being "applied".
[*runtime.a-security-descriptor-change-takes-effect-on-the-next-query]

## Recording it

eventd emits a `synthetic.config_change` event for every change applied
at runtime, carrying the key name and the old and new values rendered
deterministically (§3.2).
[*runtime.every-applied-change-emits-a-config-change-event-with-key-and-old-and-new-values]

Invalid values are ignored and the previous value is retained — an
administrator who types a batch size outside its range does not get a
daemon that stops working, and the retained value is the one already in
use rather than the compiled-in default.
[*runtime.an-invalid-value-is-ignored-and-the-value-in-use-is-kept] Unknown keys in the subtree are
ignored entirely. [*runtime.unknown-keys-are-ignored]

## SIGHUP

`SIGHUP` re-reads the configuration, equivalent to a watch notification
(§8.5). [*runtime.sighup-re-reads-configuration-like-a-watch-notification]
It exists for the case where the watch itself is not delivering
— a registry outage, or a watch that failed and has not re-armed
(§9.3) — and gives an administrator a way to force the read rather than
restarting the daemon.
