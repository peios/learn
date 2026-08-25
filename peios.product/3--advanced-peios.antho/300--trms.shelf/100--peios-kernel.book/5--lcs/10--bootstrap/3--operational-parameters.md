---
title: Operational Parameters
description: The nineteen parameters LCS reads from the registry, how they are validated, and what hot-swapping one does to in-flight operations.
---

LCS reads nineteen parameters from `Machine\System\Registry\`. All are
`REG_DWORD`. Each has a compiled-in default and a valid range, and LCS
runs on the defaults until the registry says otherwise.

| Value | Default | Range | Bounds |
|---|---:|---|---|
| `RequestTimeoutMs` | 30000 | 1000–600000 | A source round trip (§5.8.3). |
| `TransactionTimeoutMs` | 30000 | 1000–600000 | The lifetime of an open transaction (§5.7.1). |
| `NotificationQueueSize` | 256 | 16–65536 | Queued events per watcher before overflow (§5.6.4). |
| `SymlinkDepthLimit` | 16 | 1–64 | Symlink resolution depth (§5.2.4). |
| `MaxValueSize` | 1048576 | 4096–67108864 | One value's data, in bytes. |
| `MaxKeyDepth` | 512 | 32–4096 | Key hierarchy nesting. |
| `MaxPathComponentLength` | 255 | 64–1024 | One key, value or layer name, in UTF-8 bytes. |
| `MaxTotalPathLength` | 16383 | 1024–65535 | A whole path, in UTF-8 bytes. |
| `MaxLayersPerValue` | 128 | 1–1024 | Layers writing to one `(key, value name)` (§5.3.1). |
| `MaxBoundTransactionsPerSource` | 16 | 1–256 | Concurrently bound transactions per source (§5.7.1). |
| `MaxReadOnlyTransactionsPerSource` | 16 | 1–256 | Concurrent backup snapshots per source (§5.9.2). |
| `MaxTotalLayers` | 1024 | 16–65536 | Distinct layers in the in-memory table (§5.3.1). |
| `MaxRegisteredSources` | 32 | 1–256 | Concurrently registered sources. |
| `MaxHivesPerSource` | 64 | 1–1024 | Hives one source may register. |
| `MaxConcurrentRSIRequests` | 256 | 8–4096 | In-flight RSI requests per source (§5.8.3). |
| `MaxScopeGUIDsPerToken` | 8 | 1–256 | Private hive scope GUIDs on a token (§5.2.2). |
| `MaxPrivateLayersPerToken` | 16 | 1–256 | Private layer names on a token (§5.3.5). |
| `MaxSubtreeWatchDepth` | 0 | 0–4096 | Subtree watch depth; 0 is unlimited (§5.6.3). |
| `MaxTransactionWatchEventBurst` | 4096 | 256–65536 | Watch events per watcher from one commit (§5.6.3). |

Unknown values under this key are ignored. There are exactly nineteen
parameters and no undocumented ones; a separate set under
`Machine\System\KMES\` belongs to KMES.

Two limits are not among them. The **transaction mutation log** is
capped at 4096 entries by a compile-time constant (§5.7.2), and hard
ceilings on total path length and key depth exist independently of
configuration — set equal to the range maxima above, so they never
conflict.

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
  new operations.
- **Invalid** — out of range, the wrong type, or missing — the value is
  **ignored** and the previously active one is kept: the compiled-in
  default or the last known-good. An `LCS_SELF_CONFIG_INVALID` audit
  event is emitted naming the parameter, what was wrong, and the value
  being retained (§5.4.4).

**Values are never clamped or silently corrected.** There is no
`min`/`max` on any configuration path. A write to the registry
succeeds, because the source does not enforce kernel semantics, and LCS
simply refuses to use it. The registry shows what was written; the
audit log shows what LCS is running on.

Because "missing" is invalid, a first boot before seed restore emits
nineteen of these events per refresh.

## Hot-swap and in-flight operations

Configuration is published as a whole structure under a seqlock, and a
reader takes a complete copy of it. A syscall entry point snapshots it
once and threads that snapshot through the operation, so in-flight work
uses the values that were current when it started and new work uses the
updated ones.

That is the rule, and mostly the practice. Some deeper paths take a
second snapshot part-way through, and a few call sites read a single
live value rather than a snapshot — `reg_begin_transaction`'s timeout,
the bound-transaction cap, and the in-flight request cap among them.
For those, a hot-swap can be observed mid-operation.

## Security

`Machine\System\Registry\` inherits the `Machine` hive root descriptor
— SYSTEM and Administrators with `KEY_ALL_ACCESS`, Authenticated Users
with `KEY_READ` — so an unprivileged process cannot change any of this.

Domain policy at a higher-precedence layer defends against a
compromised local administrator, which is the reason `SeTcbPrivilege`
guards precedence above 0 (§5.3.4).
