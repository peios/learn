---
title: Struct Layouts
order: 2
---

Byte-level layouts for all structures crossing the kernel/userspace
boundary. All multi-byte integers are little-endian. All structs are
**packed** -- fields are placed at the exact offsets shown with no
implicit padding. GUIDs are 16 bytes, stored as raw bytes (not a
struct of fields).

An independent implementer can write compatible userspace code from
this page.

Strings in ioctl structs are **length-delimited**, not
null-terminated. Each string is referenced by a `(len, ptr)` pair
where `len` is the byte count and `ptr` is a userspace pointer.
LCS reads exactly `len` bytes from `ptr`. Null terminators are
neither required nor expected.

## Ioctl argument structs

### reg_query_value_args (REG_IOC_QUERY_VALUE)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | name_len | Length of value name in bytes. |
| 4 | 8 | name_ptr | Pointer to value name (userspace). |
| 12 | 4 | type | Output: value type (uint32). |
| 16 | 4 | data_len | Input: buffer size. Output: actual data size. |
| 20 | 4 | txn_fd | Transaction fd (-1 if none). |
| 24 | 8 | data_ptr | Pointer to data buffer (userspace). |
| 32 | 8 | sequence | Output: sequence number of the effective entry. Used as expected_sequence in conditional writes to the same layer. |
| 40 | 4 | layer_len | Output: length of effective layer name. |
| 44 | 8 | layer_ptr | Input: pointer to buffer for layer name. |
| 52 | 4 | layer_buf_len | Input: buffer size for layer name. |

Total: 56 bytes.

If data_len on input is too small, the ioctl returns ERANGE and
sets data_len to the required size. The caller retries with a
larger buffer.

### reg_set_value_args (REG_IOC_SET_VALUE)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | name_len | Length of value name in bytes. |
| 4 | 8 | name_ptr | Pointer to value name. |
| 12 | 4 | type | Value type (uint32). REG_TOMBSTONE for tombstones. |
| 16 | 4 | data_len | Length of data in bytes. |
| 20 | 8 | data_ptr | Pointer to data. |
| 28 | 4 | layer_len | Length of layer name (0 for base layer). |
| 32 | 8 | layer_ptr | Pointer to layer name (null for base layer). |
| 40 | 4 | txn_fd | Transaction fd (-1 if none). |
| 44 | 4 | _pad | Reserved. |
| 48 | 8 | expected_seq | Expected sequence for CAS (0 to disable). |

Total: 56 bytes.

### reg_delete_value_args (REG_IOC_DELETE_VALUE)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | name_len | Length of value name in bytes. |
| 4 | 8 | name_ptr | Pointer to value name. |
| 12 | 4 | layer_len | Length of layer name. |
| 16 | 8 | layer_ptr | Pointer to layer name. |
| 24 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 28 bytes.

### reg_blanket_tombstone_args (REG_IOC_BLANKET_TOMBSTONE)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | layer_len | Length of layer name. |
| 4 | 8 | layer_ptr | Pointer to layer name. |
| 12 | 1 | set | 1 to write blanket, 0 to remove. |
| 13 | 3 | _pad | Reserved. |
| 16 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 20 bytes.

### reg_query_values_batch_args (REG_IOC_QUERY_VALUES_BATCH)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | buf_len | Input: buffer size. Output: bytes written. |
| 4 | 4 | count | Output: number of values returned. |
| 8 | 8 | buf_ptr | Pointer to output buffer. |
| 16 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 20 bytes.

Each value in the buffer is packed as:

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | name_len |
| 4 | name_len | name (UTF-8) |
| 4+name_len | 4 | type |
| 8+name_len | 4 | data_len |
| 12+name_len | data_len | data |

Values are packed consecutively with no padding between them. If
the buffer is too small, the ioctl returns ERANGE and sets buf_len
to the required size.

### reg_enum_value_args (REG_IOC_ENUM_VALUES)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | index | Value index (0-based). |
| 4 | 4 | name_len | Input: buffer size. Output: actual name length. |
| 8 | 8 | name_ptr | Pointer to name buffer. |
| 16 | 4 | type | Output: value type. |
| 20 | 4 | data_len | Input: buffer size. Output: actual data size. |
| 24 | 8 | data_ptr | Pointer to data buffer. |
| 32 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 36 bytes.

### reg_enum_subkey_args (REG_IOC_ENUM_SUBKEYS)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | index | Subkey index (0-based). |
| 4 | 4 | name_len | Input: buffer size. Output: actual name length. |
| 8 | 8 | name_ptr | Pointer to name buffer. |
| 16 | 8 | last_write_time | Output: last modification (Unix ns). |
| 24 | 4 | subkey_count | Output: number of child keys. |
| 28 | 4 | value_count | Output: number of values. |
| 32 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 36 bytes.

### reg_query_key_info_args (REG_IOC_QUERY_KEY_INFO)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | name_len | Input: buffer size. Output: actual name length. |
| 4 | 8 | name_ptr | Pointer to name buffer. |
| 12 | 8 | last_write_time | Output: Unix nanoseconds. |
| 20 | 4 | subkey_count | Output. |
| 24 | 4 | value_count | Output. |
| 28 | 4 | max_subkey_name_len | Output: bytes. |
| 32 | 4 | max_value_name_len | Output: bytes. |
| 36 | 4 | max_value_data_size | Output: bytes. |
| 40 | 4 | sd_size | Output: bytes. |
| 44 | 1 | volatile | Output: 1 if volatile. |
| 45 | 1 | symlink | Output: 1 if symlink. |
| 46 | 2 | _pad | Reserved. |
| 48 | 8 | hive_generation | Output: hive generation number. |

Total: 56 bytes.

### reg_delete_key_args (REG_IOC_DELETE_KEY)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | layer_len | Length of layer name. |
| 4 | 8 | layer_ptr | Pointer to layer name. |
| 12 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 16 bytes.

### reg_hide_key_args (REG_IOC_HIDE_KEY)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | layer_len | Length of layer name. |
| 4 | 8 | layer_ptr | Pointer to layer name. |
| 12 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 16 bytes.

### reg_get_security_args (REG_IOC_GET_SECURITY)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | security_info | Flags: which SD components to return. |
| 4 | 4 | sd_len | Input: buffer size. Output: actual SD size. |
| 8 | 8 | sd_ptr | Pointer to SD buffer. |

Total: 16 bytes.

### reg_set_security_args (REG_IOC_SET_SECURITY)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | security_info | Flags: which components to set. |
| 4 | 4 | sd_len | Length of SD data. |
| 8 | 8 | sd_ptr | Pointer to SD data in KACS binary format. |
| 16 | 4 | txn_fd | Transaction fd (-1 if none). |

Total: 20 bytes.

### reg_notify_args (REG_IOC_NOTIFY)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | filter | Bitmask: REG_NOTIFY_VALUE, _SUBKEY, _SD. |
| 4 | 1 | subtree | 1 for subtree watch, 0 for direct. |
| 5 | 3 | _pad | Reserved. |

Total: 8 bytes.

### reg_backup_args (REG_IOC_BACKUP)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | output_fd | Writable fd to write backup stream to. |

Total: 4 bytes.

### reg_restore_args (REG_IOC_RESTORE)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | input_fd | Readable fd to read backup stream from. |

Total: 4 bytes.

## Security information flags

Used in reg_get_security_args and reg_set_security_args:

| Flag | Value | Description |
|---|---|---|
| OWNER_SECURITY_INFORMATION | 0x01 | Owner SID. |
| GROUP_SECURITY_INFORMATION | 0x02 | Group SID. |
| DACL_SECURITY_INFORMATION | 0x04 | Discretionary ACL. |
| SACL_SECURITY_INFORMATION | 0x08 | System ACL. |

## Watch event structures

### Direct watch event

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | total_len | Total event size in bytes. |
| 4 | 2 | event_type | Event type code. |
| 6 | 2 | name_len | Length of name in bytes (0 for no-name events). |
| 8 | name_len | name | Changed entity name (UTF-8). |

Minimum size: 8 bytes (no name).

### Subtree watch event

Extends the direct event with path components:

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | total_len | Total event size. |
| 4 | 2 | event_type | Event type code. |
| 6 | 2 | name_len | Length of name. |
| 8 | name_len | name | Changed entity name. |
| 8+name_len | 2 | path_depth | Components from watched key to changed key. |
| 10+name_len | variable | path_components | Sequence of (len:uint16, UTF-8 bytes). |

path_depth of 0 means the change is on the watched key itself
(equivalent to a direct event). Consumers distinguish direct from
subtree events by checking whether bytes remain after the name
field (using total_len).

## RSI registration struct

### reg_src_register_args (REG_SRC_REGISTER ioctl)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | hive_count | Number of hives to register. |
| 4 | 8 | max_sequence | Highest persisted sequence number. |
| 12 | 8 | hives_ptr | Pointer to array of reg_src_hive_entry. |

Total: 20 bytes.

### reg_src_hive_entry

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | name_len | Length of hive name. |
| 4 | 8 | name_ptr | Pointer to hive name string. |
| 12 | 16 | root_guid | Root key GUID. |
| 28 | 4 | flags | RSI_HIVE_PRIVATE (0x01) if private. |
| 32 | 16 | scope_guid | Scope GUID (only if PRIVATE flag set, zeroed otherwise). |

Total: 48 bytes per entry.
