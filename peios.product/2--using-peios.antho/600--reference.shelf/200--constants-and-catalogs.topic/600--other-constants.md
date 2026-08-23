---
title: Other constants
type: reference
description: Enumerated values that are not access rights — impersonation levels, integrity levels, logon types, PIP tiers, token audit policy, create dispositions, SECURITY_INFORMATION flags, mitigation flags, and the kernel's size limits.
related:
  - peios/constants-and-catalogs/overview
  - peios/constants-and-catalogs/access-mask-bits
  - peios/impersonation/impersonation-levels
  - peios/logon-sessions/logon-types
---

Enumerated values that are not access rights. Access rights are catalogued separately in [Access mask bits](~peios/constants-and-catalogs/access-mask-bits).

> [!NOTE]
> Names here are the ones `uapi/pkm/` declares, because that is where a reader meets them. Several were published under different spellings in older design documents; where that is so, this page says which. The Peios Kernel TRM §3.A carries the full mapping.

## Impersonation levels

A token's impersonation level. The conceptual model is [Impersonation levels](~peios/impersonation/impersonation-levels).

| Constant | Value | Meaning |
|---|---|---|
| `KACS_IMLEVEL_ANONYMOUS` | 0 | No identity. |
| `KACS_IMLEVEL_IDENTIFICATION` | 1 | Inspect only. Cannot be used for an access check. |
| `KACS_IMLEVEL_IMPERSONATION` | 2 | Act as the client locally. The default. |
| `KACS_IMLEVEL_DELEGATION` | 3 | Act as the client locally, and forward credentials to remote machines. |

Older documents spell these `KACS_LEVEL_*`. That spelling does not exist in any header.

A primary token reports level 0.

## Integrity levels

The RIDs used in `S-1-16-*` SIDs and in a token's `integrity_level` field. The model is [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

| Constant | RID | Name |
|---|---|---|
| `INTEGRITY_LEVEL_UNTRUSTED` | 0 | Untrusted |
| `INTEGRITY_LEVEL_LOW` | 4096 | Low |
| `INTEGRITY_LEVEL_MEDIUM` | 8192 | Medium |
| `INTEGRITY_LEVEL_HIGH` | 12288 | High |
| `INTEGRITY_LEVEL_SYSTEM` | 16384 | System |

Spaced by 4096, so future levels can be inserted between existing ones.

**These are named levels, not a closed enum.** The integrity level is the `S-1-16` SID's single sub-authority as an unsigned integer, compared numerically. Any such value is valid, and non-standard ones appear in Windows-interop descriptors — `medium-plus` at 8448, `protected` at 20480. Code that switches on the five names will mishandle those.

## Mandatory policy flags

A token's `mandatory_policy` field. Both are immutable after token creation.

| Flag | Value | Meaning |
|---|---|---|
| `NO_WRITE_UP` | 0x01 | MIC blocks write-category access from lower integrity. |
| `NEW_PROCESS_MIN` | 0x02 | At exec, lower the token's integrity to match the binary if the binary is lower. |

## Logon types

A session's `logon_type` field. The model is [Logon types](~peios/logon-sessions/logon-types).

| Constant | Value | Meaning |
|---|---|---|
| `LOGON_TYPE_INTERACTIVE` | 2 | Console, SSH, terminal services. |
| `LOGON_TYPE_NETWORK` | 3 | Network resource access — SMB, RPC, federated. |
| `LOGON_TYPE_BATCH` | 4 | Scheduled job. |
| `LOGON_TYPE_SERVICE` | 5 | Service running under a specific principal. |
| `LOGON_TYPE_NETWORK_CLEARTEXT` | 8 | Network logon with a cleartext credential. |
| `LOGON_TYPE_NEW_CREDENTIALS` | 9 | Keep the local identity; use alternative credentials outbound. |

Values 1, 6, 7 and 10 upward are reserved.

## Elevation types

A token's `elevation_type` field.

| Constant | Value | Meaning |
|---|---|---|
| `KACS_ELEVATION_DEFAULT` | 1 | Not part of a linked pair. |
| `KACS_ELEVATION_FULL` | 2 | The elevated half of a linked pair. |
| `KACS_ELEVATION_LIMITED` | 3 | The non-elevated half. |

## PIP tiers

A process's PSB `pip_type` field.

| Value | Meaning |
|---|---|
| 0 | None. Unprotected, the default for unsigned binaries. |
| 512 | Protected. Standard PIP protection. |
| 1024 | Isolated. Reserved; no signing key targets it. |

**There are no public constants for these.** Nothing in `uapi/pkm/` names the tiers, and `PIP_TYPE_NONE` / `_PROTECTED` / `_ISOLATED` — which older documents use — exist nowhere in the tree. Protected survives only as the kernel-private `PKM_KACS_PIP_TYPE_PROTECTED`.

A program reasoning about tiers compares the numbers. The Peios Kernel TRM §3.7 says the same.

## Token audit policy flags

A token's `audit_policy` field. These are what force the audit events in the [Events Index](~peios/kernel-access-events/access-audit).

| Flag | Value | Meaning |
|---|---|---|
| `OBJECT_ACCESS_SUCCESS` | 0x01 | Force an audit event on every successful access. |
| `OBJECT_ACCESS_FAILURE` | 0x02 | Force an audit event on every failed access. |
| `PRIVILEGE_USE_SUCCESS` | 0x04 | Emit a `privilege-use` event when a privilege's bits survive. |
| `PRIVILEGE_USE_FAILURE` | 0x08 | Emit a `privilege-use` event when its bits are stripped. |

## Create dispositions

For `kacs_open`.

| Constant | Value | Behaviour |
|---|---|---|
| `KACS_DISPOSITION_SUPERSEDE` | 0 | If it exists, delete and recreate; otherwise create. |
| `KACS_DISPOSITION_OPEN` | 1 | If it exists, open; otherwise fail with `ENOENT`. |
| `KACS_DISPOSITION_CREATE` | 2 | If it exists, fail with `EEXIST`; otherwise create. |
| `KACS_DISPOSITION_OPEN_IF` | 3 | If it exists, open; otherwise create. |
| `KACS_DISPOSITION_OVERWRITE` | 4 | If it exists, truncate and open; otherwise fail with `ENOENT`. |
| `KACS_DISPOSITION_OVERWRITE_IF` | 5 | If it exists, truncate and open; otherwise create. |

Older documents spell these `KACS_FILE_SUPERSEDE`, `KACS_FILE_OPEN` and so on. That spelling does not exist in any header.

## SECURITY_INFORMATION flags

For `kacs_get_sd` and `kacs_set_sd`. Declared as `KACS_SECINFO_*`; the names below are the MS-DTYP spellings PCDS uses.

| Flag | Value | Right to read | Right to write |
|---|---|---|---|
| `OWNER_SECURITY_INFORMATION` | 0x01 | `READ_CONTROL` | `WRITE_OWNER` |
| `GROUP_SECURITY_INFORMATION` | 0x02 | `READ_CONTROL` | `WRITE_OWNER` |
| `DACL_SECURITY_INFORMATION` | 0x04 | `READ_CONTROL` | `WRITE_DAC` |
| `SACL_SECURITY_INFORMATION` | 0x08 | `ACCESS_SYSTEM_SECURITY` | `ACCESS_SYSTEM_SECURITY` |
| `LABEL_SECURITY_INFORMATION` | 0x10 | `READ_CONTROL` | `WRITE_OWNER`, plus the integrity rules |

`SACL_SECURITY_INFORMATION` and `LABEL_SECURITY_INFORMATION` are mutually exclusive in one call.

## Process mitigation flags

The `KACS_MIT_*` flags on the PSB. The catalogue of what each one gates is [Process mitigations](~peios/process-mitigations/catalog).

## Size and count limits

| Limit | Value | Context |
|---|---|---|
| Max SD size | 65,535 bytes | Any SD blob. Normative in PCDS §5.1. |
| Max ACL size | 64 KB | Any ACL within an SD |
| Max single ACE size | 64 KB | Bounded by the ACL size |
| Min SID size | 8 bytes | Revision, count and authority, no sub-authorities |
| Max SID size | 68 bytes | 15 sub-authorities |
| Max token wire spec | 64 KB | `kacs_create_token` input |
| Max session wire spec | 4096 bytes | `kacs_create_session` input |
| Max CAAP wire spec | 256 KB | `kacs_set_caap` input |
| Max CAAP rules per policy | 256 | |
| Max applies-to expression | 64 KB | Per CAAP rule |
| Max conditional stack depth | 1024 | Evaluator limit |
| Max TLP cache entries | 64 | Trusted Library Path prefixes |
| Max TLP path length | 4096 bytes | Per prefix |
| Max mount template SD | 64 KB | `kacs_set_mount_policy` template |
