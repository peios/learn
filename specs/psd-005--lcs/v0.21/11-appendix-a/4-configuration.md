---
title: Configuration Reference
---

Complete reference for all LCS self-configuration parameters. Every
parameter lives under `Machine\System\Registry\` and follows the
self-configuration mechanism described in §8.2: compiled-in
defaults at boot, hot-swapped via self-watch
when registry values are available, validated against defined
ranges, invalid values rejected with audit event.

All parameters are REG_DWORD (uint32). All have compiled-in
defaults that produce correct behaviour without any registry
configuration.

## Timeouts

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\RequestTimeoutMs` | 30000 | 1000 | 600000 | milliseconds | Per-request timeout for RSI round trips to a source. When exceeded, the calling thread receives ETIMEDOUT. The source stays alive. | ETIMEDOUT |
| `Machine\System\Registry\TransactionTimeoutMs` | 30000 | 1000 | 600000 | milliseconds | Maximum lifetime of an open transaction from reg_begin_transaction to auto-abort. Prevents stalled or malicious processes from holding the source's write lock indefinitely. | Transaction auto-aborted; caller's next operation returns EINVAL. |

## Path and naming limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxKeyDepth` | 512 | 32 | 4096 | levels | Maximum nesting depth for the key hierarchy. Bounds ancestor chain memory per fd and path resolution walk length. | EINVAL on reg_open_key / reg_create_key |
| `Machine\System\Registry\MaxPathComponentLength` | 255 | 64 | 1024 | characters | Maximum length of a single key name component, value name, or layer name. | ENAMETOOLONG |
| `Machine\System\Registry\MaxTotalPathLength` | 16383 | 1024 | 65535 | characters | Maximum total length of a full registry path including all components and separators. Matches or exceeds the Windows limit. | ENAMETOOLONG |
| `Machine\System\Registry\SymlinkDepthLimit` | 16 | 1 | 64 | hops | Maximum symlink resolution recursion depth during path resolution. | ELOOP |

## Value limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxValueSize` | 1048576 | 4096 | 67108864 | bytes | Maximum data payload size for a single value. Default 1 MB, ceiling 64 MB. | ENOSPC |

## Layer limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxLayersPerValue` | 128 | 1 | 1024 | layers | Maximum number of layers that can write to the same (key GUID, value name) pair. Bounds per-value layer resolution cost. | ENOSPC |
| `Machine\System\Registry\MaxTotalLayers` | 1024 | 16 | 65536 | layers | Maximum number of distinct layers in the in-memory layer table. Bounds kernel memory consumption from layer creation. | ENOSPC on layer creation |

## Transaction limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxBoundTransactionsPerSource` | 16 | 1 | 256 | transactions | Maximum number of concurrently bound (write-lock-holding) transactions per source. Prevents transaction chaining DoS. | EBUSY on the operation that would bind the transaction |

## Source limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxRegisteredSources` | 32 | 1 | 256 | sources | Maximum number of concurrently registered sources. | ENOSPC on REG_SRC_REGISTER |
| `Machine\System\Registry\MaxHivesPerSource` | 64 | 1 | 1024 | hives | Maximum number of hives a single source can register. | ENOSPC on REG_SRC_REGISTER |
| `Machine\System\Registry\MaxConcurrentRSIRequests` | 256 | 8 | 4096 | requests | Maximum simultaneously in-flight RSI requests per source. When reached, new operations block until an in-flight request completes or times out. | Caller blocks; ETIMEDOUT if blocked too long. |

## Watch limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\NotificationQueueSize` | 256 | 16 | 65536 | events | Maximum queued events per armed watch before overflow. When exceeded, oldest events are dropped and OVERFLOW is inserted. | OVERFLOW event delivered to watcher. |
| `Machine\System\Registry\MaxSubtreeWatchDepth` | 0 | 0 | 4096 | levels | Maximum depth from the watched key to descendant keys for subtree watch event delivery. 0 means unlimited (all descendants). Events for changes deeper than this limit are silently dropped. | Events silently not delivered for changes beyond the depth limit. |
| `Machine\System\Registry\MaxTransactionWatchEventBurst` | 4096 | 256 | 65536 | events | Maximum watch events generated per-watcher from a single transaction commit. When exceeded, LCS stops generating individual events and inserts a single OVERFLOW instead. | OVERFLOW event delivered to watcher. |

## Private hive and layer credential limits

| Full path | Default | Min | Max | Unit | Description | Errno on violation |
|---|---|---|---|---|---|---|
| `Machine\System\Registry\MaxScopeGUIDsPerToken` | 8 | 1 | 256 | GUIDs | Maximum private hive scope GUIDs a thread's credentials can carry. Bounds per-syscall routing iteration cost. | Error at credential attachment time (KACS concern). |
| `Machine\System\Registry\MaxPrivateLayersPerToken` | 16 | 1 | 256 | layers | Maximum private layer names a thread's credentials can carry. Bounds per-resolution is_active() iteration cost. | Error at credential attachment time (KACS concern). |

## Notes

- All parameters are read from `Machine\System\Registry\` via the
  self-watch mechanism. Changes take effect for new operations
  after the self-watch callback completes. In-flight operations
  use the value active when they started.

- Invalid values (out of range, wrong type) are silently ignored.
  LCS retains the previous known-good value and emits an audit
  event.

- Values are never clamped. The registry shows what was written;
  the audit log shows what LCS is actually using.

- The SD on `Machine\System\Registry\` controls who can modify
  these parameters. By default: SYSTEM and Administrators have
  KEY_ALL_ACCESS, Authenticated Users have KEY_READ. Domain
  policy via Group Policy at higher precedence layers provides
  additional protection.
