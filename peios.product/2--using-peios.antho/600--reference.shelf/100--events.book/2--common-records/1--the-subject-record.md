---
title: The Subject Record
description: The subject map identifying the effective token behind an operation — its fields, the two parallel arrays, and what it deliberately omits.
---

The `subject` map identifies the **effective token** under which an
operation ran. It appears in every KACS event except
`logon-session-destroyed`.

For an event fired from an impersonating thread, the subject is the
impersonation token, not the primary. For a non-impersonating thread the
primary token *is* the effective one.

For `continuous-audit` (§3.2) the subject is the effective token **at
the moment of the operation**, not at the moment the handle was opened.
A process whose token changed since the open gets the current subject on
each subsequent operation.

## Fields

| Key | Type | Meaning |
|---|---|---|
| `user_sid` | bin | The token's user SID. |
| `group_sids` | array of bin | The token's group SIDs. |
| `group_attributes` | array of uint | Per-group attribute bitmasks, parallel to `group_sids`. |
| `integrity_level` | uint | The token's integrity RID — 0, 4096, 8192, 12288 or 16384. |
| `pip_type` | uint | The calling process's PIP type. 0 None, 512 Protected, 1024 Isolated. |
| `pip_trust` | uint | The calling process's PIP trust level. |
| `auth_id` | uint | The LUID of the logon session the token belongs to. |
| `token_id` | uint | The token's own LUID. |
| `impersonation_level` | uint | 0–3. A primary token reports 0. |
| `projected_uid` | uint | The Linux UID projection, for correlating with Linux-side audit data. |

Every field is always present.

`auth_id` is the join key to `logon-session-destroyed` (§3.5) and to
`/sys/kernel/security/kacs/sessions`. `token_id` correlates events from
one specific token.

## The two parallel arrays

`group_sids[i]` and `group_attributes[i]` describe the same group entry,
and the arrays are always the same length.

| Flag | Value | Meaning |
|---|---|---|
| `SE_GROUP_MANDATORY` | 0x01 | Cannot be disabled. |
| `SE_GROUP_ENABLED_BY_DEFAULT` | 0x02 | Enabled at creation. |
| `SE_GROUP_ENABLED` | 0x04 | Currently enabled. |
| `SE_GROUP_OWNER` | 0x08 | May act as owner for new objects. |
| `SE_GROUP_USE_FOR_DENY_ONLY` | 0x10 | Matches deny ACEs only. |
| `SE_GROUP_INTEGRITY` | 0x20 | Identifies an integrity SID. Present for ABI parity; MIC reads the token's `integrity_level` field, not this flag. |
| `SE_GROUP_INTEGRITY_ENABLED` | 0x40 | Used with `SE_GROUP_INTEGRITY`. |
| `SE_GROUP_RESOURCE` | 0x20000000 | A domain-local group from a resource domain. Metadata only. |
| `SE_GROUP_LOGON_ID` | 0xC0000000 | The logon SID. Cannot be disabled. |

These are MS-DTYP's names, which PCDS uses. The headers declare the same
flags as `KACS_SID_GROUP_*`; the Peios Kernel TRM §3.A maps the two.

Reconstructing group membership from an event means applying the same
rule the access check applies: `SE_GROUP_ENABLED` set and
`SE_GROUP_USE_FOR_DENY_ONLY` clear, for allow-side matching.

## What the subject deliberately omits

Privileges, claims, the restricted-SID list, confinement state, and the
default DACL are all absent. Each is unbounded, and an event that
embedded them could grow without limit.

Code needing full token state queries the token directly with
`KACS_IOC_QUERY`, while it still exists. The subject record is for
correlation, not for reconstruction.
