---
title: Ioctls
---

All ioctls on key fds use type byte `'R'`. Each ioctl checks the
fd's granted access mask before proceeding. If the required access
right is not present, the ioctl returns EACCES without contacting
the source.

All mutating ioctls accept an optional transaction fd. If provided,
the operation is enlisted in the transaction. If the transaction is
bound to a different hive than the key's hive, the ioctl
returns EXDEV.

Read ioctls (REG_IOC_QUERY_VALUE, REG_IOC_QUERY_VALUES_BATCH,
REG_IOC_ENUM_VALUES, REG_IOC_ENUM_SUBKEYS) also accept an
optional transaction fd. If provided, the read is performed within
the transaction's context, providing read-your-own-writes
isolation: the caller sees the transaction's uncommitted writes.

All mutating ioctls that accept a layer name parameter perform
**layer write authorization** before proceeding. LCS verifies that
the caller's token has KEY_SET_VALUE on the target layer's metadata
key at `Machine\System\Registry\Layers\<layer_name>\`. If the
caller lacks access, the ioctl returns EACCES. If the named layer
does not exist in the layer table, the ioctl returns ENOENT. LCS
caches layer metadata SDs alongside the layer table and invalidates
the cache via the self-watch mechanism.

**Base layer fallback.** The base layer's metadata key at
`Machine\System\Registry\Layers\base\` inherits from the Machine
hive root (SYSTEM and Administrators: KEY_ALL_ACCESS). If the base
layer's metadata key does not yet exist (first boot before seed
restore), LCS uses a compiled-in default SD granting KEY_ALL_ACCESS
to SYSTEM and Administrators. This default is replaced when the
key is created via seed restore.

## Common ioctl errors

The following errors apply to all key fd ioctls unless stated
otherwise:

| Errno | Condition |
|---|---|
| EACCES | The fd's granted mask does not include the required access right, or layer write authorization failed. |
| EIO | Source is unavailable or returned an internal error. |
| ETIMEDOUT | Source did not respond within RequestTimeoutMs. |
| ENOMEM | Kernel memory allocation failed. |
| EXDEV | Transaction fd is bound to a different hive (mutating ioctls only). |
| ENOENT | Target layer does not exist in the layer table (layer-targeting ioctls only). |

Individual ioctls document additional errors specific to their
operation.

## Key fd ioctls

### REG_IOC_QUERY_VALUE

Read the effective value of a named value on this key.

| Field | Value |
|---|---|
| Direction | _IOWR |
| Required access | KEY_QUERY_VALUE |

**Input:** Value name (string, empty string for default value),
optional transaction fd.

**Output:** Value type (uint32), data (bytes), data length,
effective sequence (uint64), effective layer name (string). When
the effective entry is from the base layer, the returned layer
name is `"base"`.

**Behaviour:** LCS sends a query to the source for all layer
entries of this (key GUID, value name) plus any blanket tombstones
on the key. If a transaction fd is provided, the query is sent
within the transaction's context (read-your-own-writes). LCS resolves through the layer stack and returns the
effective value. If the effective entry is a tombstone or blanket
tombstone, returns ENOENT. If no entries exist, returns ENOENT.

**Additional errors:**

| Errno | Condition |
|---|---|
| ENOENT | Value does not exist after layer resolution. |
| ERANGE | Caller-provided data buffer or layer name buffer is too small. data_len and/or layer_len are set to the required sizes. |

### REG_IOC_SET_VALUE

Write a value entry in a specific layer, with optional conditional
write support.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | KEY_SET_VALUE |

**Input:** Value name (string), value type (uint32), data (bytes),
layer name (string, null for base layer), optional transaction fd,
optional expected_sequence (uint64).

**Behaviour:** LCS assigns the next sequence number from the global
counter and sends a write to the source: store
(key GUID, value name, layer) → (type, data, sequence).

If type is REG_TOMBSTONE, the source stores a tombstone entry.
REG_TOMBSTONE is never exposed to callers reading values.

Updates the key's last write time.

**Conditional writes.** If expected_sequence is non-zero, LCS
passes it to the source in the RSI_SET_VALUE request. The source
MUST atomically verify that the layer's current entry at
(key GUID, value name, layer) has this sequence number before
writing. If the sequence does not match or no entry exists, the
source returns RSI_CAS_FAILED and LCS returns EAGAIN to the
caller.

The condition is evaluated against the **layer's own entry**, not
the effective value, and is enforced **by the source** atomically.
LCS does not perform a separate query-then-write. This prevents
lost updates from concurrent writers within the same layer.
Cross-layer overrides are not conflicts -- they are the layer
system working as designed.

**Additional errors:**

| Errno | Condition |
|---|---|
| EAGAIN | Conditional write failed -- layer entry sequence mismatch. |
| ENOSPC | Layer cap exceeded for this (key GUID, value name). Value data exceeds MaxValueSize. |
| ENAMETOOLONG | Value name exceeds MaxPathComponentLength. |
| EPERM | Writing a Precedence value > 0 to a layer metadata key without SeTcbPrivilege. |

### REG_IOC_DELETE_VALUE

Remove a layer's entry for a value.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | KEY_SET_VALUE |

**Input:** Value name (string), layer name (string, null for base
layer), optional transaction fd.

**Behaviour:** LCS tells the source to remove the entry at
(key GUID, value name, layer). If no entry exists for that layer,
returns success (idempotent). Updates the key's last write time.

This removes the layer's opinion -- whether it was a normal value
or a tombstone. If lower-precedence layers have entries, they
become effective.

### REG_IOC_BLANKET_TOMBSTONE

Write or remove a blanket tombstone for a layer on this key.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | KEY_SET_VALUE |

**Input:** Layer name (string, null for base layer), set flag
(boolean -- true to write, false to remove), optional transaction
fd.

**Behaviour:** If set is true, LCS tells the source to set the
blanket tombstone flag on (key GUID, layer). This masks all values
from lower-precedence layers for this key. A new sequence number
is assigned for watch dispatch ordering.

If set is false, LCS tells the source to remove the blanket
tombstone. Lower-precedence values become visible again.

Updates the key's last write time. Watch events are generated for
each value whose effective state changed.

### REG_IOC_QUERY_VALUES_BATCH

Read all effective values for this key in a single call.

| Field | Value |
|---|---|
| Direction | _IOWR |
| Required access | KEY_QUERY_VALUE |

**Input:** Buffer for results.

**Output:** Array of (name, type, data, data_length) tuples for
all effective values. Values masked by tombstones or blanket
tombstones are omitted.

**Behaviour:** LCS requests all values for this key GUID from the
source, resolves each through the layer stack (including blanket
tombstones), and returns the complete effective value set in one
call.

This replaces the index-based REG_IOC_ENUM_VALUES loop for callers
that want all values. It avoids the O(n²) cost of repeated
single-index enumeration.

**Additional errors:**

| Errno | Condition |
|---|---|
| ERANGE | Buffer too small. buf_len is set to the required size. |

### REG_IOC_ENUM_VALUES

Enumerate values by index. Returns one effective value per call.

| Field | Value |
|---|---|
| Direction | _IOWR |
| Required access | KEY_QUERY_VALUE |

**Input:** Index (uint32), buffer for name/type/data.

**Output:** Value name, type, data, data length at the given index.

**Behaviour:** LCS requests all values for this key GUID from the
source, resolves each through the layer stack, filters out
tombstones and blanket-masked values, and returns the entry at the
requested index. Returns ENOENT when the index is past the last
value.

**Additional errors:**

| Errno | Condition |
|---|---|
| ENOENT | Index past end of value list. |
| ERANGE | Name or data buffer too small. |

Each call re-resolves the full value set. A 0..N-1 enumeration
loop performs N full resolutions -- O(n²) total work. For most
keys (< 20 values) this is negligible. For hot paths, use
REG_IOC_QUERY_VALUES_BATCH.

Enumeration order is not defined. The index-to-entry mapping may
change between calls if the key's effective values change
(mutations, layer changes). Callers MUST NOT cache indices across
mutations. Use REG_IOC_QUERY_VALUES_BATCH for a consistent
snapshot of all values.

### REG_IOC_ENUM_SUBKEYS

Enumerate child keys by index.

| Field | Value |
|---|---|
| Direction | _IOWR |
| Required access | KEY_ENUMERATE_SUB_KEYS |

**Input:** Index (uint32), buffer for name and metadata.

**Output:** Subkey name, last write time, subkey count, value count
at the given index.

**Behaviour:** LCS requests all child path entries from the source,
resolves visibility through the layer stack, and returns the entry
at the requested index. Returns ENOENT when past the last subkey.

No per-child AccessCheck is performed during enumeration. All
visible children are returned regardless of the caller's access to
individual child keys. The caller learns child key names but MUST
open each child separately (with AccessCheck) to read its contents.
This matches Windows RegEnumKeyEx and filesystem readdir semantics.

Same O(n²) characteristic as REG_IOC_ENUM_VALUES.

**Additional errors:**

| Errno | Condition |
|---|---|
| ENOENT | Index past end of subkey list. |
| ERANGE | Name buffer too small. |

### REG_IOC_QUERY_KEY_INFO

Query metadata about the key.

| Field | Value |
|---|---|
| Direction | _IOR |
| Required access | READ_CONTROL |

**Output:** Key name, last write time, subkey count, value count,
max subkey name length, max value name length, max value data size,
SD size, volatile flag, symlink flag, hive generation number.

**Hive generation number.** A monotonic counter representing the
highest write sequence number committed to this key's hive. Exposed
on every key for convenience. Watchers that receive OVERFLOW can
compare their last-seen generation with the current value to detect
missed changes without speculatively re-reading the entire subtree.

The hive generation number is incremented once per committed
mutation or once per committed transaction (not per operation
within the transaction). Specifically: a non-transactional write
increments by 1; a committed transaction increments by 1
regardless of how many operations it contains.

**Layer operations and atomicity.** When a layer metadata key is
deleted, LCS processes the metadata key deletion and the resulting
layer effects (RSI_DELETE_LAYER, effective state recomputation,
watch events) as a single atomic generation increment. There is no
generation number at which the metadata key is gone but the layer's
data entries are still resolving. For layer operations that affect
multiple hives, each affected hive's generation number is
incremented independently. Layer precedence changes that alter
effective state also produce a single generation increment
encompassing all effects.

**Behaviour:** LCS queries the source for subkey and value counts,
maximum name/data lengths, and SD size via RSI operations. The key
name, flags, last write time, and hive generation number are
available from kernel-side state (the fd's metadata and the
per-hive generation counter). The hive generation number is purely
kernel-side state, not persisted by the source, and resets to the
source's max_sequence on LCS restart.

**Additional errors:**

| Errno | Condition |
|---|---|
| ERANGE | Name buffer too small. |

### REG_IOC_DELETE_KEY

Remove this key's path entry from a specific layer.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | DELETE |

**Input:** Layer name (string, null for base layer), optional
transaction fd.

**Behaviour:** LCS derives the parent GUID (second-to-last entry
in the fd's ancestor chain) and the child name (last component of
the fd's resolved path) and tells the source to remove the path
entry via RSI_DELETE_ENTRY(parent_GUID, child_name, layer). If no
remaining path entries exist
across any layer, the key is orphaned (§2.8).
Updates the parent key's last write time.

Does NOT delete child keys. Returns ENOTEMPTY if the key has
visible children.

**Additional errors:**

| Errno | Condition |
|---|---|
| ENOTEMPTY | Key has visible children. |

### REG_IOC_HIDE_KEY

Create a HIDDEN path entry in a layer, masking this key from
visibility.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | DELETE |

**Input:** Layer name (string, null for base layer), optional
transaction fd.

**Behaviour:** LCS derives the parent GUID and child name from the
fd's ancestor chain and resolved path (same derivation as
REG_IOC_DELETE_KEY) and tells the source to create a HIDDEN path
entry via RSI_HIDE_ENTRY(parent_GUID, child_name, layer). The HIDDEN entry masks
lower-precedence path entries during resolution. A new sequence
number is assigned.

The caller MUST have an open fd to the key being hidden (proving
access). The HIDDEN entry is created at the path stored on the fd,
in the specified layer.

When the hiding layer is removed, the lower-precedence key
reappears.

### REG_IOC_GET_SECURITY

Read the key's Security Descriptor.

| Field | Value |
|---|---|
| Direction | _IOWR |
| Required access | READ_CONTROL (owner, group, DACL). ACCESS_SYSTEM_SECURITY (SACL). |

**Input:** Security information flags (which SD components to
return: owner, group, DACL, SACL).

**Output:** SD in binary KACS format.

**Additional errors:**

| Errno | Condition |
|---|---|
| ERANGE | SD buffer too small. sd_len is set to the required size. |

### REG_IOC_SET_SECURITY

Modify the key's Security Descriptor.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | WRITE_DAC (DACL). WRITE_OWNER (owner). ACCESS_SYSTEM_SECURITY (SACL). |

**Input:** Security information flags (which components to set),
SD in binary KACS format, optional transaction fd.

**Behaviour:** LCS merges the provided SD components into the
key's existing SD and tells the source to persist the update. SD
changes are NOT layer-qualified -- they modify the key directly.
Updates the key's last write time.

**Transaction interaction.** If a transaction fd is provided, the
SD change is enlisted in the transaction. It commits or aborts
with the rest of the transaction's operations. The SD change is
still a direct mutation on the key (not tagged with a layer, not
reverted on layer deletion) -- the transaction provides atomicity,
not layer qualification. An SD change in an aborted transaction
is not applied.

### REG_IOC_NOTIFY

Arm this key fd for change watches.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required access | KEY_NOTIFY |

**Input:** Filter (bitmask of event types), subtree flag (boolean).

**Behaviour:** Arms the fd. After arming, the fd is pollable via
epoll/poll/select -- EPOLLIN indicates pending events. read() on
the fd returns structured event records (§4.1).

Calling REG_IOC_NOTIFY on an already-armed fd replaces the
previous filter and subtree settings. Calling with filter=0
disarms the watch -- pending events are discarded and no further
events are queued until re-armed.

KEY_DELETED and OVERFLOW events are always delivered regardless of
filter setting.

### REG_IOC_FLUSH

Force the source to persist pending writes for this key's hive.

| Field | Value |
|---|---|
| Direction | _IO |
| Required access | KEY_SET_VALUE |

**Behaviour:** LCS sends a flush command to the source. Returns
when persistence is confirmed. KEY_SET_VALUE is required because
flush is only meaningful for callers who have written data that
needs durability guarantees. This prevents unprivileged readers
from using flush as a disk I/O amplification vector.

### REG_IOC_BACKUP

Export this key and its entire subtree to an fd.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required privilege | SeBackupPrivilege (PSD-004 §7) |

**Input:** Output fd (any writable fd).

**Behaviour:** LCS opens a read-only transaction on the source
(via RSI_BEGIN_TRANSACTION) to guarantee a point-in-time snapshot,
then reads the entire subtree and writes it to the output fd in
the standard backup format (§9.1). The
transaction is closed when the backup completes. Concurrent
mutations do not affect the backup stream. Privilege check only
-- no per-key AccessCheck. LCS MUST emit an audit event for every
backup operation regardless of SACL state on the target key. The
audit event includes the caller's token, the target key GUID, and
the output fd.

**Additional errors:**

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeBackupPrivilege. |
| EBADF | Output fd is not writable. |

### REG_IOC_RESTORE

Replace this key and its entire subtree from an fd.

| Field | Value |
|---|---|
| Direction | _IOW |
| Required privilege | SeRestorePrivilege (PSD-004 §7) |

**Input:** Input fd (any readable fd).

**Behaviour:** See §9.1. Privilege check only
-- no per-key AccessCheck. The restore operation MUST be wrapped
in a single source transaction. Sources that return
RSI_TXN_NOT_SUPPORTED for REG_IOC_RESTORE MUST be rejected —
restore requires transactional atomicity. If a GUID collision,
checksum failure, or precedence validation failure occurs, the
entire restore MUST be rolled back. LCS MUST emit an audit event
for every restore operation regardless of SACL state.

**Precedence validation.** After LAYER records are read from the
backup stream but before any KEY records are written, LCS MUST
check whether any layer in the backup has Precedence > 0. If so
and the caller's token does not hold SeTcbPrivilege, the restore
MUST be aborted with EPERM before any data is written to the
source. This is cheap (LAYER records precede KEY records in the
stream) and prevents SeRestorePrivilege from bypassing the
SeTcbPrivilege defense-in-depth for high-precedence layer
creation.

**Additional errors:**

| Errno | Condition |
|---|---|
| EPERM | Caller does not hold SeRestorePrivilege, or restored data contains Precedence > 0 layers and caller does not hold SeTcbPrivilege. |
| EBADF | Input fd is not readable. |
| EINVAL | Backup stream has invalid magic, minimum reader version exceeds this LCS version, or checksum verification failed. |
| EEXIST | GUID collision -- a GUID in the backup already exists elsewhere in the source. |

## Transaction fd ioctls

### REG_IOC_COMMIT

Commit all operations in this transaction.

| Field | Value |
|---|---|
| Direction | _IO |
| Fd type | Transaction fd |

**Behaviour:** LCS tells the bound source to atomically commit all
operations. On success, the transaction is complete -- subsequent
operations return EINVAL. Watch events for all changes are
delivered after commit.

**Errors** (the common key fd error table does not apply to
transaction fd ioctls):

| Errno | Condition |
|---|---|
| EINVAL | Transaction already committed or not bound to any source. |
| EBUSY | Source could not acquire write lock. Retry. |
| EIO | Source failed to commit. Transaction remains open. |
