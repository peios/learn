---
title: Syscalls
type: reference
description: Full catalog of KACS-specific syscalls in v0.20. Each entry covers the syscall number, parameters, return value, required access rights and privileges, and the errors it can return. Numbers in the 1000–1027 block.
related:
  - peios/kernel-abi-reference/overview
  - peios/kernel-abi-reference/token-ioctls
  - peios/kernel-abi-reference/structs-and-forward-compat
  - peios/wire-formats-reference/overview
  - peios/constants-and-catalogs/overview
---

KACS-specific syscalls occupy numbers **1000–1027** in v0.20. Each is named `kacs_*` and is documented below in numeric order. The catalogue groups them by category for navigation:

- **Token operations** — 1000–1004, 1010
- **Impersonation** — 1011–1013
- **PSB** — 1005
- **File access** — 1020–1022
- **AccessCheck** — 1023, 1024
- **CAAP** — 1025
- **Mount policy** — 1026, 1027

For struct layouts (`kacs_open_how`, `kacs_access_check_args`, etc.), see [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat).

## Token operations

### kacs_open_self_token (1000)

```
int kacs_open_self_token(u32 flags);
```

Opens the calling thread's effective token (or its primary token if `KACS_REAL_TOKEN` is set).

| Parameter | Meaning |
|---|---|
| `flags` | `0` for the effective token; `KACS_REAL_TOKEN` (0x01) for the primary token even when impersonating. |

**Returns** a token fd on success; -errno on failure. The fd has `TOKEN_QUERY | TOKEN_IMPERSONATE` access.

**Requires** no privilege. Always succeeds for the calling thread.

**Errors**: `-EINVAL` (unknown flags).

### kacs_open_process_token (1001)

```
int kacs_open_process_token(int pidfd, u32 desired_access);
```

Opens another process's primary token.

| Parameter | Meaning |
|---|---|
| `pidfd` | Pidfd of the target process. |
| `desired_access` | Mask of `TOKEN_*` rights to grant on the returned fd. |

**Returns** a token fd on success.

**Requires** three checks:
- The target's process SD must grant `PROCESS_QUERY_INFORMATION` to the caller.
- The caller must PIP-dominate the target.
- The target's token SD must grant the requested `desired_access` rights to the caller.

**Errors**: `-EACCES` (any of the three checks failed); `-EPERM` (PIP dominance failed); `-EBADF` (invalid pidfd); `-ESRCH` (target exited).

### kacs_open_thread_token (1002)

```
int kacs_open_thread_token(int pidfd, u32 tid, u32 desired_access);
```

Opens a specific thread's effective token (impersonation token if the thread is impersonating, primary otherwise).

| Parameter | Meaning |
|---|---|
| `pidfd` | Pidfd of the process containing the thread. |
| `tid` | Thread ID within the process. |
| `desired_access` | Mask of `TOKEN_*` rights to grant on the returned fd. |

**Returns** a token fd on success.

**Requires** the same three checks as `kacs_open_process_token`.

**Errors**: same as `kacs_open_process_token`, plus `-ESRCH` if the thread no longer exists.

### kacs_create_token (1003)

```
int kacs_create_token(const void* spec, size_t spec_len);
```

Mints a new token from a wire-format specification. Used by authd and peinit to issue tokens to other processes.

| Parameter | Meaning |
|---|---|
| `spec` | Pointer to the wire-format token specification. |
| `spec_len` | Length of the spec in bytes. |

**Returns** a token fd with `TOKEN_ALL_ACCESS` on success.

**Requires** `SeCreateTokenPrivilege` on the calling token.

**Errors**: `-EPERM` (no privilege); `-EINVAL` (malformed spec, validation failed — wire-format version mismatch, bad SIDs, invalid index references, etc.); `-EFAULT` (bad pointer); `-ENOMEM` (allocation failed).

The wire-format spec is documented in [Wire formats reference](~peios/wire-formats-reference/overview).

### kacs_create_session (1004)

```
u64 kacs_create_session(const void* spec, size_t spec_len);
```

Creates a new logon session. Used by authd at user-authentication time.

| Parameter | Meaning |
|---|---|
| `spec` | Pointer to the wire-format session specification (logon_type, auth_package, user_sid). |
| `spec_len` | Length of the spec in bytes (15–4096). |

**Returns** the new session's `auth_id` (a u64 LUID).

**Requires** `SeTcbPrivilege` on the calling token.

**Errors**: `-EPERM`; `-EINVAL` (malformed spec); `-EFAULT`; `-ENOMEM`.

### kacs_open_peer_token (1010)

```
int kacs_open_peer_token(int socket_fd);
```

Opens a token fd reflecting the peer's identity on a connected Unix stream or seqpacket socket. The peer token was captured at connect time.

| Parameter | Meaning |
|---|---|
| `socket_fd` | Connected Unix socket fd. |

**Returns** a token fd with **fixed** `TOKEN_QUERY | TOKEN_IMPERSONATE` access (the access mask is not parameterised).

**Requires** the socket fd to be a connected Unix stream or seqpacket socket that captured a peer token at connect.

**Errors**: `-EACCES` (socket lacks a peer token — datagram socket, socketpair, pre-connected socket); `-EBADF` (invalid fd); `-ENOTCONN` (socket not yet connected).

## Impersonation

### kacs_impersonate_peer (1011)

```
int kacs_impersonate_peer(int socket_fd);
```

Captures the peer's token from a Unix socket and installs it as the calling thread's impersonation token. Combines `kacs_open_peer_token` + install in one call. Reverts any existing impersonation first.

| Parameter | Meaning |
|---|---|
| `socket_fd` | Connected Unix socket fd. |

**Returns** 0 on success.

**Requires** the socket to carry a peer token. The two-gate model runs (identity gate, integrity ceiling); the resulting level may be silently downgraded.

**Errors**: `-EACCES` (no peer token); `-EPERM` (restricted→unrestricted same-user impersonation attempt — see [The two-gate model](~peios/impersonation/the-two-gates)); `-EBADF`.

### kacs_revert (1012)

```
int kacs_revert(void);
```

Reverts the calling thread to its primary token. Always succeeds.

**Returns** 0 always.

**Requires** no privilege; no checks.

**Errors**: none in normal operation.

### kacs_set_impersonation_level (1013)

```
int kacs_set_impersonation_level(int socket_fd, u32 level);
```

Sets the maximum impersonation level the server may use when impersonating the peer of this socket. Called by the client before `connect()`. Default is `KACS_LEVEL_IMPERSONATION` (2).

| Parameter | Meaning |
|---|---|
| `socket_fd` | Unix socket fd (must not yet be connected). |
| `level` | One of `KACS_LEVEL_ANONYMOUS` (0), `KACS_LEVEL_IDENTIFICATION` (1), `KACS_LEVEL_IMPERSONATION` (2), `KACS_LEVEL_DELEGATION` (3). |

**Returns** 0 on success.

**Errors**: `-EINVAL` (unknown level, or socket already connected); `-EBADF`.

## PSB

### kacs_set_psb (1005)

```
int kacs_set_psb(int target_pidfd, u64 flags);
```

Sets one-way mitigation flags on a process's PSB. Can target the caller's own process (no privilege required) or another process (requires `PROCESS_SET_INFORMATION` plus PIP dominance).

| Parameter | Meaning |
|---|---|
| `target_pidfd` | Pidfd of the target process (or own pidfd / sentinel for self). |
| `flags` | Bitmask of mitigation flags to set. Cleared bits are not touched (OR with current). |

**Returns** 0 on success.

**Requires** for cross-process: `PROCESS_SET_INFORMATION` on target's process SD + PIP dominance. For self: nothing.

**Errors**: `-EACCES` (target SD denied); `-EPERM` (PIP dominance failed); `-EINVAL` (unknown flag bits); `-EBADF`; `-ESRCH`.

The full mitigation-flag catalog is in [Process mitigations](~peios/process-mitigations/catalog).

## File access

### kacs_open (1020)

```
int kacs_open(int dirfd, const char* path, const struct kacs_open_how* how, size_t howsize, u32* status_out);
```

Native KACS-aware file open. Strict-mode: every right in `how->desired_access` must be granted or the call fails.

| Parameter | Meaning |
|---|---|
| `dirfd` | Directory fd for path resolution (or `AT_FDCWD`). |
| `path` | Path to open. May be empty if `AT_EMPTY_PATH` in `how->flags`. |
| `how` | Pointer to `kacs_open_how` struct. |
| `howsize` | Size of the struct as known to the caller. Minimum 16 bytes. |
| `status_out` | Optional output: one of `KACS_STATUS_OPENED`, `KACS_STATUS_CREATED`, `KACS_STATUS_OVERWRITTEN`, `KACS_STATUS_SUPERSEDED`. |

**Returns** a file fd with the granted access mask cached.

**Errors**: `-EACCES` (some requested right denied); `-EEXIST` (CREATE with existing file); `-ENOENT` (OPEN with missing file); `-ENOTDIR` (DIRECTORY flag and target isn't); `-ELOOP` (NOFOLLOW and target is symlink); `-EINVAL` (MAXIMUM_ALLOWED with no concrete bits, malformed creator SD, etc.); `-EBADF`.

The struct is in [Structs and forward-compat](~peios/kernel-abi-reference/structs-and-forward-compat); the conceptual model is in [Opening files](~peios/file-access/opening-files).

### kacs_get_sd (1021)

```
ssize_t kacs_get_sd(int dirfd, const char* path, u32 security_info, void* buf, size_t buf_len, u32 flags);
```

Reads all or part of an object's security descriptor.

| Parameter | Meaning |
|---|---|
| `dirfd`, `path` | Target object (file path-based). |
| `security_info` | Bitmask of components to return (`OWNER_SECURITY_INFORMATION` etc.). |
| `buf` | Output buffer; may be NULL for probe. |
| `buf_len` | Buffer size; 0 for probe. |
| `flags` | `AT_EMPTY_PATH`, `AT_SYMLINK_NOFOLLOW`. |

**Returns** the required size in bytes (whether probing or fetching). On probe (buf_len=0), the size is the return value, no -ERANGE.

**Requires** the rights corresponding to the requested components (per [Managing file security](~peios/file-access/managing-file-security)).

**Errors**: `-EACCES`; `-EINVAL` (incompatible flag combination, e.g. SACL+LABEL); `-ERANGE` (non-probe call with buf too small).

### kacs_set_sd (1022)

```
int kacs_set_sd(int dirfd, const char* path, u32 security_info, const void* sd_buf, size_t sd_len, u32 flags);
```

Sets all or part of an object's security descriptor.

| Parameter | Meaning |
|---|---|
| `dirfd`, `path` | Target. |
| `security_info` | Which components to update. |
| `sd_buf`, `sd_len` | The new SD bytes (self-relative format). |
| `flags` | `AT_EMPTY_PATH`, `AT_SYMLINK_NOFOLLOW`. |

**Returns** 0 on success.

**Requires** the rights corresponding to components being updated. Owner SID validation per [Ownership](~peios/security-descriptors/ownership); MANDATORY attribute protection per [Resource attributes](~peios/security-descriptors/resource-attributes); integrity-label ceiling per [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

**Errors**: `-EACCES`; `-EPERM` (owner-validation failed without SeRestore; etc.); `-EINVAL` (malformed SD; incompatible flag combination).

## AccessCheck

### kacs_access_check (1023)

```
int kacs_access_check(struct kacs_access_check_args* args);
```

Performs AccessCheck for a userspace-managed object. Used by userspace object managers (loregd for the registry, application servers for their own objects).

| Parameter | Meaning |
|---|---|
| `args` | Pointer to `kacs_access_check_args` struct (size-versioned). |

**Returns** 0 on success (granted mask non-empty), or `-EACCES` if no requested rights were granted. The granted mask, continuous-audit mask, and staging-mismatch flag are written to fields in `args`.

**Requires** no privilege; available to any caller that has a token and an SD to evaluate.

**Errors**: `-EACCES` (denied — granted mask still written); `-EINVAL` (malformed SD, invalid object type list, etc.); `-EFAULT` (bad output pointers).

### kacs_access_check_list (1024)

```
int kacs_access_check_list(struct kacs_access_check_args* args, struct kacs_node_result* results, size_t results_count);
```

Per-property AccessCheck. Requires an object type list. Returns per-node granted masks and statuses.

| Parameter | Meaning |
|---|---|
| `args` | Same struct as `kacs_access_check`; must include an object type list. |
| `results` | Output array, one entry per node in the object type list. |
| `results_count` | Length of `results`; must match the tree's node count. |

**Returns** 0 on success.

**Errors**: same as `kacs_access_check`, plus `-EINVAL` (mismatch between `results_count` and the tree's node count).

## CAAP

### kacs_set_caap (1025)

```
int kacs_set_caap(const void* policy_sid, size_t sid_len, const void* spec, size_t spec_len);
```

Pushes, replaces, or removes a central access policy in the kernel's policy cache.

| Parameter | Meaning |
|---|---|
| `policy_sid` | SID identifying the policy. |
| `sid_len` | Length of the SID in bytes. |
| `spec` | Wire-format policy spec. NULL to remove. |
| `spec_len` | Length of spec. 0 with NULL spec means remove. |

**Returns** 0 on success.

**Requires** `SeTcbPrivilege`.

**Errors**: `-EPERM`; `-EINVAL` (malformed spec — version byte, oversized, malformed expressions, invalid SIDs); `-EFAULT`; `-ENOMEM`.

Wire format details in [Wire formats reference](~peios/wire-formats-reference/overview).

## Mount policy

### kacs_get_mount_policy (1026)

```
int kacs_get_mount_policy(int fd, struct kacs_mount_policy_args* args);
```

Queries the current mount policy of the superblock containing `fd`.

| Parameter | Meaning |
|---|---|
| `fd` | Any fd on the target superblock. |
| `args` | Pointer to `kacs_mount_policy_args` struct (size-versioned). |

**Returns** 0 on success. The policy class, generation counter, and template SD (if buffer provided) are written to fields in `args`.

**Requires** `SeTcbPrivilege`.

**Errors**: `-EPERM`; `-EBADF`; `-ERANGE` (template buffer too small).

### kacs_set_mount_policy (1027)

```
int kacs_set_mount_policy(int fd, const struct kacs_mount_policy_args* args);
```

Sets the mount policy on the superblock containing `fd`.

| Parameter | Meaning |
|---|---|
| `fd` | Any fd on the target superblock. |
| `args` | Pointer to args struct with the new policy class and optional new template. |

**Returns** 0 on success. The new generation counter is written to `args->generation`.

**Requires** `SeTcbPrivilege`.

**Errors**: `-EPERM`; `-EINVAL` (`unmanaged` is not settable via this ABI; unknown policy value; malformed template; non-zero reserved fields); `-EBADF`.

## Quick number reference

For convenient lookup:

| # | Name |
|---|---|
| 1000 | `kacs_open_self_token` |
| 1001 | `kacs_open_process_token` |
| 1002 | `kacs_open_thread_token` |
| 1003 | `kacs_create_token` |
| 1004 | `kacs_create_session` |
| 1005 | `kacs_set_psb` |
| 1010 | `kacs_open_peer_token` |
| 1011 | `kacs_impersonate_peer` |
| 1012 | `kacs_revert` |
| 1013 | `kacs_set_impersonation_level` |
| 1020 | `kacs_open` |
| 1021 | `kacs_get_sd` |
| 1022 | `kacs_set_sd` |
| 1023 | `kacs_access_check` |
| 1024 | `kacs_access_check_list` |
| 1025 | `kacs_set_caap` |
| 1026 | `kacs_get_mount_policy` |
| 1027 | `kacs_set_mount_policy` |

Numbers 1006–1009 and 1014–1019 are reserved for future expansion.
