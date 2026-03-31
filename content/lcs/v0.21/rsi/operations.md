---
title: Operations
order: 2
---

RSI operations fall into five groups: path operations, key
operations, value operations, transaction operations, and
maintenance operations.

All operations that return layer-qualified data MUST return all
entries across all layers. LCS performs layer resolution, not the
source. The source returns everything it has; the kernel decides
what is effective.

## Path operations

### RSI_LOOKUP (op_code: 0x01)

Look up a child entry under a parent key. The primary path-walking
primitive -- LCS calls this once per path component.

**Request:** parent key GUID, child name component (string).

**Response:** A list of path entries for this (parent, child) pair
across all layers. Each entry contains:

| Field | Description |
|---|---|
| Layer name | Which layer this entry belongs to. |
| Target | GUID (key exists) or HIDDEN (tombstone). |
| Sequence | The entry's sequence number. |

For each unique GUID referenced in the entries, the response
includes key metadata:

| Field | Description |
|---|---|
| GUID | The key identity. |
| SD | Security Descriptor (binary). LCS needs this for AccessCheck. |
| Volatile | Boolean. |
| Symlink | Boolean. |
| Last write time | Timestamp. |

When the key metadata indicates a symlink, LCS resolves the
target by performing a separate RSI_QUERY_VALUES for the key's
default value (empty-string name) and applying layer resolution
to determine the effective REG_LINK target. This ensures symlink
targets participate correctly in the layer system.

Empty response (no entries) means the child does not exist in any
layer.

### RSI_CREATE_ENTRY (op_code: 0x02)

Create a path entry: (parent, child_name, layer) → GUID.

**Request:** parent GUID, child name, layer name, GUID, sequence
number.

Always paired with RSI_CREATE_KEY which provides the fresh GUID.

### RSI_HIDE_ENTRY (op_code: 0x03)

Create a HIDDEN path entry at (parent, child_name, layer).

**Request:** parent GUID, child name, layer name, sequence number.

### RSI_DELETE_ENTRY (op_code: 0x04)

Remove the path entry at (parent, child_name, layer). Whether it
was a GUID entry or a HIDDEN entry, it is removed.

**Request:** parent GUID, child name, layer name.

### RSI_ENUM_CHILDREN (op_code: 0x05)

Enumerate all child entries under a parent key across all layers.

**Request:** parent GUID.

**Response:** For each unique child name, the same entry format as
RSI_LOOKUP (per-layer path entries with layer name, target type,
GUID, sequence). After all children and their entries, a single
deduplicated metadata block covers all unique GUIDs across all
children (SD, last write time, volatile flag, symlink flag). This
avoids per-child RSI_READ_KEY round trips. HIDDEN entries (zero
GUID) do not contribute to the metadata block.

## Key operations

### RSI_CREATE_KEY (op_code: 0x10)

Create a new key record. The GUID is assigned by LCS and passed to
the source for storage.

**Request:** GUID, name, parent GUID, SD (binary), volatile flag,
symlink flag.

The path entry linking the key into the namespace is created
separately via RSI_CREATE_ENTRY. For symlink keys, the target path
is written as a separate default REG_LINK value via RSI_SET_VALUE.

### RSI_READ_KEY (op_code: 0x11)

Read a key's full record.

**Request:** GUID.

**Response:** name, parent GUID, SD, volatile flag, symlink flag,
last write time.

### RSI_WRITE_KEY (op_code: 0x12)

Update a key's mutable fields. Used for SD updates and last write
time updates.

**Request:** GUID, field bitmask (which fields to update), field
values.

Immutable fields (GUID, volatile, symlink flag) MUST NOT be
specified. The source MUST reject requests that attempt to modify
immutable fields.

### RSI_DROP_KEY (op_code: 0x13)

Purge all data associated with a GUID: key record, all value
entries across all layers, all path entries, and any blanket
tombstones. Called when an orphaned key's last fd closes.

**Request:** GUID.

RSI_DROP_KEY is idempotent. If the GUID does not exist in the
source (e.g., already cleaned up by crash recovery), the source
MUST return RSI_OK.

## Value operations

### RSI_QUERY_VALUES (op_code: 0x20)

Retrieve all layer entries for a specific value, or all values for
a key.

**Request:** GUID, value name. If value name is the empty sentinel
with a query-all flag set, return all values for the key across all
layers.

**Response:** List of entries. Each entry contains:

| Field | Description |
|---|---|
| Value name | The value's name. |
| Layer name | Which layer this entry belongs to. |
| Type | Value type (uint32). REG_TOMBSTONE for tombstones. |
| Data | Value data (empty for tombstones). |
| Sequence | The entry's sequence number. |

Additionally, the response includes blanket tombstone state for
the key: a list of (layer name, sequence number) pairs for each
active blanket tombstone on this key.

### RSI_SET_VALUE (op_code: 0x21)

Store a value entry at (GUID, value_name, layer).

**Request:** GUID, value name, layer name, type, data, sequence
number, optional expected_sequence (uint64).

If an entry already exists for this (GUID, value name, layer), it
is replaced. If type is REG_TOMBSTONE, the source stores a
tombstone marker instead of data.

**Conditional write.** If expected_sequence is non-zero, the source
MUST check that the current entry at (GUID, value name, layer) has
this sequence number before writing. If the sequence does not match
or no entry exists, the source MUST return RSI_CAS_FAILED without
writing.

### RSI_DELETE_VALUE_ENTRY (op_code: 0x22)

Remove the entry at (GUID, value_name, layer). Whether it was a
normal value or a tombstone, it is removed. Idempotent.

**Request:** GUID, value name, layer name.

### RSI_SET_BLANKET_TOMBSTONE (op_code: 0x23)

Set or remove a blanket tombstone on (GUID, layer).

**Request:** GUID, layer name, set flag (boolean), sequence number.

If set is true, the source stores a blanket tombstone marker on
(GUID, layer) with the given sequence number. If set is false, the
source removes the blanket tombstone.

## Transaction operations

### RSI_BEGIN_TRANSACTION (op_code: 0x30)

Signal the start of a transaction.

**Request:** transaction ID (uint64).

The source allocates transaction state. Subsequent operations
tagged with this transaction ID are part of the transaction.

### RSI_COMMIT_TRANSACTION (op_code: 0x31)

Atomically commit all operations in the transaction.

**Request:** transaction ID.

On success, all changes are durable. On failure, all changes are
rolled back and the source reports the error.

### RSI_ABORT_TRANSACTION (op_code: 0x32)

Roll back all operations in the transaction.

**Request:** transaction ID.

Called when the transaction fd is closed without committing, or on
timeout.

## Layer operations

### RSI_DELETE_LAYER (op_code: 0x50)

Remove all entries tagged with a layer name from the source's
storage. Called by LCS when a layer's metadata key is deleted.

**Request:** layer name (string).

**Response (success):**

| Field | Description |
|---|---|
| status | RSI_OK. |
| orphaned_guids | Array of GUIDs that lost their last path entry as a result of this operation. LCS tracks these for deferred deletion (Drop when last fd closes). |

The source MUST atomically remove:
- All path entries where layer = layer_name
- All value entries where layer = layer_name
- All blanket tombstones where layer = layer_name

The source MUST NOT remove key records (GUIDs) -- orphan cleanup
is managed by LCS via RSI_DROP_KEY when the last fd closes.

If the layer name is unknown to the source (no entries exist for
it), the source MUST return RSI_OK with an empty orphaned_guids
list. This is not an error -- a layer may have entries in some
sources but not others.

## Maintenance operations

### RSI_FLUSH (op_code: 0x40)

Persist all pending writes to durable storage.

**Request:** (no fields beyond header).

**Response:** Returns when persistence is confirmed.
