---
title: Access mask bits
type: reference
description: The 32-bit access mask uses object-specific bits (0–15) whose meaning depends on the object type, plus standard rights, special rights, and generic rights. This page catalogues the per-object-type bits — file, process, token — and the GenericMapping tables that convert generic rights to specific ones.
related:
  - peios/constants-and-catalogs/overview
  - peios/constants-and-catalogs/ace-types-and-flags
  - peios/wire-formats-reference/security-descriptors
  - peios/security-descriptors/acls-and-aces
---

The 32-bit access mask is the same shape across every object type — bits 0–15 are object-specific, bits 16–20 are standard rights, bits 24–25 are special, bits 28–31 are generic. The standard, special, and generic rights are uniform; the object-specific bits 0–15 carry different meanings for different object types.

This page catalogues the access mask bits per object type and the GenericMapping tables that expand generic rights at evaluation time.

The mask layout itself is documented in [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags) and [Security descriptors (wire format)](~peios/wire-formats-reference/security-descriptors). This page is the per-type catalog.

## Mask layout reminder

| Bit range | Region | Examples |
|---|---|---|
| 0–15 | Object-specific | `FILE_READ_DATA`, `PROCESS_TERMINATE`, `TOKEN_QUERY`, etc. |
| 16–20 | Standard rights | `DELETE`, `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER`, `SYNCHRONIZE` |
| 21–23 | Reserved | Must be 0 |
| 24–25 | Special | `ACCESS_SYSTEM_SECURITY`, `MAXIMUM_ALLOWED` |
| 26–27 | Reserved | Must be 0 |
| 28–31 | Generic | `GENERIC_ALL`, `GENERIC_EXECUTE`, `GENERIC_WRITE`, `GENERIC_READ` |

## File access rights

For SDs on files and directories.

| Right | Value | For files | For directories (alias) |
|---|---|---|---|
| `FILE_READ_DATA` | 0x0001 | Read file content | `FILE_LIST_DIRECTORY` (list entries) |
| `FILE_WRITE_DATA` | 0x0002 | Write file content | `FILE_ADD_FILE` (create files in directory) |
| `FILE_APPEND_DATA` | 0x0004 | Append-only write | `FILE_ADD_SUBDIRECTORY` (create subdirectory) |
| `FILE_READ_EA` | 0x0008 | Read extended attributes | Same |
| `FILE_WRITE_EA` | 0x0010 | Write extended attributes | Same |
| `FILE_EXECUTE` | 0x0020 | Execute file | `FILE_TRAVERSE` (path-traverse through directory) |
| `FILE_DELETE_CHILD` | 0x0040 | (not applicable) | Delete children regardless of children's permissions |
| `FILE_READ_ATTRIBUTES` | 0x0080 | Read file attributes | Same |
| `FILE_WRITE_ATTRIBUTES` | 0x0100 | Write file attributes | Same |

`FILE_LIST_DIRECTORY`, `FILE_ADD_FILE`, `FILE_ADD_SUBDIRECTORY`, and `FILE_TRAVERSE` are name aliases for the corresponding file rights — the bit values are identical, only the naming convention differs based on whether the object is a file or directory.

### File GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL | SYNCHRONIZE` |
| `GENERIC_WRITE` | `FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_ATTRIBUTES | FILE_WRITE_EA | READ_CONTROL | SYNCHRONIZE` |
| `GENERIC_EXECUTE` | `FILE_EXECUTE | FILE_READ_ATTRIBUTES | READ_CONTROL | SYNCHRONIZE` |
| `GENERIC_ALL` | `FILE_READ_DATA | FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_READ_EA | FILE_WRITE_EA | FILE_EXECUTE | FILE_DELETE_CHILD | FILE_READ_ATTRIBUTES | FILE_WRITE_ATTRIBUTES | DELETE | READ_CONTROL | WRITE_DAC | WRITE_OWNER | SYNCHRONIZE` |

### FILE_ALL_ACCESS

| Constant | Value |
|---|---|
| `FILE_ALL_ACCESS` | `STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0x1FF` |

= `0x001F01FF`.

## Process access rights

For SDs on processes.

| Right | Value | Meaning |
|---|---|---|
| `PROCESS_TERMINATE` | 0x0001 | Send terminating signals (SIGKILL, SIGTERM, etc.). |
| `PROCESS_SIGNAL` | 0x0002 | Send non-terminating informational signals (SIGCHLD, SIGURG, SIGWINCH). |
| `PROCESS_VM_READ` | 0x0010 | Read process memory (`ptrace(PTRACE_PEEK*)`, `process_vm_readv`, `/proc/<pid>/mem` reads). |
| `PROCESS_VM_WRITE` | 0x0020 | Write process memory (`ptrace(PTRACE_POKE*, ATTACH)`, `process_vm_writev`). |
| `PROCESS_DUP_HANDLE` | 0x0040 | Duplicate fds out via `pidfd_getfd`. |
| `PROCESS_SET_INFORMATION` | 0x0200 | Change process attributes — priority, affinity, rlimits, `/proc/<pid>/*` writes. |
| `PROCESS_QUERY_INFORMATION` | 0x0400 | Detailed process info — token, full `/proc/<pid>/*` reads. |
| `PROCESS_SUSPEND_RESUME` | 0x0800 | Send stop/continue signals (SIGSTOP, SIGCONT). |
| `PROCESS_QUERY_LIMITED` | 0x1000 | Basic process info — PID, image name, state. Required by `pidfd_open`. |

Bits 0x0004, 0x0008, 0x0080, 0x0100 are unused.

### Process GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | READ_CONTROL` |
| `GENERIC_WRITE` | `PROCESS_SET_INFORMATION | PROCESS_VM_WRITE | WRITE_DAC` |
| `GENERIC_EXECUTE` | `PROCESS_TERMINATE | PROCESS_SUSPEND_RESUME | PROCESS_QUERY_LIMITED` |
| `GENERIC_ALL` | All process-specific bits plus `STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE` |

### PROCESS_ALL_ACCESS

| Constant | Value |
|---|---|
| `PROCESS_ALL_ACCESS` | `STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE | 0x1FFF` |

= `0x001F1FFF`.

## Token access rights

For SDs on token objects.

| Right | Value | Meaning |
|---|---|---|
| `TOKEN_ASSIGN_PRIMARY` | 0x0001 | Install as a process's primary token (via `KACS_IOC_INSTALL`). |
| `TOKEN_DUPLICATE` | 0x0002 | Create a copy (via `KACS_IOC_DUPLICATE` or FilterToken). |
| `TOKEN_IMPERSONATE` | 0x0004 | Install as a thread's impersonation token. |
| `TOKEN_QUERY` | 0x0008 | Read token information. |
| `TOKEN_QUERY_SOURCE` | 0x0010 | Subsumed by `TOKEN_QUERY`; reserved for format compatibility. |
| `TOKEN_ADJUST_PRIVILEGES` | 0x0020 | Enable, disable, or remove privileges. |
| `TOKEN_ADJUST_GROUPS` | 0x0040 | Enable or disable groups. |
| `TOKEN_ADJUST_DEFAULT` | 0x0080 | Change default DACL, owner index, primary group index. |
| `TOKEN_ADJUST_SESSIONID` | 0x0100 | Change `interactive_session_id` (additionally requires `SeTcbPrivilege`). |

`TOKEN_QUERY_SOURCE` is a documented bit position for format compatibility but is treated identically to `TOKEN_QUERY` in v0.20 — a token fd that grants `TOKEN_QUERY` is sufficient for everything; explicit `TOKEN_QUERY_SOURCE` is not separately enforced.

### Token GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `TOKEN_QUERY | READ_CONTROL` |
| `GENERIC_WRITE` | `TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT | WRITE_DAC` |
| `GENERIC_EXECUTE` | `TOKEN_IMPERSONATE` |
| `GENERIC_ALL` | `TOKEN_ALL_ACCESS` |

### TOKEN_ALL_ACCESS

| Constant | Value |
|---|---|
| `TOKEN_ALL_ACCESS` | `STANDARD_RIGHTS_REQUIRED | 0x01FF` |

= `0x000F01FF`.

## Registry-key access rights (when KACS evaluates registry-key SDs)

For SDs on registry keys (managed by loregd / the registry source).

| Right | Value | Meaning |
|---|---|---|
| `KEY_QUERY_VALUE` | 0x0001 | Read a value. |
| `KEY_SET_VALUE` | 0x0002 | Write a value. |
| `KEY_CREATE_SUB_KEY` | 0x0004 | Create a subkey. |
| `KEY_ENUMERATE_SUB_KEYS` | 0x0008 | Enumerate subkeys. |
| `KEY_NOTIFY` | 0x0010 | Watch for changes. |
| `KEY_CREATE_LINK` | 0x0020 | Create a symbolic link to another key. |

Bits 0x0040 onwards are reserved / unused.

### Registry GenericMapping

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `KEY_QUERY_VALUE | KEY_ENUMERATE_SUB_KEYS | KEY_NOTIFY | READ_CONTROL` |
| `GENERIC_WRITE` | `KEY_SET_VALUE | KEY_CREATE_SUB_KEY | READ_CONTROL` |
| `GENERIC_EXECUTE` | `READ_CONTROL` |
| `GENERIC_ALL` | All key-specific bits plus `STANDARD_RIGHTS_REQUIRED | SYNCHRONIZE` |

## Service access rights

For SDs on service objects (when the service control infrastructure exposes them).

| Right | Value | Meaning |
|---|---|---|
| `SERVICE_QUERY_CONFIG` | 0x0001 | Read configuration. |
| `SERVICE_CHANGE_CONFIG` | 0x0002 | Modify configuration. |
| `SERVICE_QUERY_STATUS` | 0x0004 | Read runtime status. |
| `SERVICE_ENUMERATE_DEPENDENTS` | 0x0008 | List dependent services. |
| `SERVICE_START` | 0x0010 | Start the service. |
| `SERVICE_STOP` | 0x0020 | Stop the service. |
| `SERVICE_PAUSE_CONTINUE` | 0x0040 | Pause and resume. |
| `SERVICE_INTERROGATE` | 0x0080 | Request status update. |
| `SERVICE_USER_DEFINED_CONTROL` | 0x0100 | Send service-specific control codes. |

## Generic right values (reminder)

| Right | Value |
|---|---|
| `GENERIC_READ` | 0x80000000 |
| `GENERIC_WRITE` | 0x40000000 |
| `GENERIC_EXECUTE` | 0x20000000 |
| `GENERIC_ALL` | 0x10000000 |

## Standard rights (reminder)

| Right | Value |
|---|---|
| `DELETE` | 0x00010000 |
| `READ_CONTROL` | 0x00020000 |
| `WRITE_DAC` | 0x00040000 |
| `WRITE_OWNER` | 0x00080000 |
| `SYNCHRONIZE` | 0x00100000 |
| `STANDARD_RIGHTS_REQUIRED` | 0x000F0000 |
| `STANDARD_RIGHTS_ALL` | 0x001F0000 |

## Special rights

| Right | Value |
|---|---|
| `ACCESS_SYSTEM_SECURITY` | 0x01000000 |
| `MAXIMUM_ALLOWED` | 0x02000000 |

## How GenericMapping is consulted

When AccessCheck encounters a generic right (either in the requested mask or in an ACE), it consults the object type's GenericMapping table:

1. For each generic bit set, look up the corresponding row in the GenericMapping table.
2. Replace the generic bit with the object-specific bits from the row.
3. Continue evaluation with the expanded mask.

The expansion happens at evaluation time. ACEs are typically stored with generic bits (so they work across different object types they might be applied to), but at the moment of evaluation the kernel expands them.

A few consequences:

- The same ACE bytes can produce different results on different object types. A `GENERIC_READ` ACE on a token grants `TOKEN_QUERY | READ_CONTROL`; on a file it grants the file-read set.
- An ACE author writing a DACL for a specific object type may use the object-specific bits directly. The end result is the same as if they'd used generic bits, but the intent is clearer.
- The kernel does not store the expanded form; each evaluation re-expands.

## Future object types

Additional object types will gain their own access mask bit definitions and GenericMapping tables in future versions:

- Pipes, sockets — currently treated by their underlying access (file-like).
- IPC objects (mutexes, semaphores, shared memory) — defined in some implementations; not yet standardised in Peios.
- Hardware devices — managed via FACS on devtmpfs; treated as file-like.

The pattern is uniform: each object type defines its own 16 bits (0–15) and a GenericMapping; standard rights, special rights, and generic right values are shared.
