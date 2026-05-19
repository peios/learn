---
title: Token ioctls
type: reference
description: Full catalog of KACS_IOC_* ioctls on token file descriptors. Magic byte 'K' (0x4B). Each entry covers the ioctl number, parameter struct, required token access right, and possible errors. v0.20 defines ioctls 0 through 10.
related:
  - peios/kernel-abi-reference/overview
  - peios/kernel-abi-reference/syscalls
  - peios/kernel-abi-reference/structs-and-forward-compat
  - peios/constants-and-catalogs/overview
---

KACS token ioctls use the magic byte `'K'` (0x4B). Each is performed on a token file descriptor (obtained from `kacs_open_self_token`, `kacs_create_token`, `kacs_open_process_token`, etc.) and operates on the underlying token's state.

This page catalogues each `KACS_IOC_*` ioctl: its number, its parameter struct, the token access right it requires, and the errors it can return.

The struct definitions are in [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat).

## KACS_IOC_QUERY (0)

Query a structured field on the token.

```
ioctl(token_fd, _IOWR('K', 0, struct kacs_query_args))
```

| `args` field | Meaning |
|---|---|
| `token_class` | The numeric class identifying what to return (1–24). |
| `buf_len` | Input: buffer size. Output: actual size needed. |
| `buf_ptr` | Userspace pointer to output buffer. |

**Two-call pattern.** Call with `buf_ptr=0` or `buf_len=0` to probe — kernel writes required size to `buf_len`, returns 0. Then allocate and call again to fetch.

**Requires** `TOKEN_QUERY` on the fd's access mask.

**Errors**: `-EACCES`; `-EINVAL` (unknown class); `-ERANGE` (non-probe call with too-small buffer; required size written); `-EFAULT` (buf_ptr overlaps `args`).

Full class catalog (1–24) covered in [Inspecting tokens](~peios/inspecting/tokens).

## KACS_IOC_ADJUST_PRIVS (1)

Enable, disable, or permanently remove privileges on the token.

```
ioctl(token_fd, _IOWR('K', 1, struct kacs_adjust_privs_args))
```

| `args` field | Meaning |
|---|---|
| `count` | Number of entries in the data array. |
| `data_ptr` | Pointer to array of `kacs_priv_entry` records. |
| `previous_enabled` | Output: the previous `enabled` bitmask, for save-and-restore patterns. |

Each `kacs_priv_entry` has a privilege LUID and an attributes value (`0` = disable, `SE_PRIVILEGE_ENABLED` = enable, `SE_PRIVILEGE_REMOVED` = permanently remove, `KACS_PRIV_RESET_ALL_DEFAULTS` with luid=0 = reset to defaults).

**Atomic.** All entries succeed or none do.

**Requires** `TOKEN_ADJUST_PRIVILEGES` on the fd's access mask.

**Errors**: `-EACCES`; `-EINVAL` (duplicate LUID, enabling absent privilege, unknown attributes bits, misuse of reset sentinel).

Bumps `modified_id` on success.

## KACS_IOC_DUPLICATE (2)

Create an independent copy of the token.

```
ioctl(token_fd, _IOWR('K', 2, struct kacs_duplicate_args))
```

| `args` field | Meaning |
|---|---|
| `access_mask` | Access mask for the new fd. |
| `token_type` | `1` for Primary, `2` for Impersonation. |
| `impersonation_level` | `0`–`3` (Anonymous through Delegation). |
| `result_fd` | Output: the new fd. |

**Returns** 0 on success; new fd in `result_fd`.

**Requires** `TOKEN_DUPLICATE` on the source fd.

**Errors**: `-EACCES`; `-EINVAL` (impersonation level exceeds source's level; unknown token_type).

## KACS_IOC_INSTALL (3)

Install the token as the calling process's primary token.

```
ioctl(token_fd, _IO('K', 3))
```

No args struct. The token represented by `token_fd` becomes the calling process's primary token.

**Requires**:
- `TOKEN_ASSIGN_PRIMARY` on the fd's access mask.
- `SeAssignPrimaryTokenPrivilege` on the calling token.

**Process-wide.** All threads of the calling process eventually converge to the new token; the change is propagated asynchronously by the kernel.

**Errors**: `-EACCES`; `-EPERM` (no privilege); `-EINVAL` (impersonation-type token cannot be installed as primary).

## KACS_IOC_RESTRICT (4)

Create a restricted version of the token (with restricted SIDs, privileges removed, groups marked deny-only, optionally write-restricted).

```
ioctl(token_fd, _IOWR('K', 4, struct kacs_restrict_args))
```

| `args` field | Meaning |
|---|---|
| `privs_to_delete` | Bitmask of privileges to remove from the new token. |
| `num_deny_indices` | Number of group indices to mark `SE_GROUP_USE_FOR_DENY_ONLY`. |
| `num_restrict_sids` | Number of restricting SIDs to add. |
| `data_len`, `data_ptr` | Variable-length payload: u32 deny indices + packed binary SIDs. |
| `flags` | `KACS_RESTRICT_WRITE_RESTRICTED` (0x01) for write-restricted mode. |
| `result_fd` | Output: the new fd. |

**Requires** `TOKEN_DUPLICATE` on the source.

**Errors**: `-EACCES`; `-EINVAL` (malformed payload, duplicate indices, out-of-range indices).

## KACS_IOC_LINK_TOKENS (5)

Associate an elevated (Full) and filtered (Limited) token pair on a logon session, for UAC-style elevation.

```
ioctl(any_token_fd, _IOWR('K', 5, struct kacs_link_tokens_args))
```

| `args` field | Meaning |
|---|---|
| `elevated_fd` | Fd of the Full token. |
| `filtered_fd` | Fd of the Limited token. |
| `session_id` | The LUID of the session both tokens belong to. |

**Sets** `elevation_type = Full` on the elevated token and `Limited` on the filtered.

**Requires**:
- `SeTcbPrivilege` on the calling token.
- `TOKEN_DUPLICATE` on both passed fds.
- Both tokens must reference the same session_id.
- Neither token may already be linked.

**Errors**: `-EPERM`; `-EACCES`; `-EINVAL` (self-link; role mismatch; session mismatch; already-linked).

## KACS_IOC_GET_LINKED_TOKEN (6)

Get the partner of a linked-pair token.

```
ioctl(token_fd, _IOR('K', 6, struct kacs_get_linked_token_args))
```

| `args` field | Meaning |
|---|---|
| `result_fd` | Output: the partner's fd. |

**Returns** 0 on success.

**Requires** `TOKEN_QUERY` on the source. Behaviour depends on additional privilege:

- **With `SeTcbPrivilege`**: returns the full partner fd, `TOKEN_ALL_ACCESS`.
- **Without `SeTcbPrivilege`**: returns a freshly-duplicated Identification-level clone of the partner, with only `TOKEN_QUERY`. Inspectable but not installable, not usable for AccessCheck.

**Errors**: `-EACCES`; `-ENOENT` (token not part of a pair, or pair was destroyed when session ended).

## KACS_IOC_ADJUST_GROUPS (7)

Enable or disable group entries on the token. Cannot target mandatory groups, deny-only groups, logon SID, or user SID.

```
ioctl(token_fd, _IOWR('K', 7, struct kacs_adjust_groups_args))
```

| `args` field | Meaning |
|---|---|
| `count` | Number of entries. |
| `data_ptr` | Array of `kacs_group_entry` (index + enable). |
| `previous_state` | Output: previous enabled state. |

Reset-all sentinel: a single entry with `index = 0xFFFFFFFF` and `enable = 0` resets all groups to their `enabled_by_default` state.

**Atomic.**

**Requires** `TOKEN_ADJUST_GROUPS`.

**Errors**: `-EACCES`; `-EINVAL` (count=0 without reset sentinel; targeting mandatory/deny-only/logon SID group; duplicate indices; out-of-range index).

Bumps `modified_id`.

## KACS_IOC_IMPERSONATE (8)

Install this token as the calling thread's impersonation token.

```
ioctl(token_fd, _IO('K', 8))
```

No args struct. Reverts any existing impersonation first.

**Requires** `TOKEN_IMPERSONATE` on the fd's access mask.

**The two-gate model runs**: identity gate (same-user or `SeImpersonatePrivilege`) and integrity ceiling (capped at calling thread's primary integrity). The effective installed level may be silently downgraded to Identification if either gate fails.

**Errors**: `-EACCES`; `-EPERM` (restricted→unrestricted same-user attempt — the one hard-deny case); `-EINVAL` (token is Primary type, not Impersonation).

## KACS_IOC_ADJUST_DEFAULT (9)

Adjust the token's default DACL, owner index, and/or primary group index — used for new objects the token creates.

```
ioctl(token_fd, _IOWR('K', 9, struct kacs_adjust_default_args))
```

| `args` field | Meaning |
|---|---|
| `dacl_ptr`, `dacl_len` | Three-way encoding: both zero = no change; ptr nonzero, len>0 = replace; ptr nonzero, len=0 = clear (NULL DACL). |
| `owner_index` | `0xFFFF` = no change; otherwise the new owner-SID index. |
| `group_index` | Same for primary group. |

**Requires** `TOKEN_ADJUST_DEFAULT`.

**Errors**: `-EACCES`; `-EINVAL` (out-of-range indices, malformed DACL).

Bumps `modified_id`.

## KACS_IOC_ADJUST_SESSIONID (10)

Change the token's interactive session ID.

```
ioctl(token_fd, _IOW('K', 10, u32))
```

The argument is a `u32` containing the new session ID.

**Requires**:
- `TOKEN_ADJUST_SESSIONID` on the fd.
- `SeTcbPrivilege` on the calling token.

**Errors**: `-EACCES`; `-EPERM`.

Bumps `modified_id`.

## Quick number reference

| # | Name | Operation |
|---|---|---|
| 0 | `KACS_IOC_QUERY` | Query token information |
| 1 | `KACS_IOC_ADJUST_PRIVS` | Enable/disable/remove privileges |
| 2 | `KACS_IOC_DUPLICATE` | Duplicate the token |
| 3 | `KACS_IOC_INSTALL` | Install as process primary |
| 4 | `KACS_IOC_RESTRICT` | Create restricted variant |
| 5 | `KACS_IOC_LINK_TOKENS` | Establish UAC-style linked pair |
| 6 | `KACS_IOC_GET_LINKED_TOKEN` | Retrieve partner of linked pair |
| 7 | `KACS_IOC_ADJUST_GROUPS` | Enable/disable groups |
| 8 | `KACS_IOC_IMPERSONATE` | Install as thread impersonation |
| 9 | `KACS_IOC_ADJUST_DEFAULT` | Adjust default DACL/owner/group |
| 10 | `KACS_IOC_ADJUST_SESSIONID` | Change interactive session ID |

Numbers 11+ are reserved for future expansion.

## Cross-cutting rules

A few rules common to several ioctls:

**Atomicity of "adjust" operations.** `ADJUST_PRIVS`, `ADJUST_GROUPS`, `ADJUST_DEFAULT` are atomic. If any entry in the array is invalid, the entire operation fails and no state changes. The `previous_*` fields are written only on success.

**`modified_id` bumping.** Any successful operation that modifies the token's mutable state increments the token's `modified_id` counter. Callers that depend on consistency across multiple queries can read `modified_id` (via `KACS_IOC_QUERY` with `TokenStatistics`) to detect mid-pipeline changes.

**Access mask checks.** Every ioctl checks the fd's access mask before doing anything. A fd opened with only `TOKEN_QUERY` cannot be used for adjustment operations even if the underlying token's SD would have granted them — the fd's mask is what gates ioctl access.

**Cross-process scope.** Adjusting an ioctl on another process's token requires both the fd's access mask **and** the cross-process rules: `PROCESS_QUERY_INFORMATION` on the target's process SD and PIP dominance (which were checked at the original `kacs_open_process_token` that produced the fd).
