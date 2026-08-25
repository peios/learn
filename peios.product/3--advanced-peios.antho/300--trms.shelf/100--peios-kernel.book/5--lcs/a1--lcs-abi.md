---
title: LCS ABI Reference
description: Every LCS syscall number, ioctl, structure layout and constant, generated from the uapi headers and measured by compilation.
---

Every name, value, offset and size in this appendix is generated from
`pkm/uapi/pkm/lcs.h` by `pkm/tools/gen-lcs-abi.py`, with ioctl
encodings and struct layouts measured by compiling a probe against the
real header. Regenerate it whenever the ABI changes; do not edit it by
hand. The names here are the ones a program actually compiles against.

What a compiler cannot measure -- which properties belong with their
operations rather than here, and the kernel configuration -- is in the
notes appendix, §5.B, which this generator does not touch.

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
| `REG_IOC_QUERY_KEY_INFO` | 7 | _IOWR | `struct reg_query_key_info_args` | 64 | `0xC0405207` |
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

*_IOWR, not _IOR: the kernel reads the caller's name_len and name_ptr out of the argument struct before it writes the result back, so the argument crosses in both directions. It was declared _IOR, which put the wrong direction bits in the encoded number -- and since the kernel dispatches on the whole encoded value, correcting it is a wire break, not a relabelling.*

| Constant | Value |
|---|---|
| `REG_IOC_QUERY_KEY_INFO` | `0xC0405207` |
| `REG_IOC_DELETE_KEY` | `0x40185208` |
| `REG_IOC_HIDE_KEY` | `0x40185209` |
| `REG_IOC_GET_SECURITY` | `0xC010520A` |
| `REG_IOC_SET_SECURITY` | `0x4018520B` |
| `REG_IOC_NOTIFY` | `0x4008520C` |
| `REG_IOC_FLUSH` | `0x0000520D` |
| `REG_IOC_BACKUP` | `0x4004520E` |
| `REG_IOC_RESTORE` | `0x4004520F` |

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

## Tracepoint diagnostic codes

From `uapi/pkm/trace.h`. These are a diagnostic contract for
ftrace, perf and eBPF consumers, letting a tool decode an `lcs:`
event's `reason`, `op` or `state` field without recompiling
against a specific kernel. No LCS syscall accepts or returns
them, and values are append-only.

lcs_rsi_request op — which of the 18 RSI dispatch verbs a source-side
request admission record describes. Emitted by lcs:lcs_rsi_request on
successful queue admission and on the admission error rungs; the rung is
read from `ret` (0 == enqueued, -EAGAIN == in-flight at limit /
backpressure, -EIO == source gone / fd closing, -EOVERFLOW == request-id
space exhausted, other == build reject). The same op enum tags the
round-trip begin marker (lcs_rsi_roundtrip). Never records a pathname,
key name, GUID, or frame bytes — only this op code, ids, counts and ret.

| Constant | Value | Notes |
|---|---|---|
| `LCS_OP_LOOKUP` | `0` | RSI_LOOKUP |
| `LCS_OP_READ_KEY` | `1` | RSI_READ_KEY |
| `LCS_OP_ENUM_CHILDREN` | `2` | RSI_ENUM_CHILDREN |
| `LCS_OP_QUERY_VALUES` | `3` | RSI_QUERY_VALUES |
| `LCS_OP_SET_VALUE` | `4` | RSI_SET_VALUE |
| `LCS_OP_DELETE_VALUE` | `5` | RSI_DELETE_VALUE_ENTRY |
| `LCS_OP_BLANKET_TOMBSTONE` | `6` | RSI_SET_BLANKET_TOMBSTONE |
| `LCS_OP_DROP_KEY` | `7` | RSI_DROP_KEY |
| `LCS_OP_CREATE_ENTRY` | `8` | RSI_CREATE_ENTRY |
| `LCS_OP_HIDE_ENTRY` | `9` | RSI_HIDE_ENTRY |
| `LCS_OP_DELETE_ENTRY` | `10` | RSI_DELETE_ENTRY |
| `LCS_OP_CREATE_KEY` | `11` | RSI_CREATE_KEY |
| `LCS_OP_WRITE_KEY` | `12` | RSI_WRITE_KEY |
| `LCS_OP_TXN_BEGIN` | `13` | RSI_BEGIN_TRANSACTION |
| `LCS_OP_TXN_COMMIT` | `14` | RSI_COMMIT_TRANSACTION |
| `LCS_OP_TXN_ABORT` | `15` | RSI_ABORT_TRANSACTION |
| `LCS_OP_FLUSH` | `16` | RSI_FLUSH |
| `LCS_OP_DELETE_LAYER` | `17` | RSI_DELETE_LAYER |

lcs_rsi_response reason — the outcome of accepting/validating a source's
RSI response frame, and the late-response effects that silently mark a
source DOWN. ACCEPTED is the clean path; DESYNC / OP_MISMATCH /
UNKNOWN_STATUS are the accept-time rejects that all surface as
-EINVAL/-EIO; MALFORMED_PAYLOAD is a per-op body validation reject; the
LATE_* codes mark a response whose deferred effect
(commit/mutation/begin bookkeeping) failed and took the source DOWN.
Verdict/outcome is also in `ret`. Never records name/GUID/frame bytes.

| Constant | Value | Notes |
|---|---|---|
| `LCS_RESP_ACCEPTED` | `0` | response matched an in-flight request |
| `LCS_RESP_DESYNC` | `1` | no matching delivered/unaccepted record |
| `LCS_RESP_OP_MISMATCH` | `2` | response op != request op \| RESPONSE_BIT |
| `LCS_RESP_UNKNOWN_STATUS` | `3` | rsi_status not a known status code |
| `LCS_RESP_MALFORMED_PAYLOAD` | `4` | per-op response body failed validation |
| `LCS_RESP_LATE_COMMIT_FAIL` | `5` | commit late-effect failed; source DOWN |
| `LCS_RESP_LATE_MUTATION_FAIL` | `6` | mutation late-effect failed; source DOWN |
| `LCS_RESP_LATE_BEGIN_FAIL` | `7` | begin-txn late-effect failed; source DOWN |

*lcs_source_fd reason — which source-fd lifecycle transition a record marks.*

OPEN is a fresh /dev/pkm_registry fd; the remaining codes are the entry
points that drive a source to the DOWN/closing state. `source_down_id`
is the source id that transitioned DOWN (0 if the call was a no-op). The
semantic *cause* of a late-effect-driven DOWN is carried by
lcs_rsi_response (LCS_RESP_LATE_*); here EXPLICIT/MARK_BY_ID are the
mechanical transitions. No pathname/SD bytes.

| Constant | Value | Notes |
|---|---|---|
| `LCS_SRC_OPEN` | `0` | new source fd issued (post-TCB check) |
| `LCS_SRC_RELEASE` | `1` | fd .release() teardown |
| `LCS_SRC_MALFORMED` | `2` | malformed protocol frame -> mark down |
| `LCS_SRC_EXPLICIT` | `3` | explicit mark-down of this fd |
| `LCS_SRC_MARK_BY_ID` | `4` | mark-down requested by source id |

lcs_in_flight reason — an in-flight RSI request table transition (kept
lean; insert on admission, delivered when handed to the source's read(),
release on response completion or teardown). `in_flight_count` is the
post-transition depth. Emitted by lcs:lcs_in_flight.

| Constant | Value | Notes |
|---|---|---|
| `LCS_IF_INSERT` | `0` | request inserted into in-flight table |
| `LCS_IF_DELIVERED` | `1` | request delivered to source read() |
| `LCS_IF_RELEASE` | `2` | request released from in-flight table |

*lcs_route op — which resolution the lcs:lcs_route event describes.*

| Constant | Value | Notes |
|---|---|---|
| `LCS_ROUTE_HIVE_NAME` | `0` | hive-name -> source/root resolution |
| `LCS_ROUTE_ABSOLUTE_PATH` | `1` | absolute-path -> source/root resolution |
| `LCS_ROUTE_SYMLINK_TARGET` | `2` | symlink-target -> source/root resolution |

*lcs_registration decision — the source registration path.*

NEW/RESUME_DOWN are publish verdicts; COPY is the input-copy stage;
REPLAY_FAIL/OVERFLOW_FAIL are resume post-publish -EIO paths that mark
the resumed source down. Emitted by lcs:lcs_source_register /
_registration_publish / _registration_copy.

| Constant | Value | Notes |
|---|---|---|
| `LCS_REG_NEW` | `0` | new source slot admitted |
| `LCS_REG_RESUME_DOWN` | `1` | down source slot resumed |
| `LCS_REG_COPY` | `2` | registration input copied from user |
| `LCS_REG_REPLAY_FAIL` | `3` | resume pending-delete replay failed (EIO) |
| `LCS_REG_OVERFLOW_FAIL` | `4` | resume overflow dispatch failed (EIO) |

*lcs_bootstrap stage — the phase of a bootstrap / self-config refresh.*

Emitted by lcs:lcs_bootstrap_refresh / _self_config_refresh /
_self_config_publish.

| Constant | Value | Notes |
|---|---|---|
| `LCS_BOOT_REGISTRY` | `0` | registry root discover phase |
| `LCS_BOOT_KMES` | `1` | kmes config root discover phase |
| `LCS_BOOT_LAYERS` | `2` | layer metadata root discover phase |
| `LCS_BOOT_SELF_WATCH` | `3` | self-watch arm phase |
| `LCS_BOOT_COMPLETE` | `4` | bootstrap refresh completed |
| `LCS_BOOT_SELF_CONFIG_REFRESH` | `5` | self-config refresh-from-key outcome |
| `LCS_BOOT_SELF_CONFIG_PARAM_INVALID` | `6` | self-config publish rejected a parameter |

lcs_runtime_limits field_id — which runtime-limit field a validate
reject names, or LCS_LIM_ALL for a successful whole-struct publish.
Emitted by lcs:lcs_limits_validate (-EINVAL, `value` offending) and
lcs:lcs_limits_publish.

| Constant | Value | Notes |
|---|---|---|
| `LCS_LIM_REQUEST_TIMEOUT_MS` | `0` |  |
| `LCS_LIM_TRANSACTION_TIMEOUT_MS` | `1` |  |
| `LCS_LIM_NOTIFICATION_QUEUE_SIZE` | `2` |  |
| `LCS_LIM_SYMLINK_DEPTH_LIMIT` | `3` |  |
| `LCS_LIM_MAX_VALUE_SIZE` | `4` |  |
| `LCS_LIM_MAX_KEY_DEPTH` | `5` |  |
| `LCS_LIM_MAX_PATH_COMPONENT_LENGTH` | `6` |  |
| `LCS_LIM_MAX_TOTAL_PATH_LENGTH` | `7` |  |
| `LCS_LIM_MAX_LAYERS_PER_VALUE` | `8` |  |
| `LCS_LIM_MAX_BOUND_TRANSACTIONS_PER_SOURCE` | `9` |  |
| `LCS_LIM_MAX_READ_ONLY_TRANSACTIONS_PER_SOURCE` | `10` |  |
| `LCS_LIM_MAX_TOTAL_LAYERS` | `11` |  |
| `LCS_LIM_MAX_REGISTERED_SOURCES` | `12` |  |
| `LCS_LIM_MAX_HIVES_PER_SOURCE` | `13` |  |
| `LCS_LIM_MAX_CONCURRENT_RSI_REQUESTS` | `14` |  |
| `LCS_LIM_MAX_SCOPE_GUIDS_PER_TOKEN` | `15` |  |
| `LCS_LIM_MAX_PRIVATE_LAYERS_PER_TOKEN` | `16` |  |
| `LCS_LIM_MAX_SUBTREE_WATCH_DEPTH` | `17` |  |
| `LCS_LIM_MAX_TRANSACTION_WATCH_EVENT_BURST` | `18` |  |
| `LCS_LIM_ALL` | `19` | whole-struct publish (success) |

*lcs_audit event_type_id — which LCS audit event a record describes.*

Emitted by lcs:lcs_audit_emit and lcs:lcs_audit_emit_failed.
`result_errno` carries the op-specific numeric. No SD or raw GUID bytes;
key GUID is a u64 hash.

| Constant | Value | Notes |
|---|---|---|
| `LCS_AUDIT_KEY_OPEN` | `0` | key-open SACL audit |
| `LCS_AUDIT_BACKUP_START` | `1` |  |
| `LCS_AUDIT_BACKUP_COMPLETE` | `2` |  |
| `LCS_AUDIT_RESTORE_START` | `3` |  |
| `LCS_AUDIT_RESTORE_COMPLETE` | `4` |  |
| `LCS_AUDIT_VALIDATION_FAILURE` | `5` | source validation-failure audit |
| `LCS_AUDIT_SELF_CONFIG_INVALID` | `6` | self-config-invalid audit |

*lcs_txn state — the transaction-fd state machine state carried in old_state new_state.*

Emitted by lcs:lcs_txn_begin / _first_bind / _bind_mutation _commit /
_abort / _timeout / _source_down.

| Constant | Value | Notes |
|---|---|---|
| `LCS_TXN_ST_ACTIVE_UNBOUND` | `0` | allocated, not yet source-bound |
| `LCS_TXN_ST_ACTIVE_BOUND` | `1` | bound to a source + root guid |
| `LCS_TXN_ST_COMMITTED` | `2` | commit round-trip succeeded |
| `LCS_TXN_ST_ABORTED` | `3` | aborted (close / layer writer abort) |
| `LCS_TXN_ST_TIMED_OUT` | `4` | deadline timer or commit timeout |
| `LCS_TXN_ST_SOURCE_DOWN` | `5` | bound source marked down |

*lcs_key_fd cmd — the key-fd ioctl verb (also stamped on lcs_key_mutation).*

LCS_KCMD_NONE is used by publish/release/read. Never records key/name/SD
bytes. Emitted by lcs:lcs_key_ioctl / _mutation.

| Constant | Value | Notes |
|---|---|---|
| `LCS_KCMD_NONE` | `0` | no ioctl verb (publish/release/read) |
| `LCS_KCMD_SET_VALUE` | `1` |  |
| `LCS_KCMD_DELETE_VALUE` | `2` |  |
| `LCS_KCMD_BLANKET_TOMBSTONE` | `3` |  |
| `LCS_KCMD_DELETE_KEY` | `4` |  |
| `LCS_KCMD_HIDE_KEY` | `5` |  |
| `LCS_KCMD_QUERY_VALUE` | `6` |  |
| `LCS_KCMD_QUERY_VALUES_BATCH` | `7` |  |
| `LCS_KCMD_ENUM_VALUES` | `8` |  |
| `LCS_KCMD_ENUM_SUBKEYS` | `9` |  |
| `LCS_KCMD_QUERY_KEY_INFO` | `10` |  |
| `LCS_KCMD_GET_SECURITY` | `11` |  |
| `LCS_KCMD_SET_SECURITY` | `12` |  |
| `LCS_KCMD_FLUSH` | `13` |  |
| `LCS_KCMD_BACKUP` | `14` |  |
| `LCS_KCMD_RESTORE` | `15` |  |
| `LCS_KCMD_NOTIFY` | `16` |  |
