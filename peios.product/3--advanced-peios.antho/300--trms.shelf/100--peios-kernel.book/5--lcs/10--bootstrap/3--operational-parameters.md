---
title: Operational Parameters
description: The nineteen parameters LCS reads from the registry, how they are validated, and what hot-swapping one does to in-flight operations.
---

LCS reads nineteen parameters from `Machine\System\Registry\`. [*param.nineteen-under-registry-key]

All are `REG_DWORD`. [*param.all-are-reg-dword] Each has a compiled-in default and a valid
range, and LCS runs on the defaults until the registry says otherwise.

| Value | Default | Range | Bounds |
|---|---:|---|---|
| `RequestTimeoutMs` | 30000 | 1000–600000 | A source round trip (§5.8.3). [*param.request-timeout-ms] |
| `TransactionTimeoutMs` | 30000 | 1000–600000 | The lifetime of an open transaction (§5.7.1). [*param.transaction-timeout-ms] |
| `NotificationQueueSize` | 256 | 16–65536 | Queued events per watcher before overflow (§5.6.4). [*param.notification-queue-size] |
| `SymlinkDepthLimit` | 16 | 1–64 | Symlink resolution depth (§5.2.4). [*param.symlink-depth-limit] |
| `MaxValueSize` | 1048576 | 4096–67108864 | One value's data, in bytes. [*param.max-value-size] |
| `MaxKeyDepth` | 512 | 32–4096 | Key hierarchy nesting. [*param.max-key-depth] |
| `MaxPathComponentLength` | 255 | 64–1024 | One key, value or layer name, in UTF-8 bytes. [*param.max-path-component-length] |
| `MaxTotalPathLength` | 16383 | 1024–65535 | A whole path, in UTF-8 bytes. [*param.max-total-path-length] |
| `MaxLayersPerValue` | 128 | 1–1024 | Layers writing to one `(key, value name)` (§5.3.1). [*param.max-layers-per-value] |
| `MaxBoundTransactionsPerSource` | 16 | 1–256 | Concurrently bound transactions per source (§5.7.1). [*param.max-bound-transactions-per-source] |
| `MaxReadOnlyTransactionsPerSource` | 16 | 1–256 | Concurrent backup snapshots per source (§5.9.2). [*param.max-read-only-transactions-per-source] |
| `MaxTotalLayers` | 1024 | 16–65536 | Distinct layers in the in-memory table (§5.3.1). [*param.max-total-layers] |
| `MaxRegisteredSources` | 32 | 1–256 | Concurrently registered sources. [*param.max-registered-sources] |
| `MaxHivesPerSource` | 64 | 1–1024 | Hives one source may register. [*param.max-hives-per-source] |
| `MaxConcurrentRSIRequests` | 256 | 8–4096 | In-flight RSI requests per source (§5.8.3). [*param.max-concurrent-rsi-requests] |
| `MaxScopeGUIDsPerToken` | 8 | 1–256 | Private hive scope GUIDs on a token (§5.2.2). [*param.max-scope-guids-per-token] |
| `MaxPrivateLayersPerToken` | 16 | 1–256 | Private layer names on a token (§5.3.5). [*param.max-private-layers-per-token] |
| `MaxSubtreeWatchDepth` | 0 | 0–4096 | Subtree watch depth; 0 is unlimited (§5.6.3). [*param.max-subtree-watch-depth] |
| `MaxTransactionWatchEventBurst` | 4096 | 256–65536 | Watch events per watcher from one commit (§5.6.3). [*param.max-transaction-watch-event-burst] |

Unknown values under this key are ignored. [*param.unknown-values-ignored] There are exactly
nineteen parameters and no undocumented ones; a separate set under
`Machine\System\KMES\` belongs to KMES.

Two limits are not among them. The **transaction mutation log** is
capped at 4096 entries by a compile-time constant (§5.7.2), and hard
ceilings on total path length and key depth exist independently of
configuration — set equal to the range maxima above, so they never
conflict. [*param.hard-ceilings-match-range-maxima]

## Where a configured value does not fully bind

Three of the nineteen do not do everything their range suggests.

`MaxTotalLayers` may be configured up to 65536, but the in-memory layer
table is a fixed array sized at compile time for 1023 dynamic layers
plus the base layer. A value above 1024 validates and publishes, and
then layer creation fails `ENOSPC` at 1023 regardless. Values below
1024 bind correctly.

`MaxPrivateLayersPerToken` is described as an attachment-time limit but
is not enforced at attachment. KACS applies its own hard cap of 256 and
LCS applies the configured value later, at use, with `E2BIG` (§5.3.5).
`MaxScopeGUIDsPerToken` behaves the same way.

`SymlinkDepthLimit` is honoured on most of the walk but two call sites
use the compiled-in default of 16 instead of the configured value.

## Validation

A value is checked against its range when it is read.

- **Valid** — hot-swapped into the in-memory configuration and used by
  new operations. [*param.validation.valid-is-hot-swapped]
- **Invalid** — out of range, the wrong type, or missing — the value is
  **ignored** and the previously active one is kept: the compiled-in
  default or the last known-good. [*param.validation.invalid-is-ignored-previous-kept]
  An `LCS_SELF_CONFIG_INVALID` audit event is emitted naming the
  parameter, what was wrong, and the value being retained (§5.4.4).

**Values are never clamped or silently corrected.** [*param.validation.never-clamped] There is no
`min`/`max` on any configuration path. A write to the registry
succeeds, because the source does not enforce kernel semantics, and LCS
simply refuses to use it. The registry shows what was written; the
audit log shows what LCS is running on.

Because "missing" is invalid, a first boot before seed restore emits
nineteen of these events per refresh.

## Hot-swap and in-flight operations

Configuration is published as a whole structure under a seqlock, and a
reader takes a complete copy of it. [*param.hot-swap.published-as-one-structure]

A syscall entry point snapshots it once and threads that snapshot
through the operation, so in-flight work uses the values that were
current when it started and new work uses the updated ones. [*param.hot-swap.syscall-snapshots-once]

That is the rule, and mostly the practice. Some deeper paths take a
second snapshot part-way through, and a few call sites read a single
live value rather than a snapshot — `reg_begin_transaction`'s timeout,
the bound-transaction cap, and the in-flight request cap among them.
For those, a hot-swap can be observed mid-operation. [*param.hot-swap.some-call-sites-read-live-values]

## Security

`Machine\System\Registry\` inherits the `Machine` hive root descriptor
— SYSTEM and Administrators with `KEY_ALL_ACCESS`, Authenticated Users
with `KEY_READ` — so an unprivileged process cannot change any of
this. [*param.security.unprivileged-cannot-change]

Domain policy at a higher-precedence layer defends against a
compromised local administrator, which is the reason `SeTcbPrivilege`
guards precedence above 0 (§5.3.4).
