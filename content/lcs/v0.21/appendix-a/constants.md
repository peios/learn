---
title: Constants
order: 1
---

All numeric constants used in the LCS interface. An independent
implementer can derive all magic numbers from this page.

## Syscall numbers

| Syscall | Number | Description |
|---|---|---|
| reg_open_key | 1100 | Open existing key. |
| reg_create_key | 1101 | Open or create key. |
| reg_begin_transaction | 1102 | Begin transaction. |

## Ioctl definitions

Type byte: `'R'` (0x52).

### Source registration ioctl (on /dev/pkm_registry fd)

| Ioctl | Number | Direction | Description |
|---|---|---|---|
| REG_SRC_REGISTER | 0 | _IOW | Register hives with LCS. |

Ioctl number namespaces are per-fd-type. REG_SRC_REGISTER (number
0 on /dev/pkm_registry fds) does not conflict with key fd ioctls
(number 0 on key fds) because the kernel dispatches ioctls based
on the fd's file_operations, not globally.

### Key fd ioctls

| Ioctl | Number | Direction | Description |
|---|---|---|---|
| REG_IOC_QUERY_VALUE | 0 | _IOWR | Read effective value. |
| REG_IOC_SET_VALUE | 1 | _IOW | Write value entry in layer. |
| REG_IOC_DELETE_VALUE | 2 | _IOW | Remove layer's value entry. |
| REG_IOC_BLANKET_TOMBSTONE | 3 | _IOW | Set/remove blanket tombstone. |
| REG_IOC_QUERY_VALUES_BATCH | 4 | _IOWR | Read all effective values. |
| REG_IOC_ENUM_VALUES | 5 | _IOWR | Enumerate values by index. |
| REG_IOC_ENUM_SUBKEYS | 6 | _IOWR | Enumerate subkeys by index. |
| REG_IOC_QUERY_KEY_INFO | 7 | _IOR | Query key metadata. |
| REG_IOC_DELETE_KEY | 8 | _IOW | Remove key's path entry from layer. |
| REG_IOC_HIDE_KEY | 9 | _IOW | Create HIDDEN path entry. |
| REG_IOC_GET_SECURITY | 10 | _IOWR | Read key SD. |
| REG_IOC_SET_SECURITY | 11 | _IOW | Modify key SD. |
| REG_IOC_NOTIFY | 12 | _IOW | Arm watch. |
| REG_IOC_FLUSH | 13 | _IO | Flush hive to durable storage. |
| REG_IOC_BACKUP | 14 | _IOW | Export subtree. |
| REG_IOC_RESTORE | 15 | _IOW | Import subtree. |

### Transaction fd ioctls

| Ioctl | Number | Direction | Description |
|---|---|---|---|
| REG_IOC_COMMIT | 16 | _IO | Commit transaction. |

## Syscall flags

### reg_open_key flags

| Flag | Value | Description |
|---|---|---|
| REG_OPEN_LINK | 0x01 | Open the symlink key itself, do not follow. |

### reg_create_key flags

| Flag | Value | Description |
|---|---|---|
| REG_OPTION_VOLATILE | 0x01 | Create volatile key (memory-only). |
| REG_OPTION_CREATE_LINK | 0x02 | Create symlink key. |

### Disposition values

| Value | Code | Description |
|---|---|---|
| REG_CREATED_NEW | 1 | Key was created. |
| REG_OPENED_EXISTING | 2 | Key already existed. |

## Access rights

### Specific rights (bits 0--15)

| Right | Value |
|---|---|
| KEY_QUERY_VALUE | 0x0001 |
| KEY_SET_VALUE | 0x0002 |
| KEY_CREATE_SUB_KEY | 0x0004 |
| KEY_ENUMERATE_SUB_KEYS | 0x0008 |
| KEY_NOTIFY | 0x0010 |
| KEY_CREATE_LINK | 0x0020 |

### Standard rights (bits 16--23)

| Right | Value |
|---|---|
| DELETE | 0x00010000 |
| READ_CONTROL | 0x00020000 |
| WRITE_DAC | 0x00040000 |
| WRITE_OWNER | 0x00080000 |

### System rights

| Right | Value |
|---|---|
| ACCESS_SYSTEM_SECURITY | 0x01000000 |
| MAXIMUM_ALLOWED | 0x02000000 |

### Generic mappings

| Generic | Value | Maps to |
|---|---|---|
| KEY_READ | 0x00020019 | KEY_QUERY_VALUE \| KEY_ENUMERATE_SUB_KEYS \| KEY_NOTIFY \| READ_CONTROL |
| KEY_WRITE | 0x00020006 | KEY_SET_VALUE \| KEY_CREATE_SUB_KEY \| READ_CONTROL |
| KEY_ALL_ACCESS | 0x000F003F | All specific \| all standard |

## Value types

| Type | Code |
|---|---|
| REG_NONE | 0 |
| REG_SZ | 1 |
| REG_EXPAND_SZ | 2 |
| REG_BINARY | 3 |
| REG_DWORD | 4 |
| REG_DWORD_BIG_ENDIAN | 5 |
| REG_LINK | 6 |
| REG_MULTI_SZ | 7 |
| REG_QWORD | 11 |
| REG_TOMBSTONE | 0xFFFF |

## Watch event types

| Type | Code |
|---|---|
| VALUE_SET | 1 |
| VALUE_DELETED | 2 |
| SUBKEY_CREATED | 3 |
| SUBKEY_DELETED | 4 |
| SD_CHANGED | 5 |
| KEY_DELETED | 6 |
| OVERFLOW | 7 |

## Watch filter bits

| Filter | Bit |
|---|---|
| REG_NOTIFY_VALUE | 0x01 |
| REG_NOTIFY_SUBKEY | 0x02 |
| REG_NOTIFY_SD | 0x04 |
| REG_NOTIFY_ALL | 0x07 |

## RSI op codes

| Operation | Code | Response code |
|---|---|---|
| RSI_LOOKUP | 0x01 | 0x8001 |
| RSI_CREATE_ENTRY | 0x02 | 0x8002 |
| RSI_HIDE_ENTRY | 0x03 | 0x8003 |
| RSI_DELETE_ENTRY | 0x04 | 0x8004 |
| RSI_ENUM_CHILDREN | 0x05 | 0x8005 |
| RSI_CREATE_KEY | 0x10 | 0x8010 |
| RSI_READ_KEY | 0x11 | 0x8011 |
| RSI_WRITE_KEY | 0x12 | 0x8012 |
| RSI_DROP_KEY | 0x13 | 0x8013 |
| RSI_QUERY_VALUES | 0x20 | 0x8020 |
| RSI_SET_VALUE | 0x21 | 0x8021 |
| RSI_DELETE_VALUE_ENTRY | 0x22 | 0x8022 |
| RSI_SET_BLANKET_TOMBSTONE | 0x23 | 0x8023 |
| RSI_BEGIN_TRANSACTION | 0x30 | 0x8030 |
| RSI_COMMIT_TRANSACTION | 0x31 | 0x8031 |
| RSI_ABORT_TRANSACTION | 0x32 | 0x8032 |
| RSI_DELETE_LAYER | 0x50 | 0x8050 |
| RSI_FLUSH | 0x40 | 0x8040 |

## RSI error codes

| Error | Code |
|---|---|
| RSI_OK | 0 |
| RSI_NOT_FOUND | 1 |
| RSI_ALREADY_EXISTS | 2 |
| RSI_STORAGE_ERROR | 3 |
| RSI_NOT_EMPTY | 4 |
| RSI_TOO_LARGE | 5 |
| RSI_TXN_BUSY | 6 |
| RSI_INVALID | 7 |
| RSI_CAS_FAILED | 8 |
| RSI_TXN_NOT_SUPPORTED | 9 |

## RSI registration flags

| Flag | Value | Description |
|---|---|---|
| RSI_HIVE_PRIVATE | 0x01 | Hive is private (requires scope GUID). |

## Backup record types

| Record | Type code |
|---|---|
| HEADER | 0x01 |
| LAYER | 0x02 |
| KEY | 0x03 |
| PATH_ENTRY | 0x04 |
| VALUE | 0x05 |
| BLANKET_TOMBSTONE | 0x06 |
| TRAILER | 0xFF |

## Backup magic

```
0x50 0x45 0x49 0x4F 0x53 0x52 0x45 0x47
 P    E    I    O    S    R    E    G
```
