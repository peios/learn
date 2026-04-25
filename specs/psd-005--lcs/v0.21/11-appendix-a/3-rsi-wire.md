---
title: RSI Wire Format
---

Byte-level layouts for all RSI messages over `/dev/pkm_registry`.
All multi-byte integers are little-endian. Strings are UTF-8,
length-prefixed with uint32. GUIDs are 16 bytes.

## Common header

Every request begins with:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | total_len |
| 4 | 8 | request_id |
| 12 | 2 | op_code |
| 14 | 8 | txn_id (0 = no transaction) |

Total request header: 22 bytes. Payload follows immediately.

Response messages begin with:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | total_len |
| 4 | 8 | request_id |
| 12 | 2 | op_code (high bit set: op_code \| 0x8000) |

Total response header: 14 bytes. Payload follows (status + data).

Every response payload begins with:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | status |

Status 0 = success. Non-zero = RSI error code.

## Variable-length encoding

Strings and byte arrays are encoded as:

```
┌──────────────┬───────────────────┐
│ len (uint32) │ data (len bytes)  │
└──────────────┴───────────────────┘
```

Arrays of structs are encoded as:

```
┌───────────────┬─────────┬─────────┬─────┐
│ count (uint32)│ entry_0 │ entry_1 │ ... │
└───────────────┴─────────┴─────────┴─────┘
```

## Path operations

### RSI_LOOKUP (0x01)

**Request payload:**

| Offset | Size | Field |
|---|---|---|
| 0 | 16 | parent_guid |
| 16 | 4+N | child_name (length-prefixed string) |

**Response payload (success):**

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | status |
| 4 | 4 | entry_count |

Followed by entry_count path entries:

| Size | Field |
|---|---|
| 4+N | layer_name (length-prefixed) |
| 1 | target_type (0 = GUID, 1 = HIDDEN) |
| 16 | target_guid (zeroed if HIDDEN) |
| 8 | sequence |

Followed by key metadata for each unique GUID:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | metadata_count |

Per metadata entry:

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | sd (length-prefixed bytes) |
| 1 | volatile |
| 1 | symlink |
| 8 | last_write_time |

HIDDEN entries (target_type=1, zero GUID) do not contribute
metadata entries. The metadata_count reflects only unique non-zero
GUIDs.

When the symlink flag is set, LCS resolves the target by issuing
a separate RSI_QUERY_VALUES for the key's default value.

### RSI_CREATE_ENTRY (0x02)

**Request payload:**

| Size | Field |
|---|---|
| 16 | parent_guid |
| 4+N | child_name |
| 4+N | layer_name |
| 16 | child_guid |
| 8 | sequence |

**Response:** status only.

### RSI_HIDE_ENTRY (0x03)

**Request payload:**

| Size | Field |
|---|---|
| 16 | parent_guid |
| 4+N | child_name |
| 4+N | layer_name |
| 8 | sequence |

**Response:** status only.

### RSI_DELETE_ENTRY (0x04)

**Request payload:**

| Size | Field |
|---|---|
| 16 | parent_guid |
| 4+N | child_name |
| 4+N | layer_name |

**Response:** status only.

### RSI_ENUM_CHILDREN (0x05)

**Request payload:**

| Size | Field |
|---|---|
| 16 | parent_guid |

**Response:** Same format as RSI_LOOKUP but with multiple child
names. Encoded as:

| Size | Field |
|---|---|
| 4 | status |
| 4 | child_count |

Per child:

| Size | Field |
|---|---|
| 4+N | child_name |
| 4 | entry_count |

Per entry within child (same as LOOKUP entries):

| Size | Field |
|---|---|
| 4+N | layer_name |
| 1 | target_type |
| 16 | target_guid |
| 8 | sequence |

Followed by key metadata block (same as LOOKUP).

## Key operations

### RSI_CREATE_KEY (0x10)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | name |
| 16 | parent_guid |
| 4+N | sd (length-prefixed bytes) |
| 1 | volatile |
| 1 | symlink |

**Response:** status only.

### RSI_READ_KEY (0x11)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |

**Response payload (success):**

| Size | Field |
|---|---|
| 4 | status |
| 4+N | name |
| 16 | parent_guid |
| 4+N | sd |
| 1 | volatile |
| 1 | symlink |
| 8 | last_write_time |

### RSI_WRITE_KEY (0x12)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4 | field_mask |
| (conditional) | fields per mask |

Field mask bits:

| Bit | Field | Size |
|---|---|---|
| 0 | sd | 4+N (length-prefixed) |
| 1 | last_write_time | 8 |

Only fields with their mask bit set are present in the payload,
in bit order.

**Response:** status only.

### RSI_DROP_KEY (0x13)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |

**Response:** status only.

## Value operations

### RSI_QUERY_VALUES (0x20)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | value_name (empty + flag for query-all) |
| 1 | query_all (1 = return all values for key) |

**Response payload (success):**

| Size | Field |
|---|---|
| 4 | status |
| 4 | entry_count |

Per entry:

| Size | Field |
|---|---|
| 4+N | value_name |
| 4+N | layer_name |
| 4 | type |
| 4+N | data (length-prefixed) |
| 8 | sequence |

Followed by blanket tombstone data:

| Size | Field |
|---|---|
| 4 | blanket_count |

Per blanket:

| Size | Field |
|---|---|
| 4+N | layer_name |
| 8 | sequence |

### RSI_SET_VALUE (0x21)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | value_name |
| 4+N | layer_name |
| 4 | type |
| 4+N | data |
| 8 | sequence |
| 8 | expected_sequence (0 = no CAS) |

**Response:** status only (RSI_CAS_FAILED if condition fails).

### RSI_DELETE_VALUE_ENTRY (0x22)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | value_name |
| 4+N | layer_name |

**Response:** status only.

### RSI_SET_BLANKET_TOMBSTONE (0x23)

**Request payload:**

| Size | Field |
|---|---|
| 16 | guid |
| 4+N | layer_name |
| 1 | set (1 = write, 0 = remove) |
| 8 | sequence |

**Response:** status only.

## Transaction operations

### RSI_BEGIN_TRANSACTION (0x30)

**Request payload:**

| Size | Field |
|---|---|
| 8 | txn_id |

**Response:** status only.

### RSI_COMMIT_TRANSACTION (0x31)

**Request payload:**

| Size | Field |
|---|---|
| 8 | txn_id |

**Response:** status only.

### RSI_ABORT_TRANSACTION (0x32)

**Request payload:**

| Size | Field |
|---|---|
| 8 | txn_id |

**Response:** status only.

## Layer operations

### RSI_DELETE_LAYER (0x50)

**Request payload:**

| Size | Field |
|---|---|
| 4+N | layer_name |

**Response payload (success):**

| Size | Field |
|---|---|
| 4 | status |
| 4 | orphaned_guid_count |

Per orphaned GUID:

| Size | Field |
|---|---|
| 16 | guid |

## Maintenance operations

### RSI_FLUSH (0x40)

**Request payload:**

| Size | Field |
|---|---|
| 4+N | hive_name (length-prefixed string) |

The hive name identifies which hive to flush. This is the only RSI
operation that routes by hive name rather than key GUID, because
flush is a hive-level operation (WAL checkpoint), not a key-level
one.

**Response:** status only.
