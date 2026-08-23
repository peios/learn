---
title: Access mask bits
type: reference
description: The per-object-type access rights — file, process, token, registry key, service — plus the standard, special and generic rights, the GenericMapping tables, and the aggregate *_ALL_ACCESS constants.
related:
  - peios/constants-and-catalogs/overview
  - peios/constants-and-catalogs/ace-types-and-flags
  - peios/security-descriptors/acls-and-aces
---

The 32-bit access mask has the same shape for every object type. Bits 0–15 are object-specific, 16–20 are standard rights, 24–25 are special, 28–31 are generic. The standard, special and generic regions are uniform; the object-specific bits carry different meanings for different object types.

This page is the catalogue of right *values*. What the mask **means** — how it is evaluated, how generic bits expand — is PCDS §5.3, which is normative. The bit layout of the mask within a descriptor is PCDS §5.1.

| Bit range | Region | Examples |
|---|---|---|
| 0–15 | Object-specific | `FILE_READ_DATA`, `PROCESS_TERMINATE`, `TOKEN_QUERY` |
| 16–20 | Standard rights | `DELETE`, `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER`, `SYNCHRONIZE` |
| 21–23 | Reserved | Rejected at parse. PCDS §5.3. |
| 24–25 | Special | `ACCESS_SYSTEM_SECURITY`, `MAXIMUM_ALLOWED` |
| 26–27 | Reserved | Rejected at parse. |
| 28–31 | Generic | `GENERIC_ALL`, `GENERIC_EXECUTE`, `GENERIC_WRITE`, `GENERIC_READ` |

## File access rights

| Right | Value | For files | For directories (alias) |
|---|---|---|---|
| `FILE_READ_DATA` | 0x0001 | Read file content | `FILE_LIST_DIRECTORY` — list entries |
| `FILE_WRITE_DATA` | 0x0002 | Write file content | `FILE_ADD_FILE` — create files |
| `FILE_APPEND_DATA` | 0x0004 | Append-only write | `FILE_ADD_SUBDIRECTORY` — create subdirectory |
| `FILE_READ_EA` | 0x0008 | Read extended attributes | Same |
| `FILE_WRITE_EA` | 0x0010 | Write extended attributes | Same |
| `FILE_EXECUTE` | 0x0020 | Execute file | `FILE_TRAVERSE` — traverse through |
| `FILE_DELETE_CHILD` | 0x0040 | (not applicable) | Delete children regardless of their permissions |
| `FILE_READ_ATTRIBUTES` | 0x0080 | Read attributes | Same |
| `FILE_WRITE_ATTRIBUTES` | 0x0100 | Write attributes | Same |

The directory names are **aliases**: identical bit values, different naming convention depending on whether the object is a file or a directory.

### File GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `FILE_READ_DATA` \| `FILE_READ_ATTRIBUTES` \| `FILE_READ_EA` \| `READ_CONTROL` \| `SYNCHRONIZE` |
| `GENERIC_WRITE` | `FILE_WRITE_DATA` \| `FILE_APPEND_DATA` \| `FILE_WRITE_ATTRIBUTES` \| `FILE_WRITE_EA` \| `READ_CONTROL` \| `SYNCHRONIZE` |
| `GENERIC_EXECUTE` | `FILE_EXECUTE` \| `FILE_READ_ATTRIBUTES` \| `READ_CONTROL` \| `SYNCHRONIZE` |
| `GENERIC_ALL` | Every file-specific bit, plus `DELETE`, `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER`, `SYNCHRONIZE` |

`FILE_ALL_ACCESS` = `STANDARD_RIGHTS_REQUIRED` \| `SYNCHRONIZE` \| `0x1FF` = **0x001F01FF**.

## Process access rights

| Right | Value | Meaning |
|---|---|---|
| `PROCESS_TERMINATE` | 0x0001 | Send terminating signals. |
| `PROCESS_SIGNAL` | 0x0002 | Send non-terminating informational signals — SIGCHLD, SIGURG, SIGWINCH. |
| `PROCESS_VM_READ` | 0x0010 | Read process memory — `ptrace(PTRACE_PEEK*)`, `process_vm_readv`, `/proc/<pid>/mem` reads. |
| `PROCESS_VM_WRITE` | 0x0020 | Write process memory — `ptrace(PTRACE_POKE*, ATTACH)`, `process_vm_writev`. |
| `PROCESS_DUP_HANDLE` | 0x0040 | Duplicate file descriptors out via `pidfd_getfd`. |
| `PROCESS_SET_INFORMATION` | 0x0200 | Change process attributes — priority, affinity, rlimits, `/proc/<pid>/*` writes. |
| `PROCESS_QUERY_INFORMATION` | 0x0400 | Detailed process info — token, full `/proc/<pid>/*` reads. |
| `PROCESS_SUSPEND_RESUME` | 0x0800 | Send stop and continue signals. |
| `PROCESS_QUERY_LIMITED` | 0x1000 | Basic info — PID, image name, state. Required by `pidfd_open`. |

Bits 0x0004, 0x0008, 0x0080 and 0x0100 are unused.

### Process GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `PROCESS_QUERY_INFORMATION` \| `PROCESS_VM_READ` \| `READ_CONTROL` |
| `GENERIC_WRITE` | `PROCESS_SET_INFORMATION` \| `PROCESS_VM_WRITE` \| `WRITE_DAC` |
| `GENERIC_EXECUTE` | `PROCESS_TERMINATE` \| `PROCESS_SUSPEND_RESUME` \| `PROCESS_QUERY_LIMITED` |
| `GENERIC_ALL` | All process-specific bits, plus `STANDARD_RIGHTS_REQUIRED` \| `SYNCHRONIZE` |

`PROCESS_ALL_ACCESS` = `STANDARD_RIGHTS_REQUIRED` \| `SYNCHRONIZE` \| `0x1FFF` = **0x001F1FFF**.

## Token access rights

| Right | Value | Meaning |
|---|---|---|
| `TOKEN_ASSIGN_PRIMARY` | 0x0001 | Install as a process's primary token. |
| `TOKEN_DUPLICATE` | 0x0002 | Create a copy. |
| `TOKEN_IMPERSONATE` | 0x0004 | Install as a thread's impersonation token. |
| `TOKEN_QUERY` | 0x0008 | Read token information. |
| `TOKEN_QUERY_SOURCE` | 0x0010 | Subsumed by `TOKEN_QUERY`. Reserved for format compatibility. |
| `TOKEN_ADJUST_PRIVILEGES` | 0x0020 | Enable, disable or remove privileges. |
| `TOKEN_ADJUST_GROUPS` | 0x0040 | Enable or disable groups. |
| `TOKEN_ADJUST_DEFAULT` | 0x0080 | Change default DACL, owner index, primary group index. |
| `TOKEN_ADJUST_SESSIONID` | 0x0100 | Change `interactive_session_id`. Additionally requires `SeTcbPrivilege`. |

`TOKEN_QUERY_SOURCE` is a documented bit position rather than an enforced right: a token fd granting `TOKEN_QUERY` suffices for everything, and `TOKEN_QUERY_SOURCE` is not separately checked.

### Token GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `TOKEN_QUERY` \| `READ_CONTROL` |
| `GENERIC_WRITE` | `TOKEN_ADJUST_PRIVILEGES` \| `TOKEN_ADJUST_GROUPS` \| `TOKEN_ADJUST_DEFAULT` \| `WRITE_DAC` |
| `GENERIC_EXECUTE` | `TOKEN_IMPERSONATE` |
| `GENERIC_ALL` | `TOKEN_ALL_ACCESS` |

`TOKEN_ALL_ACCESS` = `STANDARD_RIGHTS_REQUIRED` \| `0x01FF` = **0x000F01FF**. Note the absence of `SYNCHRONIZE`, unlike the file and process aggregates.

## Registry-key access rights

| Right | Value | Meaning |
|---|---|---|
| `KEY_QUERY_VALUE` | 0x0001 | Read a value. |
| `KEY_SET_VALUE` | 0x0002 | Write a value. |
| `KEY_CREATE_SUB_KEY` | 0x0004 | Create a subkey. |
| `KEY_ENUMERATE_SUB_KEYS` | 0x0008 | Enumerate subkeys. |
| `KEY_NOTIFY` | 0x0010 | Watch for changes. |
| `KEY_CREATE_LINK` | 0x0020 | Create a symbolic link to another key. |

Bits from 0x0040 upward are reserved.

### Registry GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `KEY_QUERY_VALUE` \| `KEY_ENUMERATE_SUB_KEYS` \| `KEY_NOTIFY` \| `READ_CONTROL` |
| `GENERIC_WRITE` | `KEY_SET_VALUE` \| `KEY_CREATE_SUB_KEY` \| `READ_CONTROL` |
| `GENERIC_EXECUTE` | `READ_CONTROL` |
| `GENERIC_ALL` | All key-specific bits, plus `STANDARD_RIGHTS_REQUIRED` \| `SYNCHRONIZE` |

## Service access rights

| Right | Value | Meaning |
|---|---|---|
| `SERVICE_QUERY_CONFIG` | 0x0001 | Read configuration. |
| `SERVICE_CHANGE_CONFIG` | 0x0002 | Modify configuration. |
| `SERVICE_QUERY_STATUS` | 0x0004 | Read runtime status. |
| `SERVICE_ENUMERATE_DEPENDENTS` | 0x0008 | List dependent services. |
| `SERVICE_START` | 0x0010 | Start the service. |
| `SERVICE_STOP` | 0x0020 | Stop the service. |
| `SERVICE_PAUSE_CONTINUE` | 0x0040 | Pause and resume. |
| `SERVICE_INTERROGATE` | 0x0080 | Request a status update. |
| `SERVICE_USER_DEFINED_CONTROL` | 0x0100 | Send service-specific control codes. |

## Standard, special and generic rights

| Right | Value |
|---|---|
| `DELETE` | 0x00010000 |
| `READ_CONTROL` | 0x00020000 |
| `WRITE_DAC` | 0x00040000 |
| `WRITE_OWNER` | 0x00080000 |
| `SYNCHRONIZE` | 0x00100000 |
| `ACCESS_SYSTEM_SECURITY` | 0x01000000 |
| `MAXIMUM_ALLOWED` | 0x02000000 |
| `GENERIC_ALL` | 0x10000000 |
| `GENERIC_EXECUTE` | 0x20000000 |
| `GENERIC_WRITE` | 0x40000000 |
| `GENERIC_READ` | 0x80000000 |

### The STANDARD_RIGHTS aggregates

| Constant | Value | Composition |
|---|---|---|
| `STANDARD_RIGHTS_REQUIRED` | 0x000F0000 | `DELETE` \| `READ_CONTROL` \| `WRITE_DAC` \| `WRITE_OWNER` |
| `STANDARD_RIGHTS_READ` | 0x00020000 | Alias of `READ_CONTROL` |
| `STANDARD_RIGHTS_WRITE` | 0x00020000 | Alias of `READ_CONTROL` |
| `STANDARD_RIGHTS_EXECUTE` | 0x00020000 | Alias of `READ_CONTROL` |
| `STANDARD_RIGHTS_ALL` | 0x001F0000 | All five standard rights |

Three of these are the **same value**. `STANDARD_RIGHTS_READ`, `_WRITE` and `_EXECUTE` are all aliases of `READ_CONTROL`, which surprises people reading a mask and expecting them to differ. Only `STANDARD_RIGHTS_REQUIRED` and `STANDARD_RIGHTS_ALL` name distinct values.

`STANDARD_RIGHTS_REQUIRED` is the conventional minimum included in every `*_ALL_ACCESS` aggregate.
