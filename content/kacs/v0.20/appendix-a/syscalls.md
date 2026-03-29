---
title: Syscalls
order: 1
---

KACS registers syscalls from a reserved block in the arch-specific syscall table. Each syscall does one thing with typed parameters — no multiplexing.

## Token lifecycle

### kacs_open_self_token

Opens the calling thread's effective token as a token fd.

| Parameter | Description |
|---|---|
| `flags` | `KACS_REAL_TOKEN`: return the primary token even if impersonating. 0: return the effective token. |
| `access_mask` | Desired access for the returned handle (TOKEN_QUERY, TOKEN_DUPLICATE, etc.). |
| Returns | Token fd on success, `-errno` on failure. |

No privilege required. The access mask is checked against the token's own SD.

### kacs_open_process_token

Opens the primary token of another process.

| Parameter | Description |
|---|---|
| `pidfd` | pidfd identifying the target process. |
| `access_mask` | Desired access for the returned handle. |
| Returns | Token fd on success, `-errno` on failure. |

Two access checks: (1) PROCESS_QUERY_INFORMATION on the target process's SD, (2) the requested `access_mask` on the token's own SD.

The returned handle is a live reference — mutable fields (privilege enable/disable) are visible through this handle.

### kacs_create_token

Mints a new token from a wire-format specification.

| Parameter | Description |
|---|---|
| `spec` | Wire-format token specification. |
| `spec_len` | Length in bytes. |
| Returns | Token fd on success, `-errno` on failure. |

Requires SeCreateTokenPrivilege. The kernel validates structural invariants but MUST NOT authenticate the user, look up SIDs, or resolve mappings.

### kacs_open_peer_token

Extracts the peer's identity from a connected Unix socket.

| Parameter | Description |
|---|---|
| `sock_fd` | Connected Unix stream socket. |
| Returns | Token fd on success, `-errno` on failure. |

The peer identity is a snapshot captured at `connect()` time. The impersonation level stored on the socket determines the token's usability. No privilege required.

## Impersonation

### kacs_impersonate_peer

Impersonates the peer's identity on the calling thread. Combines open + impersonate + close in a single kernel transition.

| Parameter | Description |
|---|---|
| `sock_fd` | Connected Unix stream socket. |
| Returns | 0 on success, `-errno` on failure. |

Follows the two-gate model. If neither gate passes, the token is capped to Identification level, not rejected. Overwrites any existing impersonation.

### kacs_revert

Reverts the calling thread to its primary token.

| Parameter | Description |
|---|---|
| (none) | |
| Returns | 0 on success (including if not impersonating). |

No privilege required.

### kacs_set_impersonation_level

Sets the maximum impersonation level a server MAY use. Called by the client before `connect()`.

| Parameter | Description |
|---|---|
| `sock_fd` | Unconnected Unix stream socket. |
| `level` | ANONYMOUS (0), IDENTIFICATION (1), IMPERSONATION (2), DELEGATION (3). |
| Returns | 0 on success, `-errno` on failure. |

Default is IMPERSONATION.

## Session management

### kacs_create_session

Creates a new logon session.

| Parameter | Description |
|---|---|
| `spec` | Wire-format session specification (logon type, auth package, user SID). |
| `spec_len` | Length in bytes. |
| Returns | Session ID (>= 0) on success, `-errno` on failure. |

Requires SeTcbPrivilege. The session receives an auto-generated logon SID (`S-1-5-5-X-Y`).

## File operations

### kacs_open

Opens or creates a file with an explicit desired access mask.

| Parameter | Description |
|---|---|
| `dirfd` | Base directory fd (or AT_FDCWD). |
| `path` | Pathname relative to dirfd. |
| `desired_access` | Explicit access mask. |
| `create_disposition` | FILE_OPEN, FILE_CREATE, FILE_OPEN_IF, FILE_OVERWRITE, FILE_OVERWRITE_IF, FILE_SUPERSEDE. |
| `create_options` | FILE_DIRECTORY_FILE, FILE_DELETE_ON_CLOSE, etc. |
| `sd` | SD for newly created files. NULL = inherit from parent. |
| `sd_len` | Length of sd. 0 if NULL. |
| `status_out` | Out: creation status. NULL if not needed. |
| `flags` | AT_EMPTY_PATH, AT_SYMLINK_NOFOLLOW, etc. |
| Returns | File fd on success, `-errno` on failure. |

Strict mode: every bit in `desired_access` MUST be granted or the open fails.

### kacs_get_sd

Reads all or part of an object's security descriptor.

| Parameter | Description |
|---|---|
| `dirfd` | Base directory fd (or AT_FDCWD). |
| `path` | Pathname relative to dirfd. |
| `security_info` | Bitmask of which SD components to retrieve. |
| `buf` | Output buffer. |
| `buf_len` | Buffer size. |
| `len_needed` | Out: actual size needed. |
| `flags` | AT_EMPTY_PATH for O_PATH fds. |
| Returns | 0 on success, `-ERANGE` if buffer too small. |

Security information flags and required rights:

| Flag | Value | Required right |
|---|---|---|
| OWNER_SECURITY_INFORMATION | 0x01 | READ_CONTROL |
| GROUP_SECURITY_INFORMATION | 0x02 | READ_CONTROL |
| DACL_SECURITY_INFORMATION | 0x04 | READ_CONTROL |
| SACL_SECURITY_INFORMATION | 0x08 | ACCESS_SYSTEM_SECURITY |
| LABEL_SECURITY_INFORMATION | 0x10 | READ_CONTROL |

With AT_EMPTY_PATH, the fd type determines behaviour: file fd uses granted mask, O_PATH fd uses live AccessCheck, pidfd operates on process SD, token fd operates on token SD.

### kacs_set_sd

Sets all or part of an object's security descriptor.

| Parameter | Description |
|---|---|
| `dirfd` | Base directory fd (or AT_FDCWD). |
| `path` | Pathname relative to dirfd. |
| `security_info` | Bitmask of which SD components to set. |
| `sd_buf` | Self-relative SD containing new values. |
| `sd_len` | Length in bytes. |
| `flags` | AT_EMPTY_PATH for O_PATH fds. |
| Returns | 0 on success, `-errno` on failure. |

Required rights per component: OWNER/GROUP require WRITE_OWNER, DACL requires WRITE_DAC, SACL requires ACCESS_SYSTEM_SECURITY, LABEL requires WRITE_OWNER + integrity constraints.

## AccessCheck

### kacs_access_check

Evaluates AccessCheck for a userspace object manager.

| Parameter | Description |
|---|---|
| `args` | Pointer to a versioned struct (extensible via size field). |
| Returns | 0 if all requested rights granted, `-EACCES` if any denied. |

The args struct contains: token fd, SD pointer, desired access, GenericMapping (4 fields), optional self_sid, privilege_intent, optional object type list, optional local claims, and a granted_out pointer (always populated).

This is the same AccessCheck pipeline used by FACS. It exists for userspace daemons that manage non-file objects (loregd, lpsd, eventd).

## PSB management

### kacs_set_psb

Sets PIP and mitigation fields on a process's PSB.

| Parameter | Description |
|---|---|
| `pidfd` | Target process (0 = self). |
| `pip_type` | PIP type (0 = None, 512 = Protected, 1024 = Isolated). Requires SeTcbPrivilege. |
| `pip_trust` | Trust level. Requires SeTcbPrivilege. |
| `mitigations` | Bitmask of mitigations to enable (one-way). |
| Returns | 0 on success, `-errno` on failure. |

Mitigations are one-way: bits can only be turned on.
