---
title: Operations
description: All eighteen RSI operations — path, key, value and layer — and the rule that a source returns every layer-qualified entry without pre-filtering.
---

Eighteen operations. Every one that returns layer-qualified data MUST
return **all** entries across **all** layers: a source MUST NOT
pre-filter, resolve, or omit. The kernel decides what is effective.

Every response payload begins with a `u32` status. Payload fields
below are listed after it, in wire order, with no padding between them.
"Status only" means the payload is the status and nothing else — 18
bytes in total.

| Operation | Code | Response |
|---|---|---|
| `RSI_LOOKUP` | `0x0001` | `0x8001` |
| `RSI_CREATE_ENTRY` | `0x0002` | `0x8002` |
| `RSI_HIDE_ENTRY` | `0x0003` | `0x8003` |
| `RSI_DELETE_ENTRY` | `0x0004` | `0x8004` |
| `RSI_ENUM_CHILDREN` | `0x0005` | `0x8005` |
| `RSI_CREATE_KEY` | `0x0010` | `0x8010` |
| `RSI_READ_KEY` | `0x0011` | `0x8011` |
| `RSI_WRITE_KEY` | `0x0012` | `0x8012` |
| `RSI_DROP_KEY` | `0x0013` | `0x8013` |
| `RSI_QUERY_VALUES` | `0x0020` | `0x8020` |
| `RSI_SET_VALUE` | `0x0021` | `0x8021` |
| `RSI_DELETE_VALUE_ENTRY` | `0x0022` | `0x8022` |
| `RSI_SET_BLANKET_TOMBSTONE` | `0x0023` | `0x8023` |
| `RSI_BEGIN_TRANSACTION` | `0x0030` | `0x8030` |
| `RSI_COMMIT_TRANSACTION` | `0x0031` | `0x8031` |
| `RSI_ABORT_TRANSACTION` | `0x0032` | `0x8032` |
| `RSI_FLUSH` | `0x0040` | `0x8040` |
| `RSI_DELETE_LAYER` | `0x0050` | `0x8050` |

Any other operation code is invalid.

## Path operations

### `RSI_LOOKUP`

Look up a child entry under a parent key. This is the path-walking
primitive; the kernel issues one per path component.

**Request:** `parent_guid` (16), `child_name` (length-prefixed).

**Response:** `entry_count` (`u32`), then that many path entries:

| Size | Field |
|---|---|
| 4+n | `layer_name` |
| 1 | `target_type`: 0 = GUID, 1 = HIDDEN |
| 16 | `target_guid` |
| 8 | `sequence` |

then `metadata_count` (`u32`), then that many key metadata entries:

| Size | Field |
|---|---|
| 16 | `guid` |
| 4+n | `sd`, binary |
| 1 | `volatile` |
| 1 | `symlink` |
| 8 | `last_write_time` |

An empty response — `entry_count` zero — means the child does not exist
in any layer. That is an ordinary answer, not an error.

The metadata block is **deduplicated**: exactly one entry per distinct
GUID referenced by the path entries. A source MUST satisfy all of:

- every GUID appearing as a target has exactly one metadata entry;
- no metadata entry is duplicated;
- no metadata entry is unreferenced;
- no metadata GUID is all-zero;
- a HIDDEN entry MUST carry an all-zero `target_guid` and MUST NOT
  contribute a metadata entry.

Violating any of these is malformed data.

The kernel resolves symlink targets itself, by issuing a separate
`RSI_QUERY_VALUES` for the key's default value. A source MUST NOT
interpret the symlink flag or follow anything.

### `RSI_CREATE_ENTRY`

Create a path entry `(parent, child_name, layer) → guid`.

**Request:** `parent_guid` (16), `child_name`, `layer_name`,
`child_guid` (16), `sequence` (`u64`).

**Response:** status only.

Always paired with `RSI_CREATE_KEY`, which carries the same GUID. The
kernel sends `RSI_CREATE_ENTRY` **first**, so that a losing race is
detected before a key record is created: an `RSI_ALREADY_EXISTS` here
means another writer got the name.

### `RSI_HIDE_ENTRY`

Create a HIDDEN path entry at `(parent, child_name, layer)`.

**Request:** `parent_guid` (16), `child_name`, `layer_name`,
`sequence` (`u64`).

**Response:** status only.

### `RSI_DELETE_ENTRY`

Remove the path entry at `(parent, child_name, layer)`, whether it was
a GUID entry or a HIDDEN one.

**Request:** `parent_guid` (16), `child_name`, `layer_name`.

**Response:** status only.

### `RSI_ENUM_CHILDREN`

Enumerate every child entry under a parent, across all layers.

**Request:** `parent_guid` (16).

**Response:** `child_count` (`u32`), then per child:

| Size | Field |
|---|---|
| 4+n | `child_name` |
| 4 | `entry_count` |
| … | that many path entries, in the `RSI_LOOKUP` entry format |

followed by **one** metadata block, in the `RSI_LOOKUP` metadata
format, covering the distinct GUIDs across all children. Emitting it
once rather than per child is what makes this cheaper than a lookup per
name.

The same deduplication and closure rules apply, evaluated across the
whole response.

## Key operations

### `RSI_CREATE_KEY`

Create a key record. The GUID is assigned by the kernel.

**Request:** `guid` (16), `name`, `parent_guid` (16), `sd` (binary,
length-prefixed), `volatile` (1), `symlink` (1).

**Response:** status only.

The path entry linking the key into the namespace is created separately
by `RSI_CREATE_ENTRY`. For a symlink key, the target is written
afterwards as a default `REG_LINK` value through `RSI_SET_VALUE`.

A source MUST persist the GUID exactly as given: no rewriting, no
remapping, no reassignment. GUIDs are the kernel's identity for keys
and the source's primary key for storage.

### `RSI_READ_KEY`

**Request:** `guid` (16).

**Response:** `name`, `parent_guid` (16), `sd`, `volatile` (1),
`symlink` (1), `last_write_time` (`i64`).

### `RSI_WRITE_KEY`

Update a key's mutable fields.

**Request:** `guid` (16), `field_mask` (`u32`), then the named fields
in bit order.

| Bit | Field | Encoding |
|---|---|---|
| 0 | `sd` | length-prefixed |
| 1 | `last_write_time` | `i64` |

Only fields whose bit is set are present. Any other bit set in
`field_mask` is invalid.

**Response:** status only.

There is no way to express a change to the GUID, the volatile flag or
the symlink flag: those fields are simply absent from the request. A
source MUST reject a request attempting to modify an immutable field
with `RSI_INVALID`.

A `field_mask` of zero is a well-formed existence check that mutates
nothing.

### `RSI_DROP_KEY`

Purge everything associated with a GUID: the key record, all value
entries across all layers, all path entries, and all blanket
tombstones.

**Request:** `guid` (16).

**Response:** status only.

`RSI_DROP_KEY` MUST be idempotent. If the GUID does not exist — already
purged by startup cleanup, say — the source MUST return `RSI_OK`.

The kernel issues this when the last descriptor to an unnamed key
closes, and it issues it **without a waiting caller**. A source MUST
answer it like any other request.

## Value operations

### `RSI_QUERY_VALUES`

Retrieve every layer entry for one value, or for all values on a key.

**Request:** `guid` (16), `value_name`, `query_all` (1). When
`query_all` is set the value name is empty and every value on the key
is returned.

**Response:** `entry_count` (`u32`), then per entry:

| Size | Field |
|---|---|
| 4+n | `value_name` |
| 4+n | `layer_name` |
| 4 | `type` |
| 4+n | `data`, binary |
| 8 | `sequence` |

then `blanket_count` (`u32`), then per blanket tombstone:

| Size | Field |
|---|---|
| 4+n | `layer_name` |
| 8 | `sequence` |

The blanket list is part of every response, including one for a single
named value: the kernel needs it to resolve that name.

A tombstone entry carries type `REG_TOMBSTONE` (`0xFFFF`) and
zero-length data. A source MUST NOT return a tombstone with data, an
undefined value type, or data exceeding the configured maximum value
size.

### `RSI_SET_VALUE`

Store a value entry at `(guid, value_name, layer)`, replacing any
existing entry for that triple.

**Request:** `guid` (16), `value_name`, `layer_name`, `type` (`u32`),
`data`, `sequence` (`u64`), `expected_sequence` (`u64`).

**Response:** status only.

**Conditional writes.** A source MUST support `expected_sequence`.
Zero means unconditional. Non-zero means the source MUST **atomically**
verify that the current entry at `(guid, value_name, layer)` carries
that sequence number before writing, and MUST return `RSI_CAS_FAILED`
without writing if it does not match or if no entry exists.

The condition is against the layer's own entry, not against any
resolved value. A source does not know what is effective and MUST NOT
try to work it out.

### `RSI_DELETE_VALUE_ENTRY`

Remove the entry at `(guid, value_name, layer)`, whether it was a value
or a tombstone.

**Request:** `guid` (16), `value_name`, `layer_name`.

**Response:** status only.

This operation MUST be idempotent: a source MUST return `RSI_OK` when
there was no entry to remove. The kernel does not mask `RSI_NOT_FOUND`
here, so a source returning it makes the caller's delete fail.

### `RSI_SET_BLANKET_TOMBSTONE`

Set or remove a blanket tombstone on `(guid, layer)`.

**Request:** `guid` (16), `layer_name`, `set` (1), `sequence` (`u64`).

**Response:** status only.

## Transaction operations

### `RSI_BEGIN_TRANSACTION`

**Request:** `txn_id` (`u64`), `mode` (`u32`).

The transaction id appears in the payload. The request header's own
`txn_id` is zero for this operation, since the transaction does not yet
exist. `RSI_COMMIT_TRANSACTION` and `RSI_ABORT_TRANSACTION` carry it in
both places.

| Mode | Value | Meaning |
|---|---|---|
| `RSI_TXN_READ_WRITE` | 0 | An ordinary transaction. |
| `RSI_TXN_READ_ONLY` | 1 | A point-in-time read snapshot. |

**Response:** status only.

For `RSI_TXN_READ_WRITE`, reads tagged with the id MUST observe the
transaction's own uncommitted writes, and writes tagged with it MUST be
committed atomically by `RSI_COMMIT_TRANSACTION`.

For `RSI_TXN_READ_ONLY`, reads tagged with the id MUST observe a stable
point-in-time snapshot. The kernel MUST NOT send a mutating operation
with a read-only transaction id, and a source that receives one MUST
reject it with `RSI_INVALID` and MUST NOT mutate anything. A read-only
transaction is released with `RSI_ABORT_TRANSACTION`; the kernel MUST
NOT send `RSI_COMMIT_TRANSACTION` for one.

A source whose store cannot support a mode MAY answer
`RSI_TXN_NOT_SUPPORTED` for that mode. The two are independent: a
source MAY support read-only snapshots without supporting read-write
transactions.

### `RSI_COMMIT_TRANSACTION`

**Request:** `txn_id` (`u64`).

**Response:** status only.

On success every change in the transaction MUST be durable. On failure
every change MUST be rolled back.

### `RSI_ABORT_TRANSACTION`

**Request:** `txn_id` (`u64`).

**Response:** status only.

Sent when a transaction is closed without committing, on timeout, and
to release a read-only snapshot. The kernel MAY send it without a
waiting caller.

## Layer operations

### `RSI_DELETE_LAYER`

Remove everything tagged with a layer name.

**Request:** `layer_name`.

**Response:** `orphaned_guid_count` (`u32`), then that many GUIDs (16
each).

The source MUST atomically remove all path entries, all value entries
and all blanket tombstones whose layer is `layer_name`, and MUST NOT
remove any key record. Orphan cleanup is the kernel's, through
`RSI_DROP_KEY`.

`orphaned_guids` MUST list exactly the GUIDs that lost their last path
entry as a result, with no nil GUID and no duplicates. The kernel
tracks them for deferred deletion.

An unknown layer name is **not** an error. A source with no entries for
it MUST return `RSI_OK` with an empty orphan list — a layer may have
entries in one source and none in another.

## Maintenance

### `RSI_FLUSH`

Persist pending writes for one hive to durable storage.

**Request:** `hive_name`.

**Response:** status only, returned when persistence is confirmed.

This is the only operation that identifies its target by hive name
rather than by GUID, because flushing is a hive-level act — a WAL
checkpoint, say — not a key-level one.
