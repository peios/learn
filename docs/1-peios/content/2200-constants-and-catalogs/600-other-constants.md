---
title: Other constants
type: reference
description: Mitigation flags, mount policy values, integrity levels, impersonation levels, logon types, error codes, size limits, magic numbers, and the rest of the numeric constants that don't fit the larger catalogs.
related:
  - peios/constants-and-catalogs/overview
  - peios/constants-and-catalogs/well-known-sids
  - peios/constants-and-catalogs/privilege-catalog
  - peios/constants-and-catalogs/access-mask-bits
---

This page catalogues the remaining numeric constants — values that don't fit the larger per-topic catalogues but appear in the API surface and event payloads.

## Process mitigation flags

In the PSB's mitigation bitfield (settable via `kacs_set_psb`):

| Flag | Value | Meaning |
|---|---|---|
| `KACS_MIT_WXP` | 0x001 | Write-XOR-Execute. |
| `KACS_MIT_TLP` | 0x002 | Trusted Library Paths. |
| `KACS_MIT_LSV` | 0x004 | Library Signature Verification. |
| `KACS_MIT_CFI` | 0x008 | Legacy alias: sets both CFIF and CFIB. |
| `KACS_MIT_UI_ACCESS` | 0x010 | Reserved in v0.20. |
| `KACS_MIT_NO_CHILD` | 0x020 | Forbid fork/clone-new-process. |
| `KACS_MIT_CFIF` | 0x040 | Forward CFI (Indirect Branch Tracking). |
| `KACS_MIT_CFIB` | 0x080 | Backward CFI (Shadow Stack). |
| `KACS_MIT_PIE` | 0x100 | PIE-only exec (refuse non-PIE binaries at exec). |
| `KACS_MIT_SML` | 0x200 | Speculation Mitigation Lock. |
| `KACS_MIT_ALL` | 0x3FF | OR of all valid flags. |

All flags are one-way — once set, cannot be cleared.

## Mount policy values

For `kacs_set_mount_policy` and `kacs_get_mount_policy`:

| Constant | Value | Meaning |
|---|---|---|
| `KACS_MOUNT_POLICY_UNMANAGED` | 1 | FACS does not apply. Not settable via public ABI; kernel-only. |
| `KACS_MOUNT_POLICY_DENY_MISSING` | 2 | Missing SDs deny access. |
| `KACS_MOUNT_POLICY_SYNTHESIZE_EPHEMERAL` | 3 | Missing SDs synthesised in memory; not written back. |
| `KACS_MOUNT_POLICY_SYNTHESIZE_PERSISTENT` | 4 | Missing SDs synthesised and persisted to the filesystem. |

Setting `UNMANAGED` via `kacs_set_mount_policy` returns `-EINVAL`.

## Integrity levels

The RIDs used in `S-1-16-*` SIDs and in token `integrity_level` fields:

| Constant | RID | Name |
|---|---|---|
| `INTEGRITY_LEVEL_UNTRUSTED` | 0 | Untrusted |
| `INTEGRITY_LEVEL_LOW` | 4096 | Low |
| `INTEGRITY_LEVEL_MEDIUM` | 8192 | Medium |
| `INTEGRITY_LEVEL_HIGH` | 12288 | High |
| `INTEGRITY_LEVEL_SYSTEM` | 16384 | System |

Spaced by 4096; future levels can be inserted between existing ones.

## Mandatory policy flags

In a token's `mandatory_policy` field:

| Flag | Value | Meaning |
|---|---|---|
| `NO_WRITE_UP` | 0x01 | MIC blocks write-category from lower integrity. |
| `NEW_PROCESS_MIN` | 0x02 | At exec, lower token integrity to match the binary if lower. |

Both flags are immutable after token creation.

## Impersonation levels

In a token's `impersonation_level` field:

| Constant | Value | Meaning |
|---|---|---|
| `KACS_LEVEL_ANONYMOUS` | 0 | No identity. |
| `KACS_LEVEL_IDENTIFICATION` | 1 | Inspect only; cannot use for AccessCheck. |
| `KACS_LEVEL_IMPERSONATION` | 2 | Act as client locally. Default. |
| `KACS_LEVEL_DELEGATION` | 3 | Act as client locally; forward credentials to remote machines. |

## Elevation types

In a token's `elevation_type` field:

| Constant | Value | Meaning |
|---|---|---|
| `KACS_ELEVATION_DEFAULT` | 0 | Not part of a linked pair. |
| `KACS_ELEVATION_FULL` | 1 | The elevated half of a linked pair. |
| `KACS_ELEVATION_LIMITED` | 2 | The non-elevated half. |

## Logon types

In a session's `logon_type` field:

| Constant | Value | Meaning |
|---|---|---|
| `LOGON_TYPE_INTERACTIVE` | 2 | Console, SSH, terminal services. |
| `LOGON_TYPE_NETWORK` | 3 | Network resource access (SMB, RPC, federated). |
| `LOGON_TYPE_BATCH` | 4 | Scheduled job. |
| `LOGON_TYPE_SERVICE` | 5 | Service running under a specific principal. |
| `LOGON_TYPE_NETWORK_CLEARTEXT` | 8 | Network logon with cleartext credential. |
| `LOGON_TYPE_NEW_CREDENTIALS` | 9 | Keep local identity; use alternative credentials for outbound. |

Values 1, 6, 7, 10+ are reserved.

## PIP type values

In a process's PSB `pip_type` field:

| Constant | Value | Meaning |
|---|---|---|
| `PIP_TYPE_NONE` | 0 | Unprotected. Default for unsigned binaries. |
| `PIP_TYPE_PROTECTED` | 512 | Standard PIP protection. |
| `PIP_TYPE_ISOLATED` | 1024 | Reserved; no v0.20 signing key targets this. |

## Token audit policy flags

In a token's `audit_policy` field:

| Flag | Value | Meaning |
|---|---|---|
| `OBJECT_ACCESS_SUCCESS` | 0x01 | Force an audit event on every successful access. |
| `OBJECT_ACCESS_FAILURE` | 0x02 | Force an audit event on every failed access. |
| `PRIVILEGE_USE_SUCCESS` | 0x04 | Emit privilege-use audit when bits survive. |
| `PRIVILEGE_USE_FAILURE` | 0x08 | Emit privilege-use audit when bits are stripped. |

## kacs_open create dispositions

| Constant | Value | Behaviour |
|---|---|---|
| `KACS_FILE_SUPERSEDE` | 0 | If exists, delete and recreate; else create. |
| `KACS_FILE_OPEN` | 1 | If exists, open; else fail with ENOENT. |
| `KACS_FILE_CREATE` | 2 | If exists, fail with EEXIST; else create. |
| `KACS_FILE_OPEN_IF` | 3 | If exists, open; else create. |
| `KACS_FILE_OVERWRITE` | 4 | If exists, truncate and open; else fail with ENOENT. |
| `KACS_FILE_OVERWRITE_IF` | 5 | If exists, truncate and open; else create. |

## kacs_open create options

| Flag | Value | Meaning |
|---|---|---|
| `KACS_CREATE_OPT_DIRECTORY` | 0x0001 | Target must be (or will be created as) a directory. |
| `KACS_CREATE_OPT_DELETE_ON_CLOSE` | 0x0002 | Delete on last fd close. |

## kacs_open status values

In the `status_out` parameter:

| Constant | Value | Meaning |
|---|---|---|
| `KACS_STATUS_OPENED` | 1 | An existing file was opened. |
| `KACS_STATUS_CREATED` | 2 | A new file was created. |
| `KACS_STATUS_OVERWRITTEN` | 3 | An existing file was truncated and opened. |
| `KACS_STATUS_SUPERSEDED` | 4 | An existing file was deleted and a new one created. |

## kacs_open_self_token flags

| Flag | Value | Meaning |
|---|---|---|
| `KACS_REAL_TOKEN` | 0x01 | Return the primary token even if the thread is impersonating. |

## SECURITY_INFORMATION flags

For `kacs_get_sd` and `kacs_set_sd`:

| Flag | Value | Required right (read) | Required right (write) |
|---|---|---|---|
| `OWNER_SECURITY_INFORMATION` | 0x01 | READ_CONTROL | WRITE_OWNER |
| `GROUP_SECURITY_INFORMATION` | 0x02 | READ_CONTROL | WRITE_OWNER |
| `DACL_SECURITY_INFORMATION` | 0x04 | READ_CONTROL | WRITE_DAC |
| `SACL_SECURITY_INFORMATION` | 0x08 | ACCESS_SYSTEM_SECURITY | ACCESS_SYSTEM_SECURITY |
| `LABEL_SECURITY_INFORMATION` | 0x10 | READ_CONTROL | WRITE_OWNER + integrity rules |

`SACL_SECURITY_INFORMATION` and `LABEL_SECURITY_INFORMATION` are mutually exclusive in one call.

## Path-resolution flags

Used in many syscalls that take a dirfd + path:

| Flag | Value | Meaning |
|---|---|---|
| `AT_EMPTY_PATH` | 0x1000 | Operate on the dirfd directly; path is empty. |
| `AT_SYMLINK_NOFOLLOW` | 0x100 | Do not follow a terminal symlink. |
| `AT_FDCWD` | -100 | Special dirfd value meaning "current working directory". |

## Privilege intent flags

For AccessCheck:

| Flag | Value | Activates |
|---|---|---|
| `BACKUP_INTENT` | 0x01 | `SeBackupPrivilege` |
| `RESTORE_INTENT` | 0x02 | `SeRestorePrivilege` |

## Privilege attribute flags

For `kacs_priv_entry` records:

| Flag | Value | Meaning |
|---|---|---|
| `SE_PRIVILEGE_ENABLED` | 0x02 | Enable. |
| `SE_PRIVILEGE_REMOVED` | 0x04 | Permanently remove. |
| `KACS_PRIV_RESET_ALL_DEFAULTS` | 0x80000000 | Reset all privileges to defaults (with luid=0). |

A value of `0` disables.

## Restrict flags

For `KACS_IOC_RESTRICT`:

| Flag | Value | Meaning |
|---|---|---|
| `KACS_RESTRICT_WRITE_RESTRICTED` | 0x01 | Enable write-restricted mode plus `user_deny_only` on the new token. |

## Token wire format constants

| Constant | Value | Meaning |
|---|---|---|
| `TOKEN_SPEC_VERSION` | 2 | Required value of the `version` field in token specs. |
| `KACS_ACCESS_CHECK_ARGS_V1_SIZE` | 40 | Minimum size of `kacs_access_check_args` the kernel accepts. |

## Conditional ACE bytecode magic

| Bytes | ASCII | Meaning |
|---|---|---|
| `0x61 0x72 0x74 0x78` | "artx" | Start of conditional expression. Absent → expression evaluates UNKNOWN. |

## Conditional ACE opcodes

Operator opcodes (from [Conditional ACE bytecode](~peios/wire-formats-reference/conditional-ace-bytecode)):

| Opcode | Operator |
|---|---|
| 0x01–0x04 | Integer literals (INT8/16/32/64) |
| 0x10 | Unicode string literal |
| 0x18 | Octet string literal |
| 0x50 | Composite literal |
| 0x51 | SID literal |
| 0x80 | == |
| 0x81 | != |
| 0x82 | < |
| 0x83 | <= |
| 0x84 | > |
| 0x85 | >= |
| 0x86 | Contains |
| 0x87 | Exists |
| 0x88 | Any_of |
| 0x89 | Member_of |
| 0x8A | Device_Member_of |
| 0x8B | Member_of_Any |
| 0x8C | Device_Member_of_Any |
| 0x8D | Not_Exists |
| 0x8E | Not_Contains |
| 0x8F | Not_Any_of |
| 0x90 | Not_Member_of |
| 0x91 | Not_Device_Member_of |
| 0x92 | Not_Member_of_Any |
| 0x93 | Not_Device_Member_of_Any |
| 0xA0 | AND |
| 0xA1 | OR |
| 0xA2 | NOT |
| 0xF8 | @Local. |
| 0xF9 | @User. |
| 0xFA | @Resource. |
| 0xFB | @Device. |

## CAAP wire format

| Constant | Value | Meaning |
|---|---|---|
| CAAP version byte | `0x01` | Required at offset 0 of every CAAP spec in v0.20. |
| CAAP rule count maximum | 256 | Max rules per policy. |
| CAAP spec maximum size | 256 KB | Max total spec size. |
| Applies-to expression maximum | 64 KB | Max bytecode size per rule. |

## Size and count limits

A summary of the limits the kernel enforces:

| Limit | Value | Context |
|---|---|---|
| Max SD size | 65,535 bytes | Any SD blob |
| Max ACL size | 64 KB | Any ACL within an SD |
| Max single ACE size | 64 KB | (bounded by ACL size) |
| Max claim entry size | (bounded by containing structure) | Resource attribute ACE, token claims |
| Min SID size | 8 bytes | Revision + count + authority, no sub-authorities |
| Max SID size | 68 bytes | 15 sub-authorities |
| Max token wire spec size | 64 KB | `kacs_create_token` input |
| Max session wire spec size | 4096 bytes | `kacs_create_session` input |
| Max CAAP wire spec size | 256 KB | `kacs_set_caap` input |
| Max CAAP rules per policy | 256 | |
| Max applies-to expression | 64 KB | Per CAAP rule |
| Recommended max conditional stack depth | 1024 | Evaluator limit |
| Max TLP cache entries | 64 | Trusted Library Path prefixes |
| Max TLP path length | 4096 bytes | Per prefix |
| Max mount template SD | 64 KiB | `kacs_set_mount_policy` template |
| Anonymous session ID | 998 | The kernel-direct Anonymous session |
| SYSTEM session ID | 0 | The kernel-direct SYSTEM session |
| Default impersonation level | Impersonation (2) | If client does not set otherwise |

## Magic numbers and sentinels

| Constant | Value | Meaning |
|---|---|---|
| KACS_IOC_MAGIC | 0x4B ('K') | Magic byte for token-fd ioctls. |
| KMES event-type prefix for file ops | `file.` | Continuous-audit events from FACS use this prefix in the `operation` field. |
| Conditional-ACE magic | `artx` (0x61 0x72 0x74 0x78) | Start of conditional expression bytecode. |
| Unmapped UID/GID projection | 65534 | Returned when a SID has no UID/GID mapping in the directory. |
| Reset-all-groups index | 0xFFFFFFFF | `kacs_group_entry.index` value meaning "reset all to defaults". |
| Reset-all-privileges luid | 0 | `kacs_priv_entry.luid` with `KACS_PRIV_RESET_ALL_DEFAULTS` attributes. |
| Bootstrap logon SID | `S-1-5-5-0-0` | The logon SID of the kernel-direct SYSTEM session. |
| Anonymous logon LUID | 998 (0x3E6) | The Anonymous session's `auth_id`. |
| `no_change` index for AdjustDefault | 0xFFFF | `owner_index` / `group_index` value meaning "no change". |
| Linux "nobody" UID/GID | 65534 | Standard fallback for unmapped principals. |

## Error code summary

The errno values most often returned by KACS syscalls:

| Code | Typical cause |
|---|---|
| `-EACCES` | Access check denied; some required right was not granted. |
| `-EPERM` | Privilege required for the operation is missing, or a special restriction (e.g., restricted→unrestricted same-user impersonation). |
| `-EINVAL` | Parameter malformed — bad SD, unknown enum value, non-zero reserved fields, malformed wire format. |
| `-EFAULT` | Bad pointer parameter. |
| `-ERANGE` | Buffer too small; required size written. |
| `-ENOENT` | Target object/principal does not exist. |
| `-EBADF` | Invalid file descriptor. |
| `-ENOSYS` | Syscall not implemented. |
| `-EEXIST` | Object already exists (typically for CREATE dispositions). |
| `-ENOTDIR` | Target is not a directory when required. |
| `-ELOOP` | Symlink encountered when NOFOLLOW was set. |
| `-EOPNOTSUPP` | Operation not supported on this filesystem / object. |
| `-ESRCH` | Target process / thread does not exist. |
| `-ENOMEM` | Allocation failed. |

For per-syscall lists of which errors are possible, see [Syscalls](~peios/kernel-abi-reference/syscalls) and [Token ioctls](~peios/kernel-abi-reference/token-ioctls).
