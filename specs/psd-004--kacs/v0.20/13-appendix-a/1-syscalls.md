---
title: Syscalls
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

Three checks: (1) PROCESS_QUERY_INFORMATION on the target process's SD, (2) PIP dominance over the target process, (3) the requested `access_mask` on the token's own SD.

The returned handle is a live reference — mutable fields (privilege enable/disable) are visible through this handle.

### kacs_open_thread_token

Opens the effective token of a specific thread.

| Parameter | Description |
|---|---|
| `pidfd` | pidfd identifying the target process. |
| `tid` | Thread ID within the target process. |
| `access_mask` | Desired access for the returned handle. |
| Returns | Token fd on success, `-errno` on failure. |

If the thread is impersonating, returns the impersonation token. Otherwise returns the process's primary token. Access checks: PROCESS_QUERY_INFORMATION on the target process's SD, PIP dominance, and the requested `access_mask` on the token's own SD.

### kacs_create_token

Mints a new token from a wire-format specification.

| Parameter | Description |
|---|---|
| `spec` | Wire-format token specification. |
| `spec_len` | Length in bytes. |
| Returns | Token fd on success, `-errno` on failure. |

Requires SeCreateTokenPrivilege. The kernel validates: all SIDs well-formed, owner/primary_group indices valid, `auth_id` references an existing session, Primary tokens have `impersonation_level` = Anonymous, `write_restricted` = true requires `user_deny_only` = true, `isolation_boundary` = true requires `confinement_sid` present, wire format `_reserved1` (elevation_type) must be 0. See §4.4 for the full validation list.

The kernel MUST NOT authenticate the user, look up SIDs, or resolve mappings.

The kernel generates: `token_id`, `modified_id` (= token_id), `created_at` (current time), `elevation_type` (always Default), and the token's own SD (default template). The kernel derives the logon SID from `session_id` (`S-1-5-5-{high}-{low}`) and appends it to the groups array with SE_GROUP_LOGON_ID. Callers MUST NOT include the logon SID in the supplied groups. `owner_sid_index` and `primary_group_index` are relative to the caller-supplied groups (0 = user SID, 1..N = caller's groups), not including the injected logon SID. See §13.6 for the wire format.

Because this syscall does not take a desired-access parameter, the returned
token fd always carries the fixed cached access mask `TOKEN_ALL_ACCESS`.

### kacs_open_peer_token

Extracts the peer's identity from a connected Unix socket.

| Parameter | Description |
|---|---|
| `sock_fd` | Connected Unix stream or seqpacket socket. |
| Returns | Token fd on success, `-errno` on failure. |

The peer identity is a snapshot captured at `connect()` time. The impersonation level stored on the socket determines the token's usability. No privilege required.

Only sockets with a KACS peer-token snapshot installed by the Unix
stream/seqpacket connect path are eligible. Unix datagram sockets,
socketpair-created sockets, and ancillary credential messages
(`SCM_CREDENTIALS` / `SCM_SECURITY`) do not create KACS peer tokens in
`v0.20`. Calling this syscall on a socket without a captured KACS peer token
fails closed with `-EACCES`.

Because this syscall does not take a desired-access parameter, the returned
token fd always carries the fixed cached access mask
`TOKEN_QUERY | TOKEN_IMPERSONATE`. This allows the caller to inspect the peer
identity and, if desired, pass the token to `KACS_IOC_IMPERSONATE` without
silently depending on unspecified handle widening.

## Impersonation

### kacs_impersonate_peer

Impersonates the peer's identity on the calling thread. Combines open + impersonate + close in a single kernel transition.

| Parameter | Description |
|---|---|
| `sock_fd` | Connected Unix stream or seqpacket socket. |
| Returns | 0 on success, `-errno` on failure. |

Follows the two-gate model (identity gate + integrity ceiling). The effective impersonation level is the minimum permitted by all constraints — if a gate caps the level, it is silently reduced. The call always succeeds (no error for capping). Overwrites any existing impersonation (reverts first, then re-impersonates). Exception: restricted→unrestricted same-user impersonation is hard-denied (-EPERM) to prevent sandbox escape.

The call requires the same captured KACS peer-token state as
`kacs_open_peer_token`. Datagram sockets, socketpair-created sockets, and
ancillary credential messages are not socket-based impersonation authorities in
`v0.20`; they fail closed with `-EACCES` unless the caller uses an explicit
token fd through `KACS_IOC_IMPERSONATE`.

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
| `sock_fd` | Unconnected Unix stream or seqpacket socket. |
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

### kacs_destroy_empty_session

Destroys a logon session that has not acquired any live token.

| Parameter | Description |
|---|---|
| `session_id` | Session ID (LUID) to destroy. |
| Returns | 0 on success, `-errno` on failure. |

Requires SeTcbPrivilege. The call succeeds only when the session exists, has
zero live tokens, has no linked-token state, and has no other in-flight kernel
references. On success, the kernel emits the normal
`logon-session-destroyed` KMES event. A nonexistent session returns `-ENOENT`.
A session with any live token, linked-token state, or other in-flight kernel
reference returns `-EBUSY`.

## File operations

### kacs_open

Opens or creates a file with an explicit desired access mask.

| Parameter | Description |
|---|---|
| `dirfd` | Base directory fd (or AT_FDCWD). |
| `path` | Pathname relative to dirfd. |
| `how` | Pointer to a `struct kacs_open_how` containing desired_access, create_disposition, create_options, sd pointer, sd_len, and flags. |
| `howsize` | Size of the `kacs_open_how` struct. Enables forward-compatible extensibility (following the `openat2` pattern). |
| `status_out` | Out: creation status. NULL if not needed. |
| Returns | File fd on success, `-errno` on failure. |

The `kacs_open_how` struct packs all open parameters into a single extensible structure. Unknown trailing fields are rejected if non-zero, ensuring old userspace cannot accidentally trigger new behaviour.

Strict mode: every concrete bit in `desired_access` MUST be granted or the
open fails. If `MAXIMUM_ALLOWED` is present, it MUST be combined with at least
one concrete data/execute bit that defines the Linux fd mode. The concrete
data/execute bits MUST be granted, and the fd's cached KACS granted mask is
the maximum granted mask computed by AccessCheck.

### kacs_get_sd

Reads all or part of an object's security descriptor.

| Parameter | Description |
|---|---|
| `dirfd` | Base directory fd (or AT_FDCWD). |
| `path` | Pathname relative to dirfd. |
| `security_info` | Bitmask of which SD components to retrieve. |
| `buf` | Output buffer. |
| `buf_len` | Buffer size. 0 to probe the required size without writing. |
| `flags` | AT_EMPTY_PATH for O_PATH fds. |
| Returns | SD size in bytes on success (regardless of whether data was written). `-ERANGE` is NOT returned — a zero-length buffer is not an error, it is the probe mechanism. Other `-errno` values for real errors. |

Security information flags and required rights:

| Flag | Value | Required right |
|---|---|---|
| OWNER_SECURITY_INFORMATION | 0x01 | READ_CONTROL |
| GROUP_SECURITY_INFORMATION | 0x02 | READ_CONTROL |
| DACL_SECURITY_INFORMATION | 0x04 | READ_CONTROL |
| SACL_SECURITY_INFORMATION | 0x08 | ACCESS_SYSTEM_SECURITY |
| LABEL_SECURITY_INFORMATION | 0x10 | READ_CONTROL |

The returned buffer MUST contain one self-relative security descriptor subset.
Revision MUST be 1 and `SE_SELF_RELATIVE` MUST be set. Only the requested
components are included:

- OWNER/GROUP populate the corresponding SID offsets when requested.
- DACL populates the descriptor's DACL field when requested.
- SACL populates the descriptor's SACL field when requested.
- LABEL populates the descriptor's SACL field with the label subset only.

Requested components that are absent on the object are omitted from the subset
descriptor (offset 0, corresponding PRESENT bit clear). The subset descriptor
header is still returned even when every requested component is absent.

`SACL_SECURITY_INFORMATION` and `LABEL_SECURITY_INFORMATION` MUST NOT be
requested together. The combination is invalid and fails with `-EINVAL`.

For `LABEL_SECURITY_INFORMATION`, the label subset is defined as:

- if the object has an explicit mandatory-label ACE, the returned SACL contains
  exactly the first non-inherit-only `SYSTEM_MANDATORY_LABEL_ACE`;
- if the object has no explicit mandatory-label ACE, the returned descriptor
  carries no SACL component.

With AT_EMPTY_PATH, the fd type determines behaviour: file fd checks the required right (READ_CONTROL or ACCESS_SYSTEM_SECURITY) against the fd's cached granted mask, O_PATH fd uses live AccessCheck against the file's SD, pidfd operates on the process SD (live AccessCheck), token fd operates on the token's own SD (live AccessCheck — the token fd's cached access mask is for token ioctls, not for SD queries).

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

`sd_buf` MUST contain one self-relative security descriptor subset. Revision
MUST be 1 and `SE_SELF_RELATIVE` MUST be set. Only the components indicated by
`security_info` are read from the input descriptor; unindicated components are
ignored and the target object's existing values are preserved.

`SACL_SECURITY_INFORMATION` and `LABEL_SECURITY_INFORMATION` MUST NOT be set in
the same call. The combination is invalid and fails with `-EINVAL`.

For `SACL_SECURITY_INFORMATION`, the input descriptor's SACL replaces the
object's entire SACL.

For `LABEL_SECURITY_INFORMATION`, the input descriptor's SACL is interpreted as
the label subset only:

- no SACL component clears the object's explicit mandatory label and returns it
  to the default unlabeled MIC state (effective Medium with no-write-up);
- a present SACL MUST contain exactly one non-inherit-only
  `SYSTEM_MANDATORY_LABEL_ACE` and no other ACEs;
- that ACE replaces the object's explicit mandatory label while all non-label
  SACL ACEs are preserved unchanged.

With AT_EMPTY_PATH, the fd type determines behaviour: file fd checks the required right against the fd's cached granted mask, O_PATH fd uses live AccessCheck against the file's SD, pidfd operates on the process SD (live AccessCheck), token fd operates on the token's own SD (live AccessCheck).

### kacs_get_mount_policy

Queries the FACS mount-policy state for the superblock containing an fd.

| Parameter | Description |
|---|---|
| `fd` | Any fd, including O_PATH, naming an object on the target superblock. |
| `args` | Pointer to `struct kacs_mount_policy_args`. |
| `argsize` | Size of the caller's struct. Enables forward-compatible extensibility. |
| Returns | 0 on success, `-errno` on failure. |

Requires SeTcbPrivilege. On success, `policy`, `flags`, `generation`, and
`template_sd_len` are written back to `args`. If `template_sd_ptr` is non-null
and the caller's `template_sd_len` is large enough, the current template bytes
are copied to that buffer. If the caller's template buffer is absent or too
small, the syscall still succeeds, writes the required template length to
`template_sd_len`, and copies no template bytes.

### kacs_set_mount_policy

Sets the FACS mount-policy state for the superblock containing an fd.

| Parameter | Description |
|---|---|
| `fd` | Any fd, including O_PATH, naming an object on the target superblock. |
| `args` | Pointer to `struct kacs_mount_policy_args`. |
| `argsize` | Size of the caller's struct. Enables forward-compatible extensibility. |
| Returns | 0 on success, `-errno` on failure. |

Requires SeTcbPrivilege. `policy` MUST be one of `facs_deny_missing`,
`facs_synthesize_ephemeral`, or `facs_synthesize_persistent`. The public ABI
MUST reject `unmanaged`. `flags` and reserved padding fields MUST be zero.
`facs_deny_missing` requires `template_sd_ptr == 0` and `template_sd_len == 0`
and clears the mount template. For synthesize-class policies,
`template_sd_ptr == 0` and `template_sd_len == 0` clears the mount template;
`template_sd_ptr != 0` requires a non-zero `template_sd_len` no larger than 64
KiB and the pointed-to bytes MUST be one structurally valid complete
self-relative file SD. Any validation failure leaves the existing mount policy
unchanged.

## AccessCheck

### kacs_access_check

Evaluates AccessCheck for a userspace object manager.

| Parameter | Description |
|---|---|
| `args` | Pointer to a versioned struct (extensible via size field). |
| Returns | Granted access mask (>= 0) on success, `-EACCES` if any requested right denied, `-errno` for other errors. |

The args struct contains: token fd, SD pointer, desired access, GenericMapping (4 fields), optional self_sid, privilege_intent, optional object type list, optional local claims, pip_type, pip_trust, optional object_audit_context (opaque blob for audit event identification), granted_out pointer (optional — 0 = not used), continuous_audit_out pointer (optional), and staging_mismatch_out pointer (optional). `local_claims` uses the same length-prefixed claim-array wrapper described in §3.9. `object_tree_ptr` points to a flat preorder array of `struct kacs_object_type_entry` values defined in §13.6. `pip_type`/`pip_trust` default to the calling process's PSB values when zero. `object_audit_context` is optional — when null, audit events are still emitted but carry no object identification. The return value carries the granted mask directly; when granted_out_ptr is non-null, the granted mask is also written there (even on -EACCES, so the caller can see what was granted). `staging_mismatch_out` is written as 1 if the staged CAAP result differs from the effective result. In scalar mode this includes scalar grant deltas and audit deltas. When an object type list is present, it is also set if any node's staged granted mask differs from that node's effective granted mask.

This is the same AccessCheck pipeline used by FACS. It exists for userspace daemons that manage non-file objects (loregd, lpsd, eventd). The kernel runs the full pipeline including privilege-use tracking and the SACL audit walk. Audit events are emitted directly by the kernel through KMES — the caller provides `object_audit_context` (an opaque blob identifying the object being accessed, e.g., a registry key path) which is included in emitted audit events so the audit trail identifies which object the access decision was about. Exact AccessCheck audit event types and payload schemas are defined in Appendix A: Audit Event Schemas.

When an object type list is provided, `kacs_access_check` returns the root node's granted mask (the intersection of all nodes). For per-node results, use `kacs_access_check_list`.

### kacs_access_check_list

Evaluates AccessCheck with an object type list and returns per-node results.

| Parameter | Description |
|---|---|
| `args` | Pointer to a versioned struct. Same fields as `kacs_access_check_args` but object type list is mandatory. |
| `results` | Pointer to output array of `{u32 granted, u32 status}` pairs, one per node. |
| `results_count` | Number of entries in the results array. MUST equal the object type list node count. |
| Returns | 0 on success, `-errno` on failure. Per-node verdicts are in the output array. |

Each result entry contains the node's granted mask and a status (0 = granted, -EACCES = denied). A node is granted if `(node.granted & mapped_desired) == mapped_desired`. A denial on one node fails only that node — other nodes may still succeed.

Because `kacs_access_check_list` reuses `struct kacs_access_check_args`, the
shared optional outputs remain valid in list mode. In particular,
`granted_out_ptr` receives the root node's granted mask (the same intersection
value returned by scalar `kacs_access_check` for the same object type list).
`continuous_audit_out_ptr` and `staging_mismatch_out_ptr` keep their normal
meanings.

This is the `AccessCheckResultList` variant described in §10.10.

## Central Access and Auditing Policy

### kacs_set_caap

Pushes, replaces, or removes a CAAP in the kernel policy cache.

| Parameter | Description |
|---|---|
| `policy_sid` | Binary SID identifying the policy. |
| `policy_sid_len` | Length of the policy SID in bytes. |
| `spec` | Wire-format CAAP specification. NULL = remove. |
| `spec_len` | Length of spec. 0 = remove. |
| Returns | 0 on success, `-errno` on failure. |

Requires SeTcbPrivilege. See §10.8 for the wire format and cache semantics.

## PSB management

### kacs_set_psb

Sets mitigation fields on a process's PSB. PIP fields are not settable via syscall — they are determined exclusively by the kernel at exec time from the binary's cryptographic signature (see §6.1).

| Parameter | Description |
|---|---|
| `pidfd` | Target process (-1 = self). |
| `mitigations` | Bitmask of mitigations to enable (one-way). |
| Returns | 0 on success, `-errno` on failure. |

Mitigations are one-way: bits can only be turned on. Any process MAY set mitigations on itself (no privilege required). Setting mitigations on another process requires PROCESS_SET_INFORMATION on the target's process SD and PIP dominance.
