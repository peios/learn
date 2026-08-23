---
title: LCS ABI Reference
description: Every LCS syscall number, ioctl, structure layout and constant, generated from the uapi headers and measured by compilation.
---

Every name, value, offset and size in this appendix is generated from
`pkm/uapi/pkm/lcs.h` by `pkm/tools/gen-lcs-abi.py`, with ioctl
encodings and struct layouts measured by compiling a probe against the
real header. Regenerate it whenever the ABI changes; do not edit it by
hand. The names here are the ones a program actually compiles against.

## Syscall numbers

Signatures are read from the `SYSCALL_DEFINE` sites in `pkm/lcs/`.

| Number | Constant | Signature |
|---|---|---|
| 1100 | `SYS_REG_OPEN_KEY` | `reg_open_key(int parent_fd, const char __user *path, u32 desired_access, u32 flags)` |
| 1101 | `SYS_REG_CREATE_KEY` | `reg_create_key(const struct reg_create_key_args __user *args)` |
| 1102 | `SYS_REG_BEGIN_TRANSACTION` | `reg_begin_transaction(void)` |

## Ioctls

The type byte is `'R'`. Ioctl number namespaces are per fd type, so
`REG_SRC_REGISTER` (number 0 on the source device) and
`REG_IOC_QUERY_VALUE` (number 0 on a key fd) do not collide: the
kernel dispatches on the fd's `file_operations`, not globally. The
encoded value is what `_IOC` produces from the direction, type byte,
number and argument size.

*Source device fd.*

| Ioctl | Number | Direction | Argument | Arg size | Encoded |
|---|---|---|---|---|---|
| `REG_SRC_REGISTER` | 0 | _IOW | `struct reg_src_register_args` | 24 | `0x40185200` |

*Key fd.*

| Ioctl | Number | Direction | Argument | Arg size | Encoded |
|---|---|---|---|---|---|
| `REG_IOC_QUERY_VALUE` | 0 | _IOWR | `struct reg_query_value_args` | 64 | `0xC0405200` |
| `REG_IOC_SET_VALUE` | 1 | _IOW | `struct reg_set_value_args` | 64 | `0x40405201` |
| `REG_IOC_DELETE_VALUE` | 2 | _IOW | `struct reg_delete_value_args` | 40 | `0x40285202` |
| `REG_IOC_BLANKET_TOMBSTONE` | 3 | _IOW | `struct reg_blanket_tombstone_args` | 24 | `0x40185203` |
| `REG_IOC_QUERY_VALUES_BATCH` | 4 | _IOWR | `struct reg_query_values_batch_args` | 24 | `0xC0185204` |
| `REG_IOC_ENUM_VALUES` | 5 | _IOWR | `struct reg_enum_value_args` | 40 | `0xC0285205` |
| `REG_IOC_ENUM_SUBKEYS` | 6 | _IOWR | `struct reg_enum_subkey_args` | 40 | `0xC0285206` |
| `REG_IOC_QUERY_KEY_INFO` | 7 | _IOR | `struct reg_query_key_info_args` | 64 | `0x80405207` |
| `REG_IOC_DELETE_KEY` | 8 | _IOW | `struct reg_delete_key_args` | 24 | `0x40185208` |
| `REG_IOC_HIDE_KEY` | 9 | _IOW | `struct reg_hide_key_args` | 24 | `0x40185209` |
| `REG_IOC_GET_SECURITY` | 10 | _IOWR | `struct reg_get_security_args` | 16 | `0xC010520A` |
| `REG_IOC_SET_SECURITY` | 11 | _IOW | `struct reg_set_security_args` | 24 | `0x4018520B` |
| `REG_IOC_NOTIFY` | 12 | _IOW | `struct reg_notify_args` | 8 | `0x4008520C` |
| `REG_IOC_FLUSH` | 13 | _IO | none | 0 | `0x0000520D` |
| `REG_IOC_BACKUP` | 14 | _IOW | `struct reg_backup_args` | 4 | `0x4004520E` |
| `REG_IOC_RESTORE` | 15 | _IOW | `struct reg_restore_args` | 4 | `0x4004520F` |

*Transaction fd.*

| Ioctl | Number | Direction | Argument | Arg size | Encoded |
|---|---|---|---|---|---|
| `REG_IOC_COMMIT` | 16 | _IO | none | 0 | `0x00005210` |
| `REG_IOC_TXN_STATUS` | 17 | _IOR | `struct reg_txn_status_args` | 8 | `0x80085211` |

## Structure layouts

Offsets and sizes are measured, not declared. The header also defines
a `_SIZE` constant for each of these structures; the two agree by
construction, and a mismatch fails the build in `uapi/smoke_test.c`.

### `struct reg_create_key_args`

Total size 48 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__s32` | `parent_fd` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `path_ptr` |
| 16 | 4 | `__u32` | `desired_access` |
| 20 | 4 | `__u32` | `flags` |
| 24 | 8 | `__u64` | `layer_ptr` |
| 32 | 4 | `__s32` | `txn_fd` |
| 36 | 4 | `__u32` | `_pad1` |
| 40 | 8 | `__u64` | `disposition_ptr` |

### `struct reg_query_value_args`

Total size 64 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `name_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 4 | `__u32` | `type` |
| 20 | 4 | `__u32` | `data_len` |
| 24 | 4 | `__s32` | `txn_fd` |
| 28 | 4 | `__u32` | `layer_buf_len` |
| 32 | 8 | `__u64` | `data_ptr` |
| 40 | 8 | `__u64` | `sequence` |
| 48 | 4 | `__u32` | `layer_len` |
| 52 | 4 | `__u32` | `_pad1` |
| 56 | 8 | `__u64` | `layer_ptr` |

### `struct reg_set_value_args`

Total size 64 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `name_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 4 | `__u32` | `type` |
| 20 | 4 | `__u32` | `data_len` |
| 24 | 8 | `__u64` | `data_ptr` |
| 32 | 4 | `__u32` | `layer_len` |
| 36 | 4 | `__u32` | `_pad1` |
| 40 | 8 | `__u64` | `layer_ptr` |
| 48 | 4 | `__s32` | `txn_fd` |
| 52 | 4 | `__u32` | `_pad2` |
| 56 | 8 | `__u64` | `expected_seq` |

### `struct reg_delete_value_args`

Total size 40 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `name_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 4 | `__u32` | `layer_len` |
| 20 | 4 | `__u32` | `_pad1` |
| 24 | 8 | `__u64` | `layer_ptr` |
| 32 | 4 | `__s32` | `txn_fd` |
| 36 | 4 | `__u32` | `_pad2` |

### `struct reg_blanket_tombstone_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `layer_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `layer_ptr` |
| 16 | 1 | `__u8` | `set` |
| 17 | 3 | `__u8``[3]` | `_pad1` |
| 20 | 4 | `__s32` | `txn_fd` |

### `struct reg_query_values_batch_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `buf_len` |
| 4 | 4 | `__u32` | `count` |
| 8 | 8 | `__u64` | `buf_ptr` |
| 16 | 4 | `__s32` | `txn_fd` |
| 20 | 4 | `__u32` | `_pad` |

### `struct reg_enum_value_args`

Total size 40 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `index` |
| 4 | 4 | `__u32` | `name_len` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 4 | `__u32` | `type` |
| 20 | 4 | `__u32` | `data_len` |
| 24 | 8 | `__u64` | `data_ptr` |
| 32 | 4 | `__s32` | `txn_fd` |
| 36 | 4 | `__u32` | `_pad` |

### `struct reg_enum_subkey_args`

Total size 40 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `index` |
| 4 | 4 | `__u32` | `name_len` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 8 | `__u64` | `last_write_time` |
| 24 | 4 | `__u32` | `subkey_count` |
| 28 | 4 | `__u32` | `value_count` |
| 32 | 4 | `__s32` | `txn_fd` |
| 36 | 4 | `__u32` | `_pad` |

### `struct reg_query_key_info_args`

Total size 64 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `name_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 8 | `__u64` | `last_write_time` |
| 24 | 4 | `__u32` | `subkey_count` |
| 28 | 4 | `__u32` | `value_count` |
| 32 | 4 | `__u32` | `max_subkey_name_len` |
| 36 | 4 | `__u32` | `max_value_name_len` |
| 40 | 4 | `__u32` | `max_value_data_size` |
| 44 | 4 | `__u32` | `sd_size` |
| 48 | 1 | `__u8` | `volatile_key` |
| 49 | 1 | `__u8` | `symlink` |
| 50 | 6 | `__u8``[6]` | `_pad1` |
| 56 | 8 | `__u64` | `hive_generation` |

### `struct reg_delete_key_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `layer_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `layer_ptr` |
| 16 | 4 | `__s32` | `txn_fd` |
| 20 | 4 | `__u32` | `_pad1` |

### `struct reg_hide_key_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `layer_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `layer_ptr` |
| 16 | 4 | `__s32` | `txn_fd` |
| 20 | 4 | `__u32` | `_pad1` |

### `struct reg_get_security_args`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `security_info` |
| 4 | 4 | `__u32` | `sd_len` |
| 8 | 8 | `__u64` | `sd_ptr` |

### `struct reg_set_security_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `security_info` |
| 4 | 4 | `__u32` | `sd_len` |
| 8 | 8 | `__u64` | `sd_ptr` |
| 16 | 4 | `__s32` | `txn_fd` |
| 20 | 4 | `__u32` | `_pad` |

### `struct reg_notify_args`

Total size 8 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `filter` |
| 4 | 1 | `__u8` | `subtree` |
| 5 | 3 | `__u8``[3]` | `_pad` |

### `struct reg_backup_args`

Total size 4 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__s32` | `output_fd` |

### `struct reg_restore_args`

Total size 4 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__s32` | `input_fd` |

### `struct reg_txn_status_args`

Total size 8 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `state` |
| 4 | 4 | `__s32` | `terminal_errno` |

### `struct reg_src_register_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `hive_count` |
| 4 | 4 | `__u32` | `_pad` |
| 8 | 8 | `__u64` | `max_sequence` |
| 16 | 8 | `__u64` | `hives_ptr` |

### `struct reg_src_hive_entry`

Total size 56 bytes.

| Offset | Size | Type | Field |
|---|---|---|---|
| 0 | 4 | `__u32` | `name_len` |
| 4 | 4 | `__u32` | `_pad0` |
| 8 | 8 | `__u64` | `name_ptr` |
| 16 | 16 | `__u8``[16]` | `root_guid` |
| 32 | 4 | `__u32` | `flags` |
| 36 | 4 | `__u32` | `_pad1` |
| 40 | 16 | `__u8``[16]` | `scope_guid` |

## Constants

Grouped as the header groups them.

*Syscall and ioctl argument sizes.*

| Constant | Value |
|---|---|
| `REG_CREATE_KEY_ARGS_SIZE` | `48` |
| `REG_QUERY_VALUE_ARGS_SIZE` | `64` |
| `REG_SET_VALUE_ARGS_SIZE` | `64` |
| `REG_DELETE_VALUE_ARGS_SIZE` | `40` |
| `REG_BLANKET_TOMBSTONE_ARGS_SIZE` | `24` |
| `REG_QUERY_VALUES_BATCH_ARGS_SIZE` | `24` |
| `REG_ENUM_VALUE_ARGS_SIZE` | `40` |
| `REG_ENUM_SUBKEY_ARGS_SIZE` | `40` |
| `REG_QUERY_KEY_INFO_ARGS_SIZE` | `64` |
| `REG_DELETE_KEY_ARGS_SIZE` | `24` |
| `REG_HIDE_KEY_ARGS_SIZE` | `24` |
| `REG_GET_SECURITY_ARGS_SIZE` | `16` |
| `REG_SET_SECURITY_ARGS_SIZE` | `24` |
| `REG_NOTIFY_ARGS_SIZE` | `8` |
| `REG_BACKUP_ARGS_SIZE` | `4` |
| `REG_RESTORE_ARGS_SIZE` | `4` |
| `REG_TXN_STATUS_ARGS_SIZE` | `8` |
| `REG_SRC_REGISTER_ARGS_SIZE` | `24` |
| `REG_SRC_HIVE_ENTRY_SIZE` | `56` |

*Transaction state codes.*

| Constant | Value |
|---|---|
| `REG_TXN_ACTIVE_UNBOUND` | `0` |
| `REG_TXN_ACTIVE_BOUND` | `1` |
| `REG_TXN_COMMITTED` | `2` |
| `REG_TXN_ABORTED` | `3` |
| `REG_TXN_TIMED_OUT` | `4` |
| `REG_TXN_SOURCE_DOWN` | `5` |

*Syscall flags and dispositions.*

| Constant | Value |
|---|---|
| `REG_OPEN_LINK` | `0x01` |
| `REG_OPTION_VOLATILE` | `0x01` |
| `REG_OPTION_CREATE_LINK` | `0x02` |
| `REG_CREATED_NEW` | `1` |
| `REG_OPENED_EXISTING` | `2` |

*Registry key access rights.*

| Constant | Value |
|---|---|
| `KEY_QUERY_VALUE` | `0x00000001` |
| `KEY_SET_VALUE` | `0x00000002` |
| `KEY_CREATE_SUB_KEY` | `0x00000004` |
| `KEY_ENUMERATE_SUB_KEYS` | `0x00000008` |
| `KEY_NOTIFY` | `0x00000010` |
| `KEY_CREATE_LINK` | `0x00000020` |
| `DELETE` | `0x00010000` |
| `READ_CONTROL` | `0x00020000` |
| `WRITE_DAC` | `0x00040000` |
| `WRITE_OWNER` | `0x00080000` |
| `ACCESS_SYSTEM_SECURITY` | `0x01000000` |
| `MAXIMUM_ALLOWED` | `0x02000000` |
| `GENERIC_ALL` | `0x10000000` |
| `GENERIC_EXECUTE` | `0x20000000` |
| `GENERIC_WRITE` | `0x40000000` |
| `GENERIC_READ` | `0x80000000` |
| `KEY_READ` | `0x00020019` |
| `KEY_WRITE` | `0x00020006` |
| `KEY_ALL_ACCESS` | `0x000F003F` |
| `REG_VALID_DESIRED_ACCESS_MASK` | `0xF30F003F` |
| `REG_VALID_MAPPED_ACCESS_MASK` | `0x010F003F` |
| `REG_VALID_ACE_ACCESS_MASK` | `0xF10F003F` |

*Security information flags for REG_IOC_GET_SECURITY / SET_SECURITY.*

| Constant | Value |
|---|---|
| `OWNER_SECURITY_INFORMATION` | `0x00000001` |
| `GROUP_SECURITY_INFORMATION` | `0x00000002` |
| `DACL_SECURITY_INFORMATION` | `0x00000004` |
| `SACL_SECURITY_INFORMATION` | `0x00000008` |
| `REG_VALID_SECURITY_INFORMATION` | `0x0000000F` |

*Registry value types.*

| Constant | Value |
|---|---|
| `REG_NONE` | `0` |
| `REG_SZ` | `1` |
| `REG_EXPAND_SZ` | `2` |
| `REG_BINARY` | `3` |
| `REG_DWORD` | `4` |
| `REG_DWORD_BIG_ENDIAN` | `5` |
| `REG_LINK` | `6` |
| `REG_MULTI_SZ` | `7` |
| `REG_RESOURCE_LIST` | `8` |
| `REG_FULL_RESOURCE_DESCRIPTOR` | `9` |
| `REG_RESOURCE_REQUIREMENTS_LIST` | `10` |
| `REG_QWORD` | `11` |
| `REG_TOMBSTONE` | `0xFFFF` |

*Watch event types and filters.*

| Constant | Value |
|---|---|
| `REG_WATCH_VALUE_SET` | `1` |
| `REG_WATCH_VALUE_DELETED` | `2` |
| `REG_WATCH_SUBKEY_CREATED` | `3` |
| `REG_WATCH_SUBKEY_DELETED` | `4` |
| `REG_WATCH_SD_CHANGED` | `5` |
| `REG_WATCH_KEY_DELETED` | `6` |
| `REG_WATCH_OVERFLOW` | `7` |

*Watch event raw byte layout.*

| Constant | Value |
|---|---|
| `REG_WATCH_EVENT_TOTAL_LEN_OFFSET` | `0` |
| `REG_WATCH_EVENT_TYPE_OFFSET` | `4` |
| `REG_WATCH_EVENT_NAME_LEN_OFFSET` | `6` |
| `REG_WATCH_EVENT_NAME_OFFSET` | `8` |
| `REG_WATCH_EVENT_MIN_SIZE` | `8` |
| `REG_WATCH_SUBTREE_PATH_DEPTH_REL_OFFSET` | `0` |
| `REG_WATCH_SUBTREE_PATH_DEPTH_SIZE` | `2` |
| `REG_WATCH_SUBTREE_PATH_COMPONENTS_REL_OFFSET` | `2` |
| `REG_WATCH_PATH_COMPONENT_LEN_SIZE` | `2` |
| `REG_NOTIFY_VALUE` | `0x01` |
| `REG_NOTIFY_SUBKEY` | `0x02` |
| `REG_NOTIFY_SD` | `0x04` |
| `REG_NOTIFY_ALL` | `0x07` |

*RSI common wire layout.*

| Constant | Value |
|---|---|
| `RSI_REQUEST_TOTAL_LEN_OFFSET` | `0` |
| `RSI_REQUEST_ID_OFFSET` | `4` |
| `RSI_REQUEST_OP_CODE_OFFSET` | `12` |
| `RSI_REQUEST_TXN_ID_OFFSET` | `14` |
| `RSI_REQUEST_HEADER_SIZE` | `22` |
| `RSI_RESPONSE_TOTAL_LEN_OFFSET` | `0` |
| `RSI_RESPONSE_ID_OFFSET` | `4` |
| `RSI_RESPONSE_OP_CODE_OFFSET` | `12` |
| `RSI_RESPONSE_HEADER_SIZE` | `14` |
| `RSI_RESPONSE_STATUS_OFFSET` | `14` |
| `RSI_STATUS_SIZE` | `4` |
| `RSI_MIN_RESPONSE_SIZE` | `18` |
| `RSI_LENGTH_PREFIX_SIZE` | `4` |
| `RSI_GUID_SIZE` | `16` |
| `RSI_RESPONSE_BIT` | `0x8000` |

*RSI op codes and response op codes.*

| Constant | Value |
|---|---|
| `RSI_LOOKUP` | `0x0001` |
| `RSI_CREATE_ENTRY` | `0x0002` |
| `RSI_HIDE_ENTRY` | `0x0003` |
| `RSI_DELETE_ENTRY` | `0x0004` |
| `RSI_ENUM_CHILDREN` | `0x0005` |
| `RSI_CREATE_KEY` | `0x0010` |
| `RSI_READ_KEY` | `0x0011` |
| `RSI_WRITE_KEY` | `0x0012` |
| `RSI_DROP_KEY` | `0x0013` |
| `RSI_QUERY_VALUES` | `0x0020` |
| `RSI_SET_VALUE` | `0x0021` |
| `RSI_DELETE_VALUE_ENTRY` | `0x0022` |
| `RSI_SET_BLANKET_TOMBSTONE` | `0x0023` |
| `RSI_BEGIN_TRANSACTION` | `0x0030` |
| `RSI_COMMIT_TRANSACTION` | `0x0031` |
| `RSI_ABORT_TRANSACTION` | `0x0032` |
| `RSI_FLUSH` | `0x0040` |
| `RSI_DELETE_LAYER` | `0x0050` |
| `RSI_LOOKUP_RESPONSE` | `0x8001` |
| `RSI_CREATE_ENTRY_RESPONSE` | `0x8002` |
| `RSI_HIDE_ENTRY_RESPONSE` | `0x8003` |
| `RSI_DELETE_ENTRY_RESPONSE` | `0x8004` |
| `RSI_ENUM_CHILDREN_RESPONSE` | `0x8005` |
| `RSI_CREATE_KEY_RESPONSE` | `0x8010` |
| `RSI_READ_KEY_RESPONSE` | `0x8011` |
| `RSI_WRITE_KEY_RESPONSE` | `0x8012` |
| `RSI_DROP_KEY_RESPONSE` | `0x8013` |
| `RSI_QUERY_VALUES_RESPONSE` | `0x8020` |
| `RSI_SET_VALUE_RESPONSE` | `0x8021` |
| `RSI_DELETE_VALUE_ENTRY_RESPONSE` | `0x8022` |
| `RSI_SET_BLANKET_TOMBSTONE_RESPONSE` | `0x8023` |
| `RSI_BEGIN_TRANSACTION_RESPONSE` | `0x8030` |
| `RSI_COMMIT_TRANSACTION_RESPONSE` | `0x8031` |
| `RSI_ABORT_TRANSACTION_RESPONSE` | `0x8032` |
| `RSI_FLUSH_RESPONSE` | `0x8040` |
| `RSI_DELETE_LAYER_RESPONSE` | `0x8050` |

*RSI status codes.*

| Constant | Value |
|---|---|
| `RSI_OK` | `0` |
| `RSI_NOT_FOUND` | `1` |
| `RSI_ALREADY_EXISTS` | `2` |
| `RSI_STORAGE_ERROR` | `3` |
| `RSI_NOT_EMPTY` | `4` |
| `RSI_TOO_LARGE` | `5` |
| `RSI_TXN_BUSY` | `6` |
| `RSI_INVALID` | `7` |
| `RSI_CAS_FAILED` | `8` |
| `RSI_TXN_NOT_SUPPORTED` | `9` |

*RSI path target types.*

| Constant | Value |
|---|---|
| `RSI_PATH_TARGET_GUID` | `0` |
| `RSI_PATH_TARGET_HIDDEN` | `1` |

*RSI_WRITE_KEY field mask bits.*

| Constant | Value |
|---|---|
| `RSI_WRITE_KEY_FIELD_SD` | `0x01` |
| `RSI_WRITE_KEY_FIELD_LAST_WRITE_TIME` | `0x02` |
| `RSI_WRITE_KEY_FIELD_KNOWN_MASK` | `0x00000003` |

*RSI transaction modes and source-registration flags.*

| Constant | Value |
|---|---|
| `RSI_TXN_READ_WRITE` | `0` |
| `RSI_TXN_READ_ONLY` | `1` |
| `RSI_HIVE_PRIVATE` | `0x01` |

*Backup record types and magic.*

| Constant | Value |
|---|---|
| `REG_BACKUP_HEADER` | `0x01` |
| `REG_BACKUP_LAYER` | `0x02` |
| `REG_BACKUP_KEY` | `0x03` |
| `REG_BACKUP_PATH_ENTRY` | `0x04` |
| `REG_BACKUP_VALUE` | `0x05` |
| `REG_BACKUP_BLANKET_TOMBSTONE` | `0x06` |
| `REG_BACKUP_TRAILER` | `0xFF` |
| `REG_BACKUP_MAGIC` | `"PEIOSREG"` |

## What is not here

The header carries names, numbers and layouts. Everything else about the
interface is a property of the implementation rather than of the ABI, and
is documented with the operation it belongs to: the required access right
for each ioctl and the two-pass output buffer convention in §5.6, the
error vocabulary in §5.6.4, the RSI payload shapes in the Registry Source
Interface specification, and the backup stream's record payloads in the
Registry Backup Format specification.

`REG_BACKUP_MAGIC` above is the eight-byte header magic; the record type
codes are the framing, not the payloads.

## Build configuration

LCS is built by `CONFIG_SECURITY_PKM`, a boolean option, so it is linked
into `vmlinux` rather than loaded. `CONFIG_RUST=y` is required: the
resolution core, the RSI codec, the backup serialiser and the transaction
log are Rust, staged into the kernel tree as `security/pkm/lcs/lcs_core`.
`CONFIG_SECURITY_PKM_KUNIT` compiles in the in-kernel test harness.

The three syscall numbers are added to the syscall table by
`kernel/patches/arch/syscall-table-pkm.patch`, which patches both
`arch/x86/entry/syscalls/syscall_64.tbl` and the copy of it that ships
under `tools/perf/`. They are registered `common`, so they are reachable
from the x32 ABI as well as from x86-64.
