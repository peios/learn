---
title: Self-Configuration
---

LCS reads its own operational parameters from the registry under
`Machine\System\Registry\`. This is the self-watch mechanism:
compiled-in defaults at boot, hot-swapped to registry values when
available, updated on change.

## Configuration keys

All keys live under `Machine\System\Registry\`. Each has a defined
type, compiled-in default, and valid range. LCS ignores unknown
keys in this subtree.

| Key | Type | Default | Valid range | Description |
|---|---|---|---|---|
| RequestTimeoutMs | REG_DWORD | 30000 | 1000--600000 | Per-request timeout for source round trips. |
| TransactionTimeoutMs | REG_DWORD | 30000 | 1000--600000 | Maximum lifetime of an open transaction. |
| NotificationQueueSize | REG_DWORD | 256 | 16--65536 | Maximum queued events per watcher before overflow. |
| SymlinkDepthLimit | REG_DWORD | 16 | 1--64 | Maximum symlink resolution recursion depth. |
| MaxValueSize | REG_DWORD | 1048576 | 4096--67108864 | Maximum size in bytes for a single value (1 MB default, 64 MB ceiling). |
| MaxKeyDepth | REG_DWORD | 512 | 32--4096 | Maximum nesting depth for key hierarchy. |
| MaxPathComponentLength | REG_DWORD | 255 | 64--1024 | Maximum length in characters of a single key or value name. |
| MaxTotalPathLength | REG_DWORD | 16383 | 1024--65535 | Maximum total length in characters of a full registry path (all components including separators). |
| MaxLayersPerValue | REG_DWORD | 128 | 1--1024 | Maximum number of layers that can write to the same (key GUID, value name) pair. |
| MaxBoundTransactionsPerSource | REG_DWORD | 16 | 1--256 | Maximum number of concurrently bound transactions per source. Prevents write lock starvation via transaction chaining. |
| MaxTotalLayers | REG_DWORD | 1024 | 16--65536 | Maximum number of distinct layers in the in-memory layer table. Prevents unbounded kernel memory consumption from layer creation. |
| MaxRegisteredSources | REG_DWORD | 32 | 1--256 | Maximum number of concurrently registered sources. Bounds routing table size and per-source kernel state. |
| MaxHivesPerSource | REG_DWORD | 64 | 1--1024 | Maximum number of hives a single source can register. |
| MaxConcurrentRSIRequests | REG_DWORD | 256 | 8--4096 | Maximum number of simultaneously in-flight RSI requests per source. Provides back-pressure when a source is slow. |
| MaxScopeGUIDsPerToken | REG_DWORD | 8 | 1--256 | Maximum number of private hive scope GUIDs a thread's credentials can carry. Bounds the per-syscall routing iteration cost. |
| MaxPrivateLayersPerToken | REG_DWORD | 16 | 1--256 | Maximum number of private layer names a thread's credentials can carry. Bounds the per-resolution is_active() iteration cost. |
| MaxSubtreeWatchDepth | REG_DWORD | 0 | 0--4096 | Maximum depth from watched key to descendant for subtree watch event delivery. 0 means unlimited (all descendants). Limits event noise and dispatch cost for deep subtree watches. |
| MaxTransactionWatchEventBurst | REG_DWORD | 4096 | 256--65536 | Maximum watch events generated per-watcher from a single transaction commit before OVERFLOW is forced. Prevents a large transaction from atomically filling a watcher's queue. |

## Validation

When LCS reads a configuration value via the self-watch mechanism,
it validates against the defined range:

- **Valid value:** Hot-swapped into the in-memory configuration.
  Takes effect for new operations. In-flight operations use the
  value active when they started.

- **Invalid value** (out of range, wrong type, missing): Ignored.
  LCS retains the previously active value (compiled-in default or
  last known-good). An audit event is emitted identifying the key,
  the invalid value, and the value being retained.

Values are never clamped or silently corrected. The write to the
registry succeeds (the source does not enforce kernel semantics),
but LCS refuses to use it. The registry shows what was written;
the audit log shows what LCS is actually using.

## Security

LCS tunables live under `Machine\System\Registry\`, which inherits
the Machine hive root SD (SYSTEM and Administrators: KEY_ALL_ACCESS,
Authenticated Users: KEY_READ). Unprivileged processes cannot modify
operational parameters.

Domain policy enforcement via Group Policy at a higher precedence
layer provides defence against compromised local administrators --
SeTcbPrivilege is required for precedence > 0.

## Self-watch mechanism

LCS monitors its own configuration and layer metadata subtrees
using an internal kernel registration — not through the fd-based
ioctl interface exposed to userspace.

LCS registers interest in specific subtree GUIDs using the same
watch map data structure that backs userspace watches. The
registration is a kernel-internal watcher: events are delivered
via an internal callback, not via read() on an fd. The watcher
has no fd, no granted access mask, and no filter — it receives
all event types for the watched subtrees.

On startup, after the first source registers, LCS resolves the
GUIDs for `Machine\System\Registry\` and
`Machine\System\Registry\Layers\` via RSI_LOOKUP and registers
internal subtree watches on both. If either key does not exist
(first boot or empty database), LCS arms a subtree watch on the
Machine\ hive root instead. When seed restore creates the
Registry\ subtree, the root's subtree watch fires, LCS resolves
the specific GUIDs, and re-arms targeted watches on both subtrees. These watches drive:

- **Self-configuration hot-swap:** changes to operational
  parameters under `Machine\System\Registry\` trigger re-read
  and validation.
- **Layer table updates:** changes to layer metadata under
  `Machine\System\Registry\Layers\` trigger re-read of
  precedence, enabled state, and layer metadata SDs.
- **Layer lifecycle:** SUBKEY_CREATED and SUBKEY_DELETED events
  under the Layers\ key trigger layer addition or deletion.

The internal watch mechanism is not exposed to userspace and is
not subject to the NotificationQueueSize limit (LCS processes
events synchronously in the kernel notification path).

## Bootstrap interaction

1. Source registers → LCS reads `Machine\System\Registry\*` →
   keys don't exist yet → compiled-in defaults retained.
2. Seed restore populates `Machine\System\Registry\*` → subtree
   watch fires → LCS validates and hot-swaps to seed values.
3. Subsequent admin changes → watch fires → LCS validates and
   hot-swaps (or rejects with audit event).

At no point does LCS enter a "waiting for configuration" state.
